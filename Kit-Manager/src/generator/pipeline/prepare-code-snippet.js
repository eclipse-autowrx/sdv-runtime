// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PrepareCodeSnippetStep = void 0;
const codeConstants_1 = require("../utils/codeConstants");
const pipeline_base_1 = require("./pipeline-base");
/**
 * Prepares digital.auto prototype code snippet to be used to extract all relevant and needed information.
 * @extends PipelineStep
 */
class PrepareCodeSnippetStep extends pipeline_base_1.PipelineStep {
    execute(context) {
        context.codeSnippetStringArray = this.removeSubstringsFromArray(context.codeSnippetStringArray, codeConstants_1.DIGITAL_AUTO.VEHICLE_INIT);
        context.codeSnippetStringArray = this.removeSubstringsFromArray(context.codeSnippetStringArray, codeConstants_1.PYTHON.IMPORT_DEPENDENCY_FROM, codeConstants_1.PYTHON.IMPORT);
        context.codeSnippetStringArray = this.removeSubstringsFromArray(context.codeSnippetStringArray, codeConstants_1.PYTHON.COMMENT);
    }
    removeSubstringsFromArray(array, substringOne, substringTwo) {
        const indexesToRemove = [];
        array.forEach((stringElement) => {
            if (!substringTwo && stringElement.includes(substringOne)) {
                const indexToRemove = array.indexOf(stringElement);
                indexesToRemove.push(indexToRemove);
            }
            if (substringTwo && stringElement.includes(substringOne) && stringElement.includes(substringTwo)) {
                const indexToRemove = array.indexOf(stringElement);
                indexesToRemove.push(indexToRemove);
            }
        });
        for (let index = 0; index < indexesToRemove.length; index++) {
            if (index === 0) {
                array.splice(indexesToRemove[index], 1);
            }
            else {
                array.splice(indexesToRemove[index] - index, 1);
            }
        }
        return array;
    }
}
exports.PrepareCodeSnippetStep = PrepareCodeSnippetStep;
