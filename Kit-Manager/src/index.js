// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

const express = require('express');
const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { Server } = require('socket.io');
const config = require('../configs');
const convertPgCode = require('./convert_code');
const { getInFlightConverts } = convertPgCode;
const cors = require('cors')
const { randomUUID } = require('crypto')
const { URL } = require('url')

const BOOT_ID = randomUUID()
const KIT_IMAGE_VERSION = process.env.KIT_IMAGE_VERSION || 'unknown'

function _earlyLog(event, meta) {
    const ts = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z')
    const parts = Object.entries(meta).map(([k, v]) => `${k}=${v}`).join(' ')
    console.log(`${ts} [KitManager] [${event}] ${parts}`)
}
_earlyLog('PROCESS_STARTING', {
    pid: process.pid,
    bootId: BOOT_ID,
    nodeVersion: process.version,
    platform: process.platform,
    arch: process.arch,
    nodeEnv: process.env.NODE_ENV || '',
    kitImageVersion: KIT_IMAGE_VERSION,
})

// ---------------------------------------------------------------------------
// Phase 1 hardening (memory + crash). All defaults are tunable via env vars.
// ---------------------------------------------------------------------------
const parsePositiveInt = (value, fallback) => {
    const n = parseInt(value, 10)
    return Number.isFinite(n) && n > 0 ? n : fallback
}
const parseBoolFlag = (value, defaultOn) => {
    if (value == null || value === '') return defaultOn
    const v = String(value).trim().toLowerCase()
    if (v === '0' || v === 'false' || v === 'off' || v === 'no') return false
    return true
}

// Express JSON body limit (raises the ~100KB default so /convertCode accepts larger snippets).
const KIT_MAX_HTTP_JSON_SIZE = parsePositiveInt(process.env.KIT_MAX_HTTP_JSON_SIZE, 2_000_000)
// Socket.IO payload limit — keep the historical ~100MB default so large deploys are not rejected.
const KIT_MAX_HTTP_BUFFER_SIZE = parsePositiveInt(process.env.KIT_MAX_HTTP_BUFFER_SIZE, 1e8)
const KIT_OFFLINE_TTL_MS = parsePositiveInt(process.env.KIT_OFFLINE_TTL_MS, 60 * 60 * 1000)
const KIT_OFFLINE_SWEEP_INTERVAL_MS = parsePositiveInt(process.env.KIT_OFFLINE_SWEEP_INTERVAL_MS, 5 * 60 * 1000)
const KIT_HEAP_WARN_MB = parsePositiveInt(process.env.KIT_HEAP_WARN_MB, 1024)
const KIT_LOG_META_MAX_LEN = parsePositiveInt(process.env.KIT_LOG_META_MAX_LEN, 2000)
const KIT_EXIT_ON_UNCAUGHT = parseBoolFlag(process.env.KIT_EXIT_ON_UNCAUGHT, true)
const KIT_ALERT_WEBHOOK_URL = (process.env.KIT_ALERT_WEBHOOK_URL || '').trim()
const KIT_ALERT_TIMEOUT_MS = parsePositiveInt(process.env.KIT_ALERT_TIMEOUT_MS, 3000)
const KIT_ALERT_MIN_INTERVAL_MS = parsePositiveInt(process.env.KIT_ALERT_MIN_INTERVAL_MS, 60 * 1000)
const MEMORY_PRESSURE_MIN_INTERVAL_MS = 60 * 1000

const app = express();
app.use(express.json({ limit: KIT_MAX_HTTP_JSON_SIZE }));
app.use(express.urlencoded({ extended: true, limit: KIT_MAX_HTTP_JSON_SIZE }));
const server = http.createServer(app);
const io = new Server(server, {
    maxHttpBufferSize: KIT_MAX_HTTP_BUFFER_SIZE,
    cors: {
        origin: '*',
    }
});

let KITS = new Map()
let CLIENTS = new Map()
let SYNCER_HW = new Map()
// Reverse indexes for O(1) disconnect resolution. Without these the disconnect
// handler did Array.from(KITS.values()).find(...) which is O(K) per disconnect
// and behaves like O(K^2) during connection-storm scenarios.
const SOCKET_TO_KIT = new Map() // socket.id -> kit_id
const SOCKET_TO_HW = new Map()  // socket.id -> kit_id

const LOG_PREFIX = '[KitManager]'
let lastDeveloperAlertAt = 0

function truncateForLog(str) {
    if (str == null) return ''
    const s = typeof str === 'string' ? str : String(str)
    if (s.length <= KIT_LOG_META_MAX_LEN) return s
    return `${s.slice(0, KIT_LOG_META_MAX_LEN)}...(truncated,len=${s.length})`
}

function formatMetaValue(value) {
    if (value === undefined || value === null) return String(value)
    if (typeof value === 'string') return truncateForLog(value)
    if (typeof value === 'number' || typeof value === 'boolean') return String(value)
    let serialized
    try {
        serialized = JSON.stringify(value)
    } catch (error) {
        serialized = '[unserializable]'
    }
    return truncateForLog(serialized)
}

