// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExtractClassesStep = void 0;
const codeConstants_1 = require("../utils/codeConstants");
const regex_1 = require("../utils/regex");
const helpers_1 = require("../utils/helpers");
const pipeline_base_1 = require("./pipeline-base");
/**
 * Extracts classes from digital.auto prototype to the CodeContext
 * @extends PipelineStep
 */
class ExtractClassesStep extends pipeline_base_1.PipelineStep {
    execute(context) {
        context.seperateClassesArray = this.identifySeperateClass(context);
        if (context.seperateClassesArray.length !== 0) {
            context.seperateClasses = this.adaptCodeBlocksToVelocitasStructure((0, helpers_1.createMultilineStringFromArray)(context.seperateClassesArray));
        }
        this.cleanUpCodeSnippet(context.seperateClassesArray, context);
    }
    identifySeperateClass(context) {
        const classStartIndexArray = [];
        context.codeSnippetStringArray.forEach((stringElement) => {
            var _a;
            if (stringElement.includes(codeConstants_1.PYTHON.CLASS)) {
                const classStartIndex = (_a = context.codeSnippetStringArray) === null || _a === void 0 ? void 0 : _a.indexOf(stringElement);
                classStartIndexArray.push(classStartIndex);
            }
        });
        const classArray = [];
        classStartIndexArray.forEach((classStartIndexElement) => {
            const tempClasses = [];
            for (let index = classStartIndexElement; this.lineBelongsToClass(context.codeSnippetStringArray, index); index++) {
                tempClasses.push(context.codeSnippetStringArray[index]);
            }
            classArray.push(tempClasses);
        });
        return classArray;
    }
    lineBelongsToClass(array, index) {
        const lineWithoutIndentation = array[index].replace(regex_1.REGEX.FIND_LINE_BEGINNING_WITH_WHITESPACES, '');
        if (array[index] !== '' && !array[index].includes(codeConstants_1.PYTHON.CLASS) && array[index].length === lineWithoutIndentation.length) {
            return false;
        }
        return true;
    }
}
exports.ExtractClassesStep = ExtractClassesStep;
