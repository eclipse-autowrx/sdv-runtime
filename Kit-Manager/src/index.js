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
const { Server } = require('socket.io');
const config = require('../configs');
const convertPgCode = require('./convert_code');
const cors = require('cors');
const { spawn } = require('child_process');

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
const server = http.createServer(app); 
const io = new Server(server, {
    maxHttpBufferSize: 1e8,
    cors: {
        origin: '*',
    }
});

let KITS = new Map()
let CLIENTS = new Map()
let SYNCER_HW = new Map()

// C++ Compilation environment detection
const base_cpp_path = '/home/dev'
console.log(`Compilation base path: ${base_cpp_path}`)

// Helper functions for C++ compilation
async function createMinimalSdkTemplate(dest) {
    await fs.promises.mkdir(dest, { recursive: true });
    await fs.promises.mkdir(path.join(dest, 'app'), { recursive: true });
    await fs.promises.mkdir(path.join(dest, 'build'), { recursive: true });
    
    const rootCMake = `cmake_minimum_required(VERSION 3.16)
project(TestApp CXX)

set(CMAKE_CXX_STANDARD 17)
find_package(Threads REQUIRED)

add_subdirectory(app)
`;
    
    const appCMake = `cmake_minimum_required(VERSION 3.16)

add_subdirectory(src)
`;

    await fs.promises.writeFile(path.join(dest, 'CMakeLists.txt'), rootCMake);
    await fs.promises.writeFile(path.join(dest, 'app', 'CMakeLists.txt'), appCMake);
}

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

app.use(cors({
    origin: '*'
}));

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
    let convertedCode = await convertPgCode('VehicleApp', req.body.code || '')
    return res.json({
        status: "OK",
        message: "Successful",
        content: convertedCode
    })
})

function announceListOfKit() {
        // console.log("announceListOfHw to all clients")
    CLIENTS.forEach((client, client_id) => {
        io.to(client_id).emit('list-all-kits-result', Array.from(KITS.values()))
    })
        hasKitStateChange = false
}

function announceListOfHw() {
    CLIENTS.forEach((client, client_id) => {
        io.to(client_id).emit('list-all-hw-result', Array.from(SYNCER_HW.values()))
    })
}

setInterval(() => {
        if(hasKitStateChange) {
                announceListOfKit()
        }
}, 1000)