function safeJsonStringify(value) {
    if (value == null) return ''
    try {
        return JSON.stringify(value)
    } catch (_) {
        try {
            return String(value)
        } catch (_inner) {
            return '[unserializable]'
        }
    }
}

function getMemoryStats() {
    const m = process.memoryUsage()
    const toMB = (b) => Math.round((b / (1024 * 1024)) * 100) / 100
    return {
        rssMB: toMB(m.rss),
        heapUsedMB: toMB(m.heapUsed),
        heapTotalMB: toMB(m.heapTotal),
        externalMB: toMB(m.external || 0),
        arrayBuffersMB: toMB(m.arrayBuffers || 0),
        uptimeSec: Math.round(process.uptime()),
    }
}

function buildHealthPayload() {
    const memory = getMemoryStats()
    const kitsOnline = countOnlineItems(KITS)
    const syncerHwOnline = countOnlineItems(SYNCER_HW)
    return {
        status: 'OK',
        bootId: BOOT_ID,
        pid: process.pid,
        uptimeSec: memory.uptimeSec,
        kitImageVersion: KIT_IMAGE_VERSION,
        kits: {
            total: KITS.size,
            online: kitsOnline,
            offline: KITS.size - kitsOnline,
        },
        syncerHw: {
            total: SYNCER_HW.size,
            online: syncerHwOnline,
            offline: SYNCER_HW.size - syncerHwOnline,
        },
        clients: {
            total: CLIENTS.size,
        },
        inFlightConverts: getInFlightConverts(),
        memory,
    }
}

function buildCrashContext(extra = {}) {
    let onlineKits = 0
    let onlineSyncerHw = 0
    try { onlineKits = countOnlineItems(KITS) } catch (_) { /* noop */ }
    try { onlineSyncerHw = countOnlineItems(SYNCER_HW) } catch (_) { /* noop */ }
    const memory = getMemoryStats()
    return Object.assign({
        kitsTotal: KITS.size,
        kitsOnline: onlineKits,
        syncerHwTotal: SYNCER_HW.size,
        syncerHwOnline: onlineSyncerHw,
        clientsTotal: CLIENTS.size,
        inFlightConverts: getInFlightConverts(),
        rssMB: memory.rssMB,
        heapUsedMB: memory.heapUsedMB,
        heapTotalMB: memory.heapTotalMB,
        externalMB: memory.externalMB,
        arrayBuffersMB: memory.arrayBuffersMB,
        uptimeSec: memory.uptimeSec,
    }, extra)
}

function log(level, event, meta = {}) {
    const ts = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z')
    const metaStr = Object.entries(meta)
        .map(([key, value]) => `${key}=${formatMetaValue(value)}`)
        .join(' ')
    const line = `${ts} ${LOG_PREFIX} [${event}]${metaStr ? ` ${metaStr}` : ''}`

    if (level === 'error') {
        console.error(line)
    } else if (level === 'warn') {
        console.warn(line)
    } else {
        console.log(line)
    }
}

function logCrashTrace(event, err) {
    const ctx = buildCrashContext({
        errorName: err && err.name,
        errorMessage: (err && err.message) || String(err),
        errorCode: err && err.code,
        errorStack: err && err.stack,
    })
    log('error', event, ctx)
}

function postJsonToWebhook(webhookUrl, payload, timeoutMs) {
    return new Promise((resolve, reject) => {
        let parsedUrl
        try {
            parsedUrl = new URL(webhookUrl)
        } catch (error) {
            reject(new Error(`Invalid KIT_ALERT_WEBHOOK_URL: ${error.message}`))
            return
        }

        const isHttps = parsedUrl.protocol === 'https:'
        if (!isHttps && parsedUrl.protocol !== 'http:') {
            reject(new Error(`Unsupported webhook protocol: ${parsedUrl.protocol}`))
            return
        }

        const body = JSON.stringify(payload)
        const req = (isHttps ? https : http).request({
            method: 'POST',
            hostname: parsedUrl.hostname,
            port: parsedUrl.port || (isHttps ? 443 : 80),
            path: `${parsedUrl.pathname}${parsedUrl.search}`,
            timeout: timeoutMs,
            headers: {
                'content-type': 'application/json',
                'content-length': Buffer.byteLength(body),
                'user-agent': 'kit-manager-alert/1.0',
            },
        }, (res) => {
            res.resume()
            res.on('end', () => {
                const statusCode = res.statusCode || 0
                if (statusCode >= 200 && statusCode < 300) {
                    resolve(statusCode)
                } else {
                    reject(new Error(`Webhook returned HTTP ${statusCode}`))
                }
            })
        })

        req.on('timeout', () => {
            req.destroy(new Error(`Webhook timed out after ${timeoutMs}ms`))
        })
        req.on('error', reject)
        req.write(body)
        req.end()
    })
}

async function sendDeveloperAlert(eventName, err, options = {}) {
    if (!KIT_ALERT_WEBHOOK_URL) {
        return false
    }

    const now = Date.now()
    if (now - lastDeveloperAlertAt < KIT_ALERT_MIN_INTERVAL_MS) {
        log('warn', 'DEVELOPER_ALERT_SUPPRESSED', {
            event: eventName,
            minIntervalMs: KIT_ALERT_MIN_INTERVAL_MS,
        })
        return false
    }
    lastDeveloperAlertAt = now

    const payload = {
        service: 'kit-manager',
        severity: options.severity || 'fatal',
        event: eventName,
        timestamp: new Date().toISOString(),
        bootId: BOOT_ID,
        pid: process.pid,
        kitImageVersion: KIT_IMAGE_VERSION,
        error: {
            name: err && err.name,
            message: (err && err.message) || String(err),
            code: err && err.code,
            stack: err && err.stack,
        },
        context: buildCrashContext(options.context || {}),
    }

    try {
        const statusCode = await postJsonToWebhook(KIT_ALERT_WEBHOOK_URL, payload, KIT_ALERT_TIMEOUT_MS)
        log('info', 'DEVELOPER_ALERT_SENT', {
            event: eventName,
            statusCode,
        })
        return true
    } catch (alertErr) {
        log('warn', 'DEVELOPER_ALERT_FAILED', {
            event: eventName,
            error: alertErr?.message || String(alertErr),
        })
        return false
    }
}

function handleFatal(eventName, err) {
    try {
        log('error', eventName, {
            error: (err && err.message) || String(err),
            code: err && err.code,
            stack: err && err.stack,
        })
        logCrashTrace('CRASH_TRACE', err)
    } catch (logErr) {
        // Last-resort: stderr write so we never lose the original failure to a logger bug.
        try { console.error('[KitManager] crash-log failure', logErr) } catch (_) { /* noop */ }
    }
    if (KIT_EXIT_ON_UNCAUGHT) {
        const forcedExit = setTimeout(() => process.exit(1), KIT_ALERT_TIMEOUT_MS + 500)
        if (typeof forcedExit.unref === 'function') forcedExit.unref()
        Promise.resolve()
            .then(() => sendDeveloperAlert(eventName, err))
            .finally(() => {
                clearTimeout(forcedExit)
                // setImmediate gives the current tick a chance to flush stdout before exit.
                setImmediate(() => process.exit(1))
            })
    } else {
        void sendDeveloperAlert(eventName, err)
    }
}

process.on('uncaughtException', (err) => {
    handleFatal('UNCAUGHT_EXCEPTION', err)
})

process.on('unhandledRejection', (reason) => {
    const err = reason instanceof Error ? reason : new Error(String(reason))
    handleFatal('UNHANDLED_REJECTION', err)
})

const SHUTDOWN_SIGNALS = ['SIGTERM', 'SIGINT', 'SIGHUP', 'SIGQUIT']
const SIGNAL_NUMBERS = { SIGTERM: 15, SIGINT: 2, SIGHUP: 1, SIGQUIT: 3 }
SHUTDOWN_SIGNALS.forEach((signal) => {
    process.on(signal, () => {
        log('warn', 'SHUTDOWN_SIGNAL', {
            signal,
            pid: process.pid,
            bootId: BOOT_ID,
            uptimeSec: Math.round(process.uptime()),
            totalKits: KITS.size,
            onlineKits: countOnlineItems(KITS),
            totalSyncerHw: SYNCER_HW.size,
            totalClients: CLIENTS.size,
        })
        const signalNumber = SIGNAL_NUMBERS[signal] || 0
        setImmediate(() => process.exit(128 + signalNumber))
    })
})

process.on('beforeExit', (code) => {
    log('warn', 'BEFORE_EXIT', {
        code,
        pid: process.pid,
        bootId: BOOT_ID,
        uptimeSec: Math.round(process.uptime()),
    })
})

process.on('exit', (code) => {
    const meta = {
        code,
        pid: process.pid,
        bootId: BOOT_ID,
        uptimeSec: Math.round(process.uptime()),
        totalKits: KITS.size,
        totalSyncerHw: SYNCER_HW.size,
        totalClients: CLIENTS.size,
    }
    const ts = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z')
    const metaStr = Object.entries(meta)
        .map(([key, value]) => `${key}=${formatMetaValue(value)}`)
        .join(' ')
    const banner = [
        '---------------------------------------------------------------',
        '------------- PROCESS EXIT ------------------------------------',
        '---------------------------------------------------------------',
        `${ts} ${LOG_PREFIX} [PROCESS_EXIT] ${metaStr}`,
        '---------------------------------------------------------------',
    ].join('\n') + '\n'
    try {
        fs.writeSync(1, banner)
    } catch (_) {
        try { console.log(banner) } catch (_inner) { /* noop */ }
    }
})

io.engine.on('connection_error', (err) => {
    let contextStr = ''
    if (err && err.context != null) {
        contextStr = safeJsonStringify(err.context).slice(0, 200)
    }
    log('warn', 'SOCKET_HANDSHAKE_FAILED', {
        code: err?.code,
        message: err?.message,
        context: contextStr,
        remote: err?.req?.socket?.remoteAddress || '',
    })
})

function countOnlineItems(itemMap) {
    let online = 0
    itemMap.forEach((item) => {
        if (item.is_online) online += 1
    })
    return online
}

const NOISY_FORWARD_CMDS = new Set(
    (process.env.KIT_LOG_QUIET_CMDS || 'get-runtime-info,subscribe_apis,unsubscribe_apis')
        .split(',').map(s => s.trim()).filter(Boolean)
)

function summarizeMap(itemMap, max = 20) {
    const parts = []
    let i = 0
    for (const item of itemMap.values()) {
        if (i >= max) {
            parts.push(`(+${itemMap.size - max} more)`)
            break
        }
        parts.push(`${item.kit_id}:${item.is_online ? 'on' : 'off'}`)
        i += 1
    }
    return parts.join(',')
}

function partitionByStatus(itemMap) {
    const online = []
    const offline = []
    for (const item of itemMap.values()) {
        if (item.is_online) {
            online.push(item.kit_id)
        } else {
            offline.push(item.kit_id)
        }
    }
    return { online, offline }
}

const HEARTBEAT_ENABLED = process.env.KIT_LOG_HEARTBEAT !== '0'

// setInterval(() => {
//     console.log(`KITS: ${KITS.size}`)
//     KITS.forEach((kit, kit_id) => {
//         console.log(`Kit ${kit_id} is online: ${kit.is_online}`)
//     })

//     console.log(`CLIENTS: ${CLIENTS.size}`)
//     CLIENTS.forEach((client, client_id) => {
//         console.log(`Client ${client_id} is online: ${client.is_online}`)
//     })
// }, 3000)

let hasKitStateChange = false
let hasHwStateChange = false

app.use(cors({
    origin: '*'
}));

app.get('/healthz', (req, res) => {
    return res.json(buildHealthPayload())
});

app.get('/listAllKits', (req, res) => {
    return res.json({
        status: "OK",
        message: "List all kits",
        content: Array.from(KITS.values())
    })
});

app.get('/listAllClient', (req, res) => {
    return res.json({
        status: "OK",
        message: "List all clients",
        content: Array.from(CLIENTS.values())
    })
});

app.post('/convertCode', async (req, res) => {
    if(!req.body.code) {
        return res.json({
                status: "ERR",
                message: "Missing code",
        })
    }
    try {
        const convertedCode = await convertPgCode('VehicleApp', req.body.code || '')
        return res.json({
            status: "OK",
            message: "Successful",
            content: convertedCode
        })
    } catch (error) {
        const code = error && error.code
        log('error', 'CONVERT_CODE_HTTP_FAILED', {
            error: error?.message || String(error),
            code,
        })
        if (code === 'CODE_TOO_LARGE') {
            return res.status(413).json({ status: 'ERR', message: 'Code payload too large', code })
        }
        if (code === 'CONVERT_TIMEOUT') {
            return res.status(504).json({ status: 'ERR', message: 'Code conversion timed out', code })
        }
        if (code === 'CONVERT_BUSY') {
            return res.status(503).json({ status: 'ERR', message: 'Converter at capacity, retry later', code })
        }
        return res.status(500).json({
            status: 'ERR',
            message: 'Code conversion failed',
        })
    }
})

function logRosterDetail(event, itemMap, onlineKey, offlineKey) {
    const { online, offline } = partitionByStatus(itemMap)
    log('info', event, {
        [onlineKey]: online.length ? online.join(',') : '(none)',
    })
    log('info', event, {
        [offlineKey]: offline.length ? offline.join(',') : '(none)',
    })
}

function announceListOfKit() {
    CLIENTS.forEach((client, client_id) => {
        io.to(client_id).emit('list-all-kits-result', Array.from(KITS.values()))
    })
    hasKitStateChange = false
    const totalKits = KITS.size
    const onlineKits = countOnlineItems(KITS)
    log('info', 'KIT_LIST_CHANGED', {
        totalKits,
        onlineKits,
        offlineKits: totalKits - onlineKits,
    })
    logRosterDetail('KIT_LIST_CHANGED', KITS, 'online', 'offline')
}

function announceListOfHw() {
    CLIENTS.forEach((client, client_id) => {
        io.to(client_id).emit('list-all-hw-result', Array.from(SYNCER_HW.values()))
    })
    hasHwStateChange = false
    const totalSyncerHw = SYNCER_HW.size
    const onlineSyncerHw = countOnlineItems(SYNCER_HW)
    log('info', 'SYNCER_HW_LIST_CHANGED', {
        totalSyncerHw,
        onlineSyncerHw,
        offlineSyncerHw: totalSyncerHw - onlineSyncerHw,
    })
    logRosterDetail('SYNCER_HW_LIST_CHANGED', SYNCER_HW, 'online', 'offline')
}

const announceInterval = setInterval(() => {
        if(hasKitStateChange) {
                announceListOfKit()
        }
        if(hasHwStateChange) {
                announceListOfHw()
        }
}, 1000)

let lastMemoryPressureLogAt = 0
let HEARTBEAT_SEQ = 0
const heartbeatInterval = setInterval(() => {
    if (!HEARTBEAT_ENABLED) {
        return
    }
    HEARTBEAT_SEQ += 1
    const totalKits = KITS.size
    const onlineKits = countOnlineItems(KITS)
    const totalSyncerHw = SYNCER_HW.size
    const onlineSyncerHw = countOnlineItems(SYNCER_HW)
    const memory = getMemoryStats()
    const inFlight = getInFlightConverts()
    log('info', 'HEARTBEAT', {
        seq: HEARTBEAT_SEQ,
        pid: process.pid,
        bootId: BOOT_ID,
        totalKits,
        onlineKits,
        offlineKits: totalKits - onlineKits,
        totalSyncerHw,
        onlineSyncerHw,
        offlineSyncerHw: totalSyncerHw - onlineSyncerHw,
        totalClients: CLIENTS.size,
        inFlightConverts: inFlight,
        rssMB: memory.rssMB,
        heapUsedMB: memory.heapUsedMB,
        heapTotalMB: memory.heapTotalMB,
        externalMB: memory.externalMB,
        arrayBuffersMB: memory.arrayBuffersMB,
        uptimeSec: memory.uptimeSec,
    })
    if (memory.heapUsedMB >= KIT_HEAP_WARN_MB) {
        const now = Date.now()
        if (now - lastMemoryPressureLogAt >= MEMORY_PRESSURE_MIN_INTERVAL_MS) {
            lastMemoryPressureLogAt = now
            log('warn', 'MEMORY_PRESSURE', {
                heapUsedMB: memory.heapUsedMB,
                heapTotalMB: memory.heapTotalMB,
                rssMB: memory.rssMB,
                thresholdMB: KIT_HEAP_WARN_MB,
                totalKits,
                totalSyncerHw,
                totalClients: CLIENTS.size,
                inFlightConverts: inFlight,
            })
        }
    }
    logRosterDetail('HEARTBEAT', KITS, 'kitsOnline', 'kitsOffline')
    logRosterDetail('HEARTBEAT', SYNCER_HW, 'syncerHwOnline', 'syncerHwOffline')
}, 10000)

// Periodic eviction sweeper for stale offline KITS / SYNCER_HW entries (C-4).
// Without this the maps grow unbounded over time. Offline entries remain
// visible to clients until they hit the TTL so the current UX is preserved.
function evictStaleOfflineEntries(itemMap, kindLabel, evictEvent) {
    const ttl = KIT_OFFLINE_TTL_MS
    if (!Number.isFinite(ttl) || ttl <= 0) return 0
    const now = Date.now()
    const toDelete = []
    itemMap.forEach((item, key) => {
        if (!item) {
            toDelete.push({ key, item: null, offlineForSec: 0 })
            return
        }
        if (item.is_online === false) {
            const lastSeen = typeof item.last_seen === 'number' ? item.last_seen : 0
            const offlineFor = now - lastSeen
            if (offlineFor > ttl) {
                toDelete.push({ key, item, offlineForSec: Math.round(offlineFor / 1000) })
            }
        }
    })
    toDelete.forEach(({ key, item, offlineForSec }) => {
        itemMap.delete(key)
        log('info', evictEvent, {
            kitId: (item && item.kit_id) || key,
            name: (item && item.name) || '',
            offlineForSec,
            totalAfterEvict: itemMap.size,
        })
    })
    return toDelete.length
}

const offlineSweepInterval = setInterval(() => {
    const evictedKits = evictStaleOfflineEntries(KITS, 'KIT', 'KIT_EVICTED')
    const evictedHw = evictStaleOfflineEntries(SYNCER_HW, 'SYNCER_HW', 'SYNCER_HW_EVICTED')
    if (evictedKits > 0) hasKitStateChange = true
    if (evictedHw > 0) hasHwStateChange = true
}, KIT_OFFLINE_SWEEP_INTERVAL_MS)

// Keep references so phase 2 (graceful shutdown) can clearInterval on SIGTERM.
// In this phase the intervals run for the lifetime of the process.
void announceInterval; void heartbeatInterval; void offlineSweepInterval;

