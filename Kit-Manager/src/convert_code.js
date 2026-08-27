// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// const fs = require('fs');
const { ProjectGenerator } = require("./generator/project-generator");


// const CodeConverter = require('./generator_lastest').CodeConverter;
// const path = require('path');
// const VELOCITAS_TEMPLATE_MAINPY = fs.readFileSync(`${path.join(__dirname, 'velocitas_template_main.py')}`, 'utf8');

// const convertPgCode = (appName, pgCode) => {
//     const codeConverter = new CodeConverter();
//     let retCode = ''
//     retCode = codeConverter.convertMainPy(VELOCITAS_TEMPLATE_MAINPY, pgCode, appName)

//     console.log("retCode")
//     console.log(retCode)

//     return retCode
// }

const encodeToBase64 = (code) => {
    return Buffer.from(code).toString("base64")
}

// ---------------------------------------------------------------------------
// Convert-flow safety: bound CPU and memory exposure (C-3).
//   - KIT_MAX_CODE_BYTES: max decoded Python source size accepted by the converter.
//   - KIT_CONVERT_TIMEOUT_MS: wall-clock budget per conversion (regex pipeline can be O(N^2)).
//   - KIT_CONVERT_CONCURRENCY: hard cap on in-flight conversions; excess requests are rejected
//     with code=CONVERT_BUSY rather than queued (queueing is unbounded and itself a memory risk).
// All limits are env-tunable so they can be raised/lowered without code changes.
// ---------------------------------------------------------------------------
const parsePositiveInt = (value, fallback) => {
    const n = parseInt(value, 10);
    return Number.isFinite(n) && n > 0 ? n : fallback;
};

const MAX_CODE_BYTES = parsePositiveInt(process.env.KIT_MAX_CODE_BYTES, 1048576);
const CONVERT_TIMEOUT_MS = parsePositiveInt(process.env.KIT_CONVERT_TIMEOUT_MS, 30000);
const CONVERT_CONCURRENCY = parsePositiveInt(process.env.KIT_CONVERT_CONCURRENCY, 8);

class ConvertError extends Error {
    constructor(code, message) {
        super(message || code);
        this.name = 'ConvertError';
        this.code = code;
    }
}

let inFlightConverts = 0;
const getInFlightConverts = () => inFlightConverts;

// Guards async-stage hangs only: while runWithPayload is synchronously churning through
// its regex/array pipeline, the event loop is blocked and this timer cannot fire. The
// real bound on pathological CPU-bound input is MAX_CODE_BYTES above, not this timeout.
const withTimeout = (promise, ms, code) => {
    let timer;
    const timeoutPromise = new Promise((_, reject) => {
        timer = setTimeout(() => reject(new ConvertError(code, `Conversion exceeded ${ms}ms`)), ms);
    });
    return Promise.race([promise, timeoutPromise]).finally(() => clearTimeout(timer));
};

const convertPgCode = async (appName, code, vss_payload) => {
    const safeCode = code == null ? '' : String(code);
    const codeBytes = Buffer.byteLength(safeCode, 'utf8');
    if (codeBytes > MAX_CODE_BYTES) {
        throw new ConvertError('CODE_TOO_LARGE', `Code size ${codeBytes} exceeds limit ${MAX_CODE_BYTES}`);
    }

    if (inFlightConverts >= CONVERT_CONCURRENCY) {
        throw new ConvertError('CONVERT_BUSY', `Converter at capacity (${CONVERT_CONCURRENCY})`);
    }

    inFlightConverts += 1;
    try {
        const safeAppName = (appName == null ? '' : String(appName));
        const finalAppName = safeAppName.replace(/[^a-zA-Z0-9]/gi, '')
        const generator = new ProjectGenerator("", (finalAppName), "")
        const payload = encodeToBase64(JSON.stringify(vss_payload || {}))
        try {
            const convertedCode = await withTimeout(
                generator.runWithPayload(encodeToBase64(safeCode), finalAppName, payload),
                CONVERT_TIMEOUT_MS,
                'CONVERT_TIMEOUT'
            )
            if(convertedCode) {
                let result = convertedCode.finalizedMainPy
                result = result.replace(`import logging`, `import logging\r\nfrom logging.handlers import RotatingFileHandler`)
                result = result.replace(`logging.getLogger().setLevel("DEBUG")`, `logging.getLogger().setLevel("INFO")`)
                result = result.replace(`logging.basicConfig(format=get_opentelemetry_log_format())`,
                                        `logging.basicConfig(filename='app.log', filemode='a',format="[%(asctime)s] %(message)s")`)

                result = result.replace(`logger = logging.getLogger(__name__)`,`logger = logging.getLogger(__name__)\r\nhandler = RotatingFileHandler('app.log', maxBytes=1048576, backupCount=1)\r\nlogger.addHandler(handler)`)
                return result
            }
        } catch(err) {
            if (err && err.code === 'CONVERT_TIMEOUT') {
                throw err;
            }
            console.log("error on converted code")
            console.log(err)
        }
        return null
    } catch (error) {
        console.log("error on generateCode", error)
        throw error;
    } finally {
        inFlightConverts = Math.max(0, inFlightConverts - 1)
    }
}

module.exports = convertPgCode;
module.exports.ConvertError = ConvertError;
module.exports.getInFlightConverts = getInFlightConverts;
module.exports.LIMITS = {
    MAX_CODE_BYTES,
    CONVERT_TIMEOUT_MS,
    CONVERT_CONCURRENCY,
};
