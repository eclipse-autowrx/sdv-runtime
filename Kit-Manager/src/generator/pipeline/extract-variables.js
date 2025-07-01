// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExtractVariablesStep = void 0;
const codeConstants_1 = require("../utils/codeConstants");
const helpers_1 = require("../utils/helpers");
const pipeline_base_1 = require("./pipeline-base");
/**
 * Extracts variables from digital.auto prototype to the CodeContext
 * @extends PipelineStep
 */
class ExtractVariablesStep extends pipeline_base_1.PipelineStep {
    execute(context) {
        var _a;
        context.variablesArray = this.identifyVariables(context.codeSnippetStringArray);
        context.variableNames = this.identifyVariableNames(context.variablesArray);
        if (((_a = context.variableNames) === null || _a === void 0 ? void 0 : _a.length) != 0) {
            context.memberVariables = this.prepareMemberVariables(context);
        }
    }
    identifyVariables(codeSnippetStringArray) {
        const variablesArray = [];
        codeSnippetStringArray.forEach((stringElement) => {
            if (!stringElement.includes('plugins')) {
                const tempVariables = [];
                if (stringElement.includes('= {')) {
                    for (let index = codeSnippetStringArray.indexOf(stringElement); codeSnippetStringArray[index] !== '' && !codeSnippetStringArray[index].includes('}}'); index++) {
                        tempVariables.push(codeSnippetStringArray[index]);
                    }
                    variablesArray.push(tempVariables);
                }
                if (stringElement.includes(' = ') && !stringElement.includes('= {')) {
                    variablesArray.push([stringElement]);
                }
            }
        });
        return variablesArray;
    }
    identifyVariableNames(variablesArray) {
        let variableNames = [];
        variablesArray.forEach((variableArray) => {
            variableArray.forEach((variable) => {
                if (variable.includes('=')) {
                    if (variable.includes(',')) {
                        variable.split(',').forEach((singleVariable) => {
                            variableNames.push(singleVariable.split('=')[0].trim());
                        });
                    }
                    else {
                        variableNames.push(variable.split('=')[0].trim());
                    }
                }
            });
        });
        variableNames = Array.from(new Set(variableNames));
        // console.log('variableNames')
        // console.log(variableNames)
        return variableNames;
    }
    prepareMemberVariables(context) {
        const memberVariablesArray = [];
        context.variableNames.forEach((variable) => {
            memberVariablesArray.push(`self.${variable.trim()} = None`);
        });
        const memberVariables = (0, helpers_1.indentCodeSnippet)((0, helpers_1.createMultilineStringFromArray)(memberVariablesArray), codeConstants_1.INDENTATION.COUNT_METHOD);
        return memberVariables;
    }
}
exports.ExtractVariablesStep = ExtractVariablesStep;