io.on('connection', (socket) => {
    log('info', 'SOCKET_CONNECTED', { socketId: socket.id })

    socket.on('error', (err) => {
        log('warn', 'SOCKET_ERROR', {
            socketId: socket.id,
            error: err?.message || String(err),
        })
    })
    /**
     * Register a kit
     */
    socket.on('register_kit', (payload) => {
        if(!payload || !payload.kit_id) {
            log('warn', 'REGISTER_KIT_INVALID_PAYLOAD', { socketId: socket.id })
            return;
        }
        const existing = KITS.get(payload.kit_id)
        if (existing && existing.socket_id && existing.socket_id !== socket.id) {
            // Another socket previously owned this kit_id. Drop the stale
            // reverse-index entry so it can't be resurrected on its disconnect.
            SOCKET_TO_KIT.delete(existing.socket_id)
        }
        KITS.set(payload.kit_id, {
            socket_id: socket.id,
            kit_id: payload.kit_id,
            name: payload.name || '',
            last_seen: new Date().getTime(),
            is_online: true,
            noRunner: 0,
            noSubscriber: 0,
            support_apis: payload.support_apis || [],
            desc: payload.desc || '',
        })
        SOCKET_TO_KIT.set(socket.id, payload.kit_id)
        hasKitStateChange = true
        log('info', 'REGISTER_KIT', {
            socketId: socket.id,
            kitId: payload.kit_id,
            name: payload.name || '',
            supportApiCount: (payload.support_apis || []).length,
            totalKits: KITS.size,
            onlineKits: countOnlineItems(KITS),
        })
    })

    socket.on('register_hw_kit', (payload) => {
        if(!payload || !payload.kit_id) {
            log('warn', 'REGISTER_SYNCER_HW_INVALID_PAYLOAD', { socketId: socket.id })
            return;
        }
        const existingHw = SYNCER_HW.get(payload.kit_id)
        if (existingHw && existingHw.socket_id && existingHw.socket_id !== socket.id) {
            SOCKET_TO_HW.delete(existingHw.socket_id)
        }
        SYNCER_HW.set(payload.kit_id, {
            socket_id: socket.id,
            kit_id: payload.kit_id,
            name: payload.name || '',
            last_seen: new Date().getTime(),
            is_online: true,
            support_apis: payload.support_apis || [],
            desc: payload.desc || '',
        })
        SOCKET_TO_HW.set(socket.id, payload.kit_id)
        hasHwStateChange = true
        log('info', 'REGISTER_SYNCER_HW', {
            socketId: socket.id,
            kitId: payload.kit_id,
            name: payload.name || '',
            supportApiCount: (payload.support_apis || []).length,
            totalSyncerHw: SYNCER_HW.size,
            onlineSyncerHw: countOnlineItems(SYNCER_HW),
        })
    })

    socket.on('report-runtime-state', (payload) => {
        let kit_id = payload?.kit_id || null
        if(kit_id && payload.data) {
            let kit = KITS.get(kit_id)
            if(!kit) {
                log('warn', 'REPORT_RUNTIME_STATE_UNKNOWN_KIT', { socketId: socket.id, kitId: kit_id })
                return
            }
            kit.noRunner = payload.data.noOfRunner || 0
            kit.noSubscriber = payload.data.noSubscriber || 0
            KITS.set(kit_id, kit)
            hasKitStateChange = true
        }
    })

    /**
     * Register a client
     */
    socket.on('register_client', (payload) => {
        if(!payload) {
            log('warn', 'REGISTER_CLIENT_INVALID_PAYLOAD', { socketId: socket.id })
            return;
        }
        CLIENTS.set(socket.id, {
            username: payload.username,
            user_id: payload.user_id,
            domain: payload.domain,
            last_seen: new Date().getTime(),
            is_online: true,
        })
        log('info', 'REGISTER_CLIENT', {
            socketId: socket.id,
            userId: payload.user_id || '',
            username: payload.username || '',
            domain: payload.domain || '',
            totalClients: CLIENTS.size,
        })
        socket.emit('list-all-kits-result', Array.from(KITS.values()))
        socket.emit('list-all-hw-result', Array.from(SYNCER_HW.values()))
    });

    socket.on('unregister_client', (payload) => {
        let existClient = CLIENTS.get(socket.id)
        if(existClient) {
            CLIENTS.delete(socket.id)
            log('info', 'UNREGISTER_CLIENT', {
                socketId: socket.id,
                userId: existClient.user_id || '',
                username: existClient.username || '',
                payloadReason: payload?.reason || '',
                totalClients: CLIENTS.size,
            })
        } else {
            log('warn', 'UNREGISTER_CLIENT_NOT_FOUND', { socketId: socket.id })
        }
    });

    socket.on('clientSubscribeToKit', (payload) => {
        if(!payload || !payload.kit_id) {
            log('warn', 'SUBSCRIBE_INVALID_PAYLOAD', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
            })
            return;
        }
        socket.join(payload.kit_id)
    });

    socket.on('clientUnsubscribeToKit', (payload) => {
        if(!payload || !payload.kit_id) {
            log('warn', 'UNSUBSCRIBE_INVALID_PAYLOAD', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
            })
            return;
        }
        socket.leave(payload.kit_id)
    });


    socket.on('list-all-kits', () => {
        log('info', 'LIST_ALL_KITS_REQUEST', { socketId: socket.id, totalKits: KITS.size })
        socket.emit('list-all-kits-result', Array.from(KITS.values()))
    });

    socket.on('list-all-syncer_hw', () => {
        log('info', 'LIST_ALL_SYNCER_HW_REQUEST', { socketId: socket.id, totalSyncerHw: SYNCER_HW.size })
        socket.emit('list-all-hw-result', Array.from(SYNCER_HW.values()))
    });

    /**
     * Handle disconnection
     */
     socket.on('disconnect', (reason) => {
        // --------------------------------------------
        // Resolve the disconnected kit in O(1) via the reverse index. The map
        // entry itself stays (marked offline) so clients can still see the kit;
        // the periodic sweeper evicts entries that have been offline > TTL.
        const kitId = SOCKET_TO_KIT.get(socket.id)
        let existKit = kitId ? KITS.get(kitId) : undefined
        if (existKit && existKit.socket_id === socket.id) {
            existKit.is_online = false
            existKit.last_seen = new Date().getTime()
            hasKitStateChange = true
            log('info', 'KIT_DISCONNECTED', {
                socketId: socket.id,
                kitId: existKit.kit_id,
                reason,
                totalKits: KITS.size,
                onlineKits: countOnlineItems(KITS),
            })
            announceListOfKit()
        } else {
            // Defensive: reverse-index points to a kit no longer owned by this
            // socket (e.g. another socket re-registered the same kit_id). Ignore.
            existKit = undefined
        }
        SOCKET_TO_KIT.delete(socket.id)
        //---------------------------------------------
        const hwKitId = SOCKET_TO_HW.get(socket.id)
        let existSyncerHW = hwKitId ? SYNCER_HW.get(hwKitId) : undefined
        if (existSyncerHW && existSyncerHW.socket_id === socket.id) {
            existSyncerHW.is_online = false
            existSyncerHW.last_seen = new Date().getTime()
            hasHwStateChange = true
            log('info', 'SYNCER_HW_DISCONNECTED', {
                socketId: socket.id,
                kitId: existSyncerHW.kit_id,
                reason,
                totalSyncerHw: SYNCER_HW.size,
                onlineSyncerHw: countOnlineItems(SYNCER_HW),
            })
        } else {
            existSyncerHW = undefined
        }
        SOCKET_TO_HW.delete(socket.id)
        // --------------------------------------------
        let existClient = CLIENTS.get(socket.id)
        if(existClient) {
            CLIENTS.delete(socket.id)
            log('info', 'CLIENT_DISCONNECTED', {
                socketId: socket.id,
                userId: existClient.user_id || '',
                username: existClient.username || '',
                reason,
                totalClients: CLIENTS.size,
            })
        }
        if(!existKit && !existSyncerHW && !existClient) {
            log('warn', 'SOCKET_DISCONNECTED_UNKNOWN_ACTOR', { socketId: socket.id, reason })
        }
    });

    // ------------ MESSAGE FROM CLIENT TO KIT ----------------
    socket.on('messageToKit', async (payload) => {
        if(!payload || !payload.cmd || !payload.to_kit_id) {
            log('warn', 'MESSAGE_TO_KIT_INVALID_PAYLOAD', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
                cmd: payload?.cmd,
                toKitId: payload?.to_kit_id,
            })
            return;
        }
        let kit = KITS.get(payload.to_kit_id)
        if(kit) {
            if(["deploy_request", "deploy_n_run"].includes(payload.cmd)) {
                let convertedCode =  ''
                try {
                    if(payload.disable_code_convert) {
                        convertedCode = payload.code
                    } else {
                        convertedCode = await convertPgCode(payload.prototype?.name || 'App', payload.code || '')
                    }
                } catch (error) {
                    const code = error && error.code
                    log('error', 'MESSAGE_TO_KIT_CODE_CONVERT_FAILED', {
                        socketId: socket.id,
                        cmd: payload.cmd,
                        toKitId: payload.to_kit_id,
                        requestFrom: socket.id,
                        error: error?.message || String(error),
                        code,
                    })
                    let replyMessage = 'Code conversion failed'
                    if (code === 'CODE_TOO_LARGE') replyMessage = 'Code payload too large'
                    else if (code === 'CONVERT_TIMEOUT') replyMessage = 'Code conversion timed out'
                    else if (code === 'CONVERT_BUSY') replyMessage = 'Converter at capacity, retry later'
                    io.to(socket.id).emit('messageToKit-kitReply', {
                        status: 'ERR',
                        cmd: payload.cmd,
                        to_kit_id: payload.to_kit_id,
                        request_from: socket.id,
                        message: replyMessage,
                        code,
                    })
                    return
                }
                if (!NOISY_FORWARD_CMDS.has(payload.cmd)) {
                    log('info', 'MESSAGE_TO_KIT_FORWARD', {
                        socketId: socket.id,
                        cmd: payload.cmd,
                        toKitId: payload.to_kit_id,
                        requestFrom: socket.id,
                        converted: true,
                    })
                }
                io.to(kit.socket_id).emit('messageToKit', {
                    request_from: socket.id,
                    ...payload,
                    convertedCode: convertedCode
                })
            } else {
                if (!NOISY_FORWARD_CMDS.has(payload.cmd)) {
                    log('info', 'MESSAGE_TO_KIT_FORWARD', {
                        socketId: socket.id,
                        cmd: payload.cmd,
                        toKitId: payload.to_kit_id,
                        requestFrom: socket.id,
                        converted: false,
                    })
                }
                io.to(kit.socket_id).emit('messageToKit', {
                    request_from: socket.id,
                    ...payload
                })
            }
        } else {
            log('warn', 'MESSAGE_TO_KIT_TARGET_NOT_FOUND', {
                socketId: socket.id,
                cmd: payload.cmd,
                toKitId: payload.to_kit_id,
                requestFrom: socket.id,
            })
        }
    })
    socket.on('messageToKit-kitReply', (payload) => {
        if(!payload || !payload.request_from) {
            log('warn', 'MESSAGE_TO_KIT_REPLY_INVALID_PAYLOAD', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
            })
            return;
        }
        if (!NOISY_FORWARD_CMDS.has(payload.cmd)) {
            log('info', 'MESSAGE_TO_KIT_REPLY_FORWARD', {
                socketId: socket.id,
                cmd: payload.cmd || '',
                requestTo: payload.request_from,
            })
        }
        io.to(payload.request_from).emit('messageToKit-kitReply', payload)
    })

    // ------------ MESSAGE FROM KIT TO CLIENT ----------------
    socket.on('broadcastToClient', (payload) => {
        if(!payload || !payload.cmd || !payload.kit_id) {
            log('warn', 'BROADCAST_TO_CLIENT_INVALID', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
                cmd: payload?.cmd,
                kitId: payload?.kit_id,
            })
            return;
        }
        let kit = KITS.get(payload.kit_id)
        if(kit && kit.socket_id == socket.id) {
            io.to(payload.kit_id).emit('broadcastToClient', payload) 
        } else {
            log('warn', 'BROADCAST_TO_CLIENT_INVALID', {
                socketId: socket.id,
                cmd: payload.cmd,
                kitId: payload.kit_id,
                reason: kit ? 'socket_owner_mismatch' : 'kit_not_found',
            })
        }
    })

    // ------------ MESSAGE FROM CLIENT TO KIT ----------------
    socket.on('messageToSyncerHw', (payload) => {
        if(!payload || !payload.cmd || !payload.to_kit_id) {
            log('warn', 'MESSAGE_TO_SYNCER_HW_INVALID_PAYLOAD', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
                cmd: payload?.cmd,
                toKitId: payload?.to_kit_id,
            })
            return;
        }
        if(payload.cmd == 'syncer_set') {
            let kit = SYNCER_HW.get(payload.to_kit_id)
            if(kit) {
                log('info', 'MESSAGE_TO_SYNCER_HW_FORWARD', {
                    socketId: socket.id,
                    cmd: payload.cmd,
                    toKitId: payload.to_kit_id,
                    requestFrom: socket.id,
                })
                io.to(kit.socket_id).emit('messageToSyncerHw', {
                    request_from: socket.id,
                    ...payload
                })
            } else {
                log('warn', 'MESSAGE_TO_SYNCER_HW_TARGET_NOT_FOUND', {
                    socketId: socket.id,
                    cmd: payload.cmd,
                    toKitId: payload.to_kit_id,
                    requestFrom: socket.id,
                })
            }
        } else {
            log('warn', 'MESSAGE_TO_SYNCER_HW_UNSUPPORTED_CMD', {
                socketId: socket.id,
                cmd: payload.cmd,
                toKitId: payload.to_kit_id,
            })
        }
    })
    socket.on('messageToSyncerHw-kitReply', (payload) => {
        if(!payload || !payload.request_from) {
            log('warn', 'MESSAGE_TO_SYNCER_HW_REPLY_INVALID_PAYLOAD', {
                socketId: socket.id,
                hasPayload: Boolean(payload),
            })
            return;
        }
        log('info', 'MESSAGE_TO_SYNCER_HW_REPLY_FORWARD', {
            socketId: socket.id,
            cmd: payload.cmd || '',
            requestTo: payload.request_from,
        })
        io.to(payload.request_from).emit('messageToKit-kitReply', payload)
    })

});

server.listen(config.port, () => {
    log('info', 'SERVER_STARTED', {
        port: config.port,
        pid: process.pid,
        bootId: BOOT_ID,
        kitImageVersion: KIT_IMAGE_VERSION,
    });
});

server.on('error', (err) => {
    log('error', 'HTTP_SERVER_ERROR', {
        error: err?.message,
        code: err?.code,
    })
    void sendDeveloperAlert('HTTP_SERVER_ERROR', err, { severity: 'error' })
})

server.on('close', () => {
    log('warn', 'HTTP_SERVER_CLOSED', {
        pid: process.pid,
        bootId: BOOT_ID,
        uptimeSec: Math.round(process.uptime()),
        totalKits: KITS.size,
        totalSyncerHw: SYNCER_HW.size,
        totalClients: CLIENTS.size,
    })
})