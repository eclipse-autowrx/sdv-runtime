// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

Object.defineProperty(exports, "__esModule", { value: true });
exports.CodeConverter = exports.CodeContext = void 0;
const create_code_snippet_1 = require("./pipeline/create-code-snippet");
const extract_classes_1 = require("./pipeline/extract-classes");
const extract_imports_1 = require("./pipeline/extract-imports");
const extract_methods_1 = require("./pipeline/extract-methods");
const extract_variables_1 = require("./pipeline/extract-variables");
const prepare_code_snippet_1 = require("./pipeline/prepare-code-snippet");
const codeConstants_1 = require("./utils/codeConstants");
const regex_1 = require("./utils/regex");
const helpers_1 = require("./utils/helpers");
const fs = require('fs')

class CodeContext {
    constructor() {
        this.appName = '';
        this.basicImportsArray = [];
        this.variablesArray = [];
        this.variableNames = [];
        this.memberVariables = '';
        this.seperateClassesArray = [];
        this.seperateClasses = '';
        this.seperateMethodsArray = [];
        this.seperateMethods = '';
        this.codeSnippetStringArray = [];
        this.codeSnippetForTemplate = '';
    }
}
exports.CodeContext = CodeContext;
/**
 * Initialize a new `CodeConverter`.
 *
 * @return {CodeConverter} which is used to convert digital.auto prototype to a functioning velocitas structure.
 * @public
 */
class CodeConverter {
    constructor() {
        this.codeContext = new CodeContext();
    }
    /**
     * Converts main.py from digital.auto to velocitas structure.
     * @param {string} mainPyContentData
     * @param {string} codeSnippet
     * @param {string} appName
     * @return {CodeConversionResult} Result of code conversion.
     * @public
     */
    convertMainPy(mainPyContentData, codeSnippet, appName) {
        try {
            this.codeContext.appName = appName;
            this.adaptCodeSnippet(codeSnippet);
            const extractedMainPyStructure = this.extractMainPyBaseStructure(mainPyContentData);
            // console.log(`extractedMainPyStructure`, extractedMainPyStructure)
            const convertedMainPy = this.addCodeSnippetToMainPy(extractedMainPyStructure);
            // console.log(`convertedMainPy`, convertedMainPy)
            const finalizedMainPy = this.finalizeMainPy(convertedMainPy);
            // console.log(`finalizedMainPy`, finalizedMainPy)
            const dataPoints = this.identifyDatapoints(finalizedMainPy);
            return { finalizedMainPy: finalizedMainPy, dataPoints: dataPoints };
        }
        catch (error) {
            throw error;
        }
    }
    adaptCodeSnippet(codeSnippet) {
        this.codeContext.codeSnippetStringArray = (0, helpers_1.createArrayFromMultilineString)(codeSnippet);
        const pipeline = new Array();
        pipeline.push(new prepare_code_snippet_1.PrepareCodeSnippetStep());
        pipeline.push(new extract_imports_1.ExtractImportsStep());
        pipeline.push(new extract_variables_1.ExtractVariablesStep());
        pipeline.push(new extract_classes_1.ExtractClassesStep());
        pipeline.push(new extract_methods_1.ExtractMethodsStep());
        pipeline.push(new create_code_snippet_1.CreateCodeSnippetForTemplateStep());
        pipeline.forEach((pipelineStep) => pipelineStep.execute(this.codeContext));
    }
    extractMainPyBaseStructure(mainPyContentData) {
        try {
            let tempContent;
            tempContent = (0, helpers_1.createArrayFromMultilineString)(mainPyContentData);
            tempContent = tempContent.filter((line) => !line.includes(` ${codeConstants_1.PYTHON.COMMENT} `) || line.includes(codeConstants_1.VELOCITAS.TYPE_IGNORE));
            tempContent = tempContent.filter((line) => !line.includes(codeConstants_1.VELOCITAS.PREDEFINED_TOPIC));
            const classesArray = (0, helpers_1.createArrayFromMultilineString)(this.codeContext.seperateClasses);
            const velocitasClassStartIndex = tempContent.indexOf('class SampleApp(VehicleApp):');
            if (classesArray.length > 0) {
                tempContent.splice(velocitasClassStartIndex - 1, 0, ...classesArray);
            }
            const velocitasOnStartIndex = tempContent.indexOf(`    ${codeConstants_1.VELOCITAS.ON_START}`);
            const topPartOfTemplate = tempContent.slice(0, velocitasOnStartIndex + 1);
            const velocitasMainIndex = tempContent.indexOf(codeConstants_1.VELOCITAS.MAIN_METHOD);
            const bottomPartOfTemplate = tempContent.slice(velocitasMainIndex - 1, tempContent.length);
            const methodsArray = (0, helpers_1.createArrayFromMultilineString)(this.codeContext.seperateMethods);
            if (methodsArray.length > 1) {
                methodsArray.unshift('');
                methodsArray.push('');
            }
            tempContent = topPartOfTemplate.concat(methodsArray).concat(bottomPartOfTemplate);
            tempContent = (0, helpers_1.createMultilineStringFromArray)(tempContent);
            const mainPyBaseStructure = tempContent.replace(regex_1.REGEX.EVERYTHING_BETWEEN_MULTILINE, '');
            return mainPyBaseStructure;
        }
        catch (error) {
            throw new Error('Error in extractMainPyBaseStructure.');
        }
    }
    addCodeSnippetToMainPy(extractedMainPyStructure) {
        const appNameForTemplate = `${this.codeContext.appName.charAt(0).toUpperCase()}${this.codeContext.appName.slice(1)}${codeConstants_1.VELOCITAS.VEHICLE_APP_SUFFIX}`;
        try {
            // fs.writeFile("extractedMainPyStructure.py", extractedMainPyStructure, () => {})
            // console.log("regex_1.REGEX.FIND_BEGIN_OF_ON_START_METHOD")
            // console.log(regex_1.REGEX.FIND_BEGIN_OF_ON_START_METHOD)
            // console.log('this.codeContext.codeSnippetForTemplate', this.codeContext.codeSnippetForTemplate)
            let newMainPy = extractedMainPyStructure.replace(regex_1.REGEX.FIND_BEGIN_OF_ON_START_METHOD, `${this.codeContext.codeSnippetForTemplate}\n`)
            // fs.writeFile("newMainPy1.py", newMainPy, () => {})
            newMainPy = newMainPy.replace(regex_1.REGEX.FIND_VEHICLE_INIT, `self.Vehicle = vehicle_client\n${this.codeContext.memberVariables}`)
            // fs.writeFile("newMainPy2.py", newMainPy, () => {})
            newMainPy = newMainPy.replace(codeConstants_1.VELOCITAS.IMPORT_SUBSCRIBE_TOPIC, '')
            // fs.writeFile("newMainPy3.py", newMainPy, () => {})
            newMainPy = newMainPy.replace(regex_1.REGEX.FIND_SAMPLE_APP, appNameForTemplate);
            // make sure no repeate appear
            newMainPy = newMainPy.split("self.self.").join("self.")
            newMainPy = newMainPy.split("await await ").join("await ")
            // fs.writeFile("newMainPy4.py", newMainPy, () => {})
            return newMainPy;
        }
        catch (error) {
            throw new Error('Error in addCodeSnippetToMainPy.');
        }
    }
    finalizeMainPy(newMainPy) {
        var _a;
        let finalCode = (0, helpers_1.createArrayFromMultilineString)(newMainPy);
        this.adaptToMqtt(finalCode);
        const firstLineOfImport = finalCode.find((element) => element.includes(codeConstants_1.PYTHON.IMPORT));
        finalCode.splice(finalCode.indexOf(firstLineOfImport), 0, '# flake8: noqa: E501,B950 line too long');
        (_a = this.codeContext.basicImportsArray) === null || _a === void 0 ? void 0 : _a.forEach((basicImportString) => {
            if (basicImportString != codeConstants_1.DIGITAL_AUTO.IMPORT_PLUGINS) {
                finalCode.splice(finalCode.indexOf(firstLineOfImport), 0, basicImportString);
            }
        });
        finalCode = (0, helpers_1.createMultilineStringFromArray)(finalCode);
        finalCode = finalCode
            .replace(regex_1.REGEX.FIND_SUBSCRIBE_METHOD_CALL, codeConstants_1.VELOCITAS.SUBSCRIPTION_SIGNATURE)
            .replace(/await await/gm, `${codeConstants_1.PYTHON.AWAIT}`)
            .replace(/\.get\(\)/gm, `${codeConstants_1.VELOCITAS.GET_VALUE}`)
            .replace(regex_1.REGEX.GET_EVERY_PLUGINS_USAGE, '')
            .replace(/await aio/gm, codeConstants_1.VELOCITAS.ASYNCIO);
        finalCode = (0, helpers_1.createArrayFromMultilineString)(finalCode);
        finalCode = (0, helpers_1.removeEmptyLines)(finalCode);
        finalCode.forEach((codeLine, index) => {
            if (codeLine.includes(codeConstants_1.VELOCITAS.GET_VALUE)) {
                finalCode[index] = codeLine.replace(/await/, '(await').replace(/{await/, '{(await');
            }
            if (codeLine.includes(codeConstants_1.VELOCITAS.INFO_LOGGER_SIGNATURE) && codeLine.includes('",')) {
                finalCode[index] = codeLine.replace('",', ': %s",');
            }
            if (codeLine.includes('.set(')) {
                const setArgument = codeLine.split('(')[1];
                if (setArgument.startsWith('self.Vehicle')) {
                    const vehicleClassEnumProperty = setArgument.split(')')[0];
                    const identifiedEnumString = vehicleClassEnumProperty.split('.').at(-1);
                    finalCode[index] = codeLine.replace(vehicleClassEnumProperty, `"${identifiedEnumString}"`);
                }
            }
        });
        if (!finalCode.some((line) => line.includes(codeConstants_1.VELOCITAS.CLASS_METHOD_SIGNATURE))) {
            finalCode.splice(finalCode.indexOf(codeConstants_1.VELOCITAS.IMPORT_DATAPOINT_REPLY), 1);
        }
        (0, helpers_1.insertClassDocString)(finalCode, this.codeContext.appName);
        const convertedFinalCode = (0, helpers_1.createMultilineStringFromArray)(finalCode);
        return convertedFinalCode;
    }
    adaptToMqtt(mainPyStringArray) {
        const setTextLines = mainPyStringArray.filter((line) => line.includes(codeConstants_1.DIGITAL_AUTO.NOTIFY) || line.includes(codeConstants_1.DIGITAL_AUTO.SET_TEXT));
        for (const setTextLine of setTextLines) {
            let mqttTopic;
            if (setTextLine.includes(codeConstants_1.DIGITAL_AUTO.NOTIFY)) {
                mqttTopic = setTextLine.split('.')[1].split('(')[0].trim();
            }
            else {
                mqttTopic = setTextLine.split('.')[0].trim();
            }
            const mqttMessage = setTextLine.split('"')[1].trim();
            const mqttPublishLine = this.transformToMqttPublish(mqttTopic, mqttMessage);
            const spacesBeforeSetTextLine = new RegExp(`\\s(?=[^,]*${mqttTopic})`, 'g');
            const spaceCountBeforeSetTextLine = setTextLine.length - setTextLine.replace(spacesBeforeSetTextLine, '').length;
            const newMqttPublishLine = (0, helpers_1.indentCodeSnippet)(mqttPublishLine, spaceCountBeforeSetTextLine);
            mainPyStringArray[mainPyStringArray.indexOf(setTextLine)] = newMqttPublishLine;
        }
        return mainPyStringArray;
    }
    transformToMqttPublish(mqttTopic, mqttMessage) {
        if (mqttMessage.includes('{')) {
            const variableInMqttMessage = this.codeContext.variableNames.find((variable) => mqttMessage.includes(variable));
            if (variableInMqttMessage) {
                mqttMessage = mqttMessage.replace(variableInMqttMessage, `self.${variableInMqttMessage}`);
            }
        }
        return this.generateMqttPublishString(mqttMessage, mqttTopic);
    }
    generateMqttPublishString(mqttMessage, mqttTopic) {
        const quoteType = mqttMessage.includes('{') ? `f"""` : `"""`;
        let jsonDumpsObject = `json.dumps({"result": {"message": ${quoteType}${mqttMessage}"""}}),\n)`;
        let mqttPublishString = `await self.publish_mqtt_event(\n${' '.repeat(4)}"${mqttTopic}",\n${' '.repeat(4)}${jsonDumpsObject}`;
        if (jsonDumpsObject.length > 88) {
            jsonDumpsObject = `json.dumps(\n${' '.repeat(8)}{\n${' '.repeat(12)}"result": {\n${' '.repeat(16)}"message": ${quoteType}${mqttMessage}"""\n${' '.repeat(12)}}\n${' '.repeat(8)}}\n${' '.repeat(4)}),\n)`;
            mqttPublishString = `await self.publish_mqtt_event(\n${' '.repeat(4)}"${mqttTopic}",\n${' '.repeat(4)}${jsonDumpsObject}`;
        }
        return mqttPublishString;
    }
    identifyDatapoints(finalizedMainPy) {
        const finalizedMainPyArray = (0, helpers_1.createArrayFromMultilineString)(finalizedMainPy);
        const dataPointsMap = new Map();
        const dataPoints = [];
        finalizedMainPyArray.forEach((line) => {
            if (line.includes('.Vehicle.')) {
                const captureAlternatives = '\\.subscribe|\\.get|\\.set|\\)';
                const dataPointRegExp = new RegExp(`Vehicle.*?(${captureAlternatives})`);
                const dataPointMatch = dataPointRegExp.exec(line);
                if (dataPointMatch) {
                    const dataPointPath = dataPointMatch[0].split(dataPointMatch[1])[0];
                    switch (dataPointMatch[1]) {
                        case '.set':
                            dataPointsMap.set(dataPointPath, 'write');
                            break;
                        default:
                            if (!dataPointsMap.has(dataPointPath)) {
                                dataPointsMap.set(dataPointPath, 'read');
                            }
                            break;
                    }
                }
            }
        });
        dataPointsMap.forEach((dataPointAccess, dataPointPath) => dataPoints.push({ path: dataPointPath, required: 'true', access: dataPointAccess }));
        return dataPoints;
    }
}
exports.CodeConverter = CodeConverter;
