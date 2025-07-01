// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExtractMethodsStep = void 0;
const codeConstants_1 = require("../utils/codeConstants");
const helpers_1 = require("../utils/helpers");
const pipeline_base_1 = require("./pipeline-base");
/**
 * Extracts methods from digital.auto prototype to the CodeContext
 * @extends PipelineStep
 */
class ExtractMethodsStep extends pipeline_base_1.PipelineStep {
    execute(context) {
        context.seperateMethodsArray = this.identifyMethodBlocks(context);
        if (context.seperateMethodsArray.length !== 0) {
            context.seperateMethods = (0, helpers_1.createMultilineStringFromArray)(context.seperateMethodsArray);
            context.seperateMethods = this.adaptCodeBlocksToVelocitasStructure(context.seperateMethods);
            context.seperateMethods = (0, helpers_1.indentCodeSnippet)(context.seperateMethods, codeConstants_1.INDENTATION.COUNT_CLASS);
        }
    }
    identifyMethodBlocks(context) {
        const methodStartIndexArray = [];
        context.codeSnippetStringArray.forEach((stringElement) => {
            var _a;
            if (stringElement.includes(codeConstants_1.PYTHON.SYNC_METHOD_START)) {
                const methodStartIndex = (_a = context.codeSnippetStringArray) === null || _a === void 0 ? void 0 : _a.indexOf(stringElement);
                methodStartIndexArray.push(methodStartIndex);
            }
        });
        const methodArray = [];
        const modifiedMethodArray = [];
        methodStartIndexArray.forEach((methodStartIndex) => {
            const tempMethods = [];
            const tempModifiedMethods = [];
            for (let index = methodStartIndex; /\S/.test(context.codeSnippetStringArray[index]); index++) {
                tempMethods.push(context.codeSnippetStringArray[index]);
                if (context.codeSnippetStringArray[index].includes(codeConstants_1.PYTHON.SYNC_METHOD_START)) {
                    let methodLine;
                    if (context.codeSnippetStringArray[index].startsWith(codeConstants_1.PYTHON.ASYNC_METHOD_START)) {
                        methodLine = context.codeSnippetStringArray[index].replace(/\(.*\)/, codeConstants_1.VELOCITAS.CLASS_METHOD_SIGNATURE);
                    }
                    else {
                        methodLine = context.codeSnippetStringArray[index]
                            .replace(codeConstants_1.PYTHON.SYNC_METHOD_START, codeConstants_1.PYTHON.ASYNC_METHOD_START)
                            .replace(/\(.*\)/, codeConstants_1.VELOCITAS.CLASS_METHOD_SIGNATURE);
                    }
                    const subscriptionCallbackVariableLine = this.mapSubscriptionCallbackForVelocitas(context.codeSnippetStringArray, index);
                    tempModifiedMethods.push(methodLine);
                    tempModifiedMethods.push(subscriptionCallbackVariableLine);
                }
                else {
                    tempModifiedMethods.push(this.changeMemberVariablesInString(context.codeSnippetStringArray[index], context));
                }
            }
            methodArray.push(tempMethods);
            modifiedMethodArray.push(tempModifiedMethods);
        });
        this.cleanUpCodeSnippet(methodArray, context);
        return modifiedMethodArray;
    }
    mapSubscriptionCallbackForVelocitas(codeSnippetStringArray, index) {
        var _a, _b;
        const methodString = codeSnippetStringArray[index];
        let methodName;
        let vssSignal;
        methodName = (_a = codeSnippetStringArray === null || codeSnippetStringArray === void 0 ? void 0 : codeSnippetStringArray.find((line) => line.includes(methodString))) === null || _a === void 0 ? void 0 : _a.split(codeConstants_1.PYTHON.SYNC_METHOD_START)[1].trim().split(`(`)[0];
        vssSignal = (_b = codeSnippetStringArray === null || codeSnippetStringArray === void 0 ? void 0 : codeSnippetStringArray.find((line) => line.includes(`${codeConstants_1.DIGITAL_AUTO.SUBSCRIBE_CALL}${methodName}`))) === null || _b === void 0 ? void 0 : _b.split(`${codeConstants_1.DIGITAL_AUTO.SUBSCRIBE_CALL}`)[0];
        if (vssSignal === null || vssSignal === void 0 ? void 0 : vssSignal.startsWith(`${codeConstants_1.PYTHON.AWAIT} `)) {
            vssSignal = vssSignal.split(`${codeConstants_1.PYTHON.AWAIT} `)[1];
        }
        const callBackVariable = methodString.split(`(`)[1].split(`:`)[0].split(`)`)[0];
        const subscriptionCallbackVariableLine = (0, helpers_1.indentCodeSnippet)(`${callBackVariable} = data.get(${vssSignal}).value`, codeConstants_1.INDENTATION.COUNT_CLASS);
        return subscriptionCallbackVariableLine;
    }
    changeMemberVariablesInString(codeSnippet, context) {
        var _a;
        (_a = context.variableNames) === null || _a === void 0 ? void 0 : _a.forEach((variableName) => {
            if (codeSnippet.includes(`${variableName}`) &&
                (!codeSnippet.includes(`.${variableName}`) ||
                    !codeSnippet.includes(`${variableName}"`) ||
                    !codeSnippet.includes(`"${variableName}`))) {
                const re = new RegExp(`(?<![\\.\\"])${variableName}(?![\\.\\"])`, 'g');
                codeSnippet = codeSnippet.replace(re, `self.${variableName}`);
            }
        });
        return codeSnippet;
    }
}
exports.ExtractMethodsStep = ExtractMethodsStep;
