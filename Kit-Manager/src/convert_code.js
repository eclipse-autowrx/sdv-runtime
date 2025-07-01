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

const convertPgCode = async (appName, code, vss_payload) => {
    try {
        // console.log(`appName`)
        // console.log(appName)
        // console.log(code)
        const finalAppName = appName.replace(/[^a-zA-Z0-9]/gi, '')
        const generator = new ProjectGenerator("", (finalAppName), "")
        
        const payload = encodeToBase64(JSON.stringify(vss_payload || {}))
        try {
            const convertedCode = await generator.runWithPayload(encodeToBase64(code), finalAppName, payload)
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
            console.log("error on converted code")
            console.log(err)
        }
        return null
        
    } catch (error) {
        console.log("error on generateCode", error)
        throw error;
    }
}

module.exports = convertPgCode;