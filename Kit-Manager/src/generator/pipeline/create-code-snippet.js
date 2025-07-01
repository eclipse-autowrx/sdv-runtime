// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CreateCodeSnippetForTemplateStep = void 0;
const codeConstants_1 = require("../utils/codeConstants");
const helpers_1 = require("../utils/helpers");
const pipeline_base_1 = require("./pipeline-base");
/**
 * Creates the code snippet which will be put into the velocitas template
 * @extends PipelineStep
 */
class CreateCodeSnippetForTemplateStep extends pipeline_base_1.PipelineStep {
    execute(context) {
        this.changeMemberVariables(context);
        context.codeSnippetForTemplate = `${(0, helpers_1.indentCodeSnippet)(codeConstants_1.VELOCITAS.ON_START, codeConstants_1.INDENTATION.COUNT_CLASS)}\n${(0, helpers_1.indentCodeSnippet)(this.adaptCodeBlocksToVelocitasStructure((0, helpers_1.createMultilineStringFromArray)(context.codeSnippetStringArray)), codeConstants_1.INDENTATION.COUNT_METHOD)}`;
    }
    changeMemberVariables(context) {
        context.variableNames.forEach((variableName) => {
            // console.log("context.codeSnippetStringArray")
            // console.log(context.codeSnippetStringArray)
            context.codeSnippetStringArray.forEach((stringElement, index) => {
                if (stringElement.includes(`${variableName} `) 
                || stringElement.includes(` ${variableName}`) 
                || stringElement.includes(`\t${variableName}`)
                || stringElement.includes(`(${variableName}`)
                ) {
                // if (stringElement.includes(`${variableName} =`) && !stringElement.includes(`self.`)) {
                    // console.log(`before\t`, context.codeSnippetStringArray[index])
                    let tmp = stringElement.split(variableName).join(`self.${variableName}`)
                    tmp = tmp.split("self.self.").join("self.")
                    context.codeSnippetStringArray[index] = tmp
                    // context.codeSnippetStringArray[index] = `self.${stringElement}`;
                    // console.log(`after\t`, context.codeSnippetStringArray[index])
                }

                // if (stringElement.includes(`${variableName} =`) && !stringElement.includes(`self.`)) {
                //     context.codeSnippetStringArray[index] = `self.${stringElement}`;
                // }
                if (stringElement.includes(`, ${variableName}`)) {
                    const re = new RegExp(`(?<!")${variableName}(?!")`, 'g');
                    context.codeSnippetStringArray[index] = stringElement.replace(re, `self.${variableName}`);
                }
                if (stringElement.includes(`${variableName} <=`) ||
                    stringElement.includes(`= ${variableName}`) ||
                    stringElement.includes(`${variableName} +`)) {
                    context.codeSnippetStringArray[index] = stringElement.replace(variableName, `self.${variableName}`);
                }
            });
        });
    }
}
exports.CreateCodeSnippetForTemplateStep = CreateCodeSnippetForTemplateStep;