io.on('connection', (socket) => {
    /**
     * Register a kit
     */
    socket.on('register_kit', (payload) => {
        if(!payload || !payload.kit_id) return;
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
                hasKitStateChange = true
        //announceListOfKit()
    })

    socket.on('register_hw_kit', (payload) => {
        if(!payload || !payload.kit_id) return;
        SYNCER_HW.set(payload.kit_id, {
            socket_id: socket.id,
            kit_id: payload.kit_id,
            name: payload.name || '',
            last_seen: new Date().getTime(),
            is_online: true,
            support_apis: payload.support_apis || [],
            desc: payload.desc || '',
        })
    })

    socket.on('report-runtime-state', (payload) => {
        let kit_id = payload && payload.kit_id ? payload.kit_id : null
        if(kit_id && payload.data) {
                        let kit = KITS.get(kit_id)
                        if(!kit) return
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
        if(!payload) return;
        CLIENTS.set(socket.id, {
            username: payload.username,
            user_id: payload.user_id,
            domain: payload.domain,
            last_seen: new Date().getTime(),
            is_online: true,
        })
        socket.emit('list-all-kits-result', Array.from(KITS.values()))
        socket.emit('list-all-hw-result', Array.from(SYNCER_HW.values()))
    });

    socket.on('unregister_client', (payload) => {
        let existClient = CLIENTS.get(socket.id)
        if(existClient) {
            CLIENTS.delete(socket.id)
        }
    });

    socket.on('clientSubscribeToKit', (payload) => {
        if(!payload || !payload.kit_id) return;
        socket.join(payload.kit_id)
    });

    socket.on('clientUnsubscribeToKit', (payload) => {
        if(!payload || !payload.kit_id) return;
        socket.leave(payload.kit_id)
    });


    socket.on('list-all-kits', () => {
        socket.emit('list-all-kits-result', Array.from(KITS.values()))
    });

    socket.on('list-all-syncer_hw', () => {
        socket.emit('list-all-hw-result', Array.from(SYNCER_HW.values()))
    });

    /**
     * Handle disconnection
     */
     socket.on('disconnect', () => {
        // --------------------------------------------
        let existKit = Array.from(KITS.values()).find(kit => kit.socket_id == socket.id)
        if(existKit) {
            existKit.is_online = false
            existKit.last_seen = new Date().getTime()
            announceListOfKit()
        }
        //---------------------------------------------
        let existSyncerHW = Array.from(SYNCER_HW.values()).find(hw => hw.socket_id == socket.id)
        if(existSyncerHW) {
            existSyncerHW.is_online = false
            existSyncerHW.last_seen = new Date().getTime()
            announceListOfHw()
        }
        // --------------------------------------------
        let existClient = CLIENTS.get(socket.id)
        if(existClient) {
            CLIENTS.delete(socket.id)
        }
    });

    // ------------ MESSAGE FROM CLIENT TO KIT ----------------
    socket.on('messageToKit', async (payload) => {
        if(!payload || !payload.cmd || !payload.to_kit_id) return;
        let kit = KITS.get(payload.to_kit_id)
        if(kit) {
            if(["deploy_request", "deploy_n_run"].includes(payload.cmd)) {
                // console.log(payload)
                let convertedCode =  ''
                if(payload.disable_code_convert) {
                        convertedCode = payload.code
                } else {
                        convertedCode = await convertPgCode((payload.prototype && payload.prototype.name) || 'App', payload.code || '')
                }
                // console.log(`convertedCode`)
                // console.log(convertedCode)
                io.to(kit.socket_id).emit('messageToKit', {
                    request_from: socket.id,
                    ...payload,
                    convertedCode: convertedCode
                })
            } else {
                io.to(kit.socket_id).emit('messageToKit', {
                    request_from: socket.id,
                    ...payload
                })
            }
        }
    })
    socket.on('messageToKit-kitReply', (payload) => {
        if(!payload || !payload.request_from) return;
        io.to(payload.request_from).emit('messageToKit-kitReply', payload)
    })

    // ------------ MESSAGE FROM KIT TO CLIENT ----------------
    socket.on('broadcastToClient', (payload) => {
        if(!payload || !payload.cmd || payload.kit_id) return;
        let kit = KITS.get(payload.kit_id)
        if(kit && kit.socket_id == socket.id) {
            io.to(payload.kit_id).emit('broadcastToClient', payload) 
        }
    })

    // ------------ MESSAGE FROM CLIENT TO KIT ----------------
    socket.on('messageToSyncerHw', (payload) => {
        if(!payload || !payload.cmd || !payload.to_kit_id) return;
        if(payload.cmd == 'syncer_set') {
            let kit = SYNCER_HW.get(payload.to_kit_id)
            if(kit) {
                io.to(kit.socket_id).emit('messageToSyncerHw', {
                    request_from: socket.id,
                    ...payload
                })
            }
        }
    })
    socket.on('messageToSyncerHw-kitReply', (payload) => {
        if(!payload || !payload.request_from) return;
        io.to(payload.request_from).emit('messageToKit-kitReply', payload)
    })

    // Native tree structure file writer
    async function writeTreeStructure(items, baseDir, socket) {
        for (const item of items) {
            if (item.type === 'file' && item.content !== undefined) {
                const filePath = path.join(baseDir, item.name);
                const fileDir = path.dirname(filePath);
                await fs.promises.mkdir(fileDir, { recursive: true });
                await fs.promises.writeFile(filePath, item.content, 'utf8');
                
                await socket.emit("compile_cpp_reply", {
                    "status": "file-written",
                    "result": `Written file: ${item.name}\r\n`,
                    "cmd": "compile_cpp",
                    "data": "",
                    "isDone": false,
                    "code": 0
                });
            } else if (item.type === 'folder' && item.items) {
                const folderPath = path.join(baseDir, item.name);
                await fs.promises.mkdir(folderPath, { recursive: true });
                await writeTreeStructure(item.items, folderPath, socket);
            }
        }
    }

    // ============ C++ COMPILATION SERVICE ============
    socket.on('compile_cpp', async (data) => {
        // Only support tree structure format
        if(!data.files || !Array.isArray(data.files) || !data["app_name"]) {
            socket.emit('compile_cpp_reply', {
                "status": "err: invalid",
                "result": "Invalid request. Only tree structure format supported. Expected files as array with type/name/content objects.\r\n",
                "cmd": "compile_cpp",
                "data": "",
                "isDone": true,
                "code": 1
            })
            return
        }

        // Validate tree structure has files
        function hasFiles(items) {
            return items.some(item => 
                item.type === 'file' || 
                (item.type === 'folder' && item.items && hasFiles(item.items))
            );
        }

        if(!hasFiles(data.files)) {
            socket.emit('compile_cpp_reply', {
                "status": "err: invalid", 
                "result": "No valid files found in tree structure\r\n",
                "cmd": "compile_cpp",
                "data": "",
                "isDone": true,
                "code": 1
            })
            return
        }

        socket.emit("compile_cpp_reply", {
            "status": "compile-start",
            "result": "Start to compile C++ app...\r\n",
            "cmd": "compile_cpp",
            "data": "",
            "isDone": false,
            "code": 0
        })

        let app_name = "app_" + socket.id
        let app_dir = `/home/dev/data/ws/${app_name}`

        try {
            await createMinimalSdkTemplate(app_dir)
        } catch(err){
            await socket.emit("compile_cpp_reply", {
                "status": "err-copy-folder",
                "result": err.toString(),
                "cmd": "compile_cpp",
                "data": "",
                "isDone": true,
                "code": 1
            })
            return
        }

        // Write C++ files using native tree structure
        try {
            try {
                if (fs.promises.rm) {
                    await fs.promises.rm(`${app_dir}/app/src`, { recursive: true, force: true });
                } else {
                    const rm = spawn('rm', ['-rf', `${app_dir}/app/src`]);
                    await new Promise((resolve, reject) => {
                        rm.on('close', (code) => code === 0 ? resolve() : reject(new Error(`rm failed with code ${code}`)));
                        rm.on('error', reject);
                    });
                }
            } catch (error) {
                console.log("Warning: Could not clear existing source files:", error.message);
            }
            await fs.promises.mkdir(`${app_dir}/app/src`, { recursive: true });

            // Write files directly from tree structure
            await writeTreeStructure(data.files, `${app_dir}/app/src`, socket);

            const cmakeContent = `set(TARGET_NAME "app")

file(GLOB_RECURSE CPP_SOURCES "*.cpp")

add_executable(\${TARGET_NAME}
    \${CPP_SOURCES}
)

target_include_directories(\${TARGET_NAME} PRIVATE
    \${CMAKE_CURRENT_SOURCE_DIR}
    \${CMAKE_CURRENT_SOURCE_DIR}/include
    \${CMAKE_CURRENT_SOURCE_DIR}/../include
)

file(GLOB_RECURSE HEADER_FILES "*.h" "*.hpp")
foreach(HEADER_FILE \${HEADER_FILES})
    get_filename_component(HEADER_DIR \${HEADER_FILE} DIRECTORY)
    target_include_directories(\${TARGET_NAME} PRIVATE \${HEADER_DIR})
endforeach()

target_link_libraries(\${TARGET_NAME}
    Threads::Threads
)`;
            
            await fs.promises.writeFile(`${app_dir}/app/src/CMakeLists.txt`, cmakeContent, 'utf8');

        } catch(err) {
            await socket.emit("compile_cpp_reply", {
                "status": "err_write_files",
                "result": err.toString(),
                "cmd": "compile_cpp",
                "data": "",
                "isDone": true,
                "code": 1
            })
            return
        }

        // Build with CMake
        try {
            await fs.promises.mkdir(`${app_dir}/build`, { recursive: true });
            const pConfigure = spawn('cmake', ['..'], { cwd: `${app_dir}/build` });

            pConfigure.stdout.on('data', async (data) => {
                await socket.emit("compile_cpp_reply", {
                    "status": "configure-stdout",
                    "cmd": "compile_cpp",
                    "data": "",
                    "isDone": false,
                    "result": `${data}`,
                    "code": 0
                })
            });

            pConfigure.stderr.on('data', async (data) => {
                await socket.emit("compile_cpp_reply", {
                    "status": "configure-stderr",
                    "cmd": "compile_cpp",
                    "data": "",
                    "isDone": false,
                    "result": `${data}`,
                    "code": 0
                })
            });

            pConfigure.on('close', async (code) => {
                if (code !== 0) {
                    await socket.emit("compile_cpp_reply", {
                        "status": "configure-failed",
                        "cmd": "compile_cpp",
                        "data": "",
                        "isDone": true,
                        "result": `CMake configuration failed with code ${code}\r\n`,
                        "code": code
                    })
                    return;
                }

                const pBuild = spawn('make', [], { cwd: `${app_dir}/build` });

                pBuild.stdout.on('data', async (data) => {
                    await socket.emit("compile_cpp_reply", {
                        "status": "build-stdout",
                        "cmd": "compile_cpp",
                        "data": "",
                        "isDone": false,
                        "result": `${data}`,
                        "code": 0
                    })
                });

                pBuild.stderr.on('data', async (data) => {
                    await socket.emit("compile_cpp_reply", {
                        "status": "build-stderr",
                        "cmd": "compile_cpp",
                        "data": "",
                        "isDone": false,
                        "result": `${data}`,
                        "code": 0
                    })
                });

                pBuild.on('close', async (code) => {
                    const willRun = data["run"] === true && code === 0;
                    
                    await socket.emit("compile_cpp_reply", {
                        "status": "build-done",
                        "cmd": "compile_cpp",
                        "data": "",
                        "isDone": !willRun,
                        "result": `Build completed with code ${code}\r\n`,
                        "code": code
                    })

                    if (code === 0) {
                        let executablePath = `${app_dir}/build/app/src/app`;
                        let outputPath = `/home/dev/data/output/${app_name}`;
                        
                        try {
                            await fs.promises.mkdir(path.dirname(outputPath), { recursive: true });
                            await fs.promises.copyFile(executablePath, outputPath);
                            await fs.promises.chmod(outputPath, 0o755);
                        } catch(err) {
                            console.log("Error copying executable:", err);
                        }

                        if(data["run"] === true) {
                            try {
                                const absoluteExecPath = path.resolve(executablePath);
                                const pRun = spawn(absoluteExecPath, [], {
                                    cwd: path.dirname(absoluteExecPath)
                                });
                                
                                pRun.stdout.on('data', async (data) => {
                                    await socket.emit("compile_cpp_reply", {
                                        "status": "run-stdout",
                                        "cmd": "compile_cpp",
                                        "data": "",
                                        "isDone": false,
                                        "result": `${data}`,
                                        "code": 0
                                    })
                                });
                        
                                pRun.stderr.on('data', async (data) => {
                                    await socket.emit("compile_cpp_reply", {
                                        "status": "run-stderr",
                                        "cmd": "compile_cpp",
                                        "data": "",
                                        "isDone": false,
                                        "result": `${data}`,
                                        "code": 0
                                    })
                                });

                                pRun.on('close', async (code) => {
                                    await socket.emit("compile_cpp_reply", {
                                        "status": "run-done",
                                        "cmd": "compile_cpp",
                                        "data": "",
                                        "isDone": true,
                                        "result": `App exit code ${code}\r\n`,
                                        "code": code
                                    })
                                })
                            } catch(err) {
                                console.log("Error running executable:", err);
                            }
                        }
                    }
                });
            });

        } catch(err) {
            await socket.emit("compile_cpp_reply", {
                "status": "err_build",
                "result": err.toString(),
                "cmd": "compile_cpp",
                "data": "",
                "isDone": true,
                "code": 1
            })
        }
    })

});

server.listen(config.port, () => {
    console.log(`SDV Runtime Kit Manager with C++ Compilation listening on port ${config.port}`);
    console.log(`Available compilation endpoints: compile_cpp`);
});