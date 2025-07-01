// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PipelineStep = void 0;
const codeConstants_1 = require("../utils/codeConstants");
const regex_1 = require("../utils/regex");
/**
 * Base class for pipeline use case in code converter.
 * To be used to extend the functionality for more detailed pipeline steps.
 */
class PipelineStep {
    /**
     * @param {CodeContext} context
     */
    execute(context) { }
    cleanUpCodeSnippet(arrayToCleanUp, codeContext) {
        if (arrayToCleanUp.length === 0) {
            return;
        }
        let linesToRemove = [];
        if (arrayToCleanUp[0].constructor === Array) {
            arrayToCleanUp.forEach((array) => {
                linesToRemove = [...linesToRemove, ...array];
            });
        }
        else {
            arrayToCleanUp.forEach((string) => {
                linesToRemove.push(string);
            });
        }
        linesToRemove.forEach((lineToRemove) => {
            var _a;
            if (codeContext.codeSnippetStringArray.indexOf(lineToRemove) >= 0) {
                (_a = codeContext.codeSnippetStringArray) === null || _a === void 0 ? void 0 : _a.splice(codeContext.codeSnippetStringArray.indexOf(lineToRemove), 1);
            }
        });
    }
    adaptCodeBlocksToVelocitasStructure(codeBlock) {
        return codeBlock
            .replace(regex_1.REGEX.FIND_VEHICLE_OCCURENCE, codeConstants_1.VELOCITAS.VEHICLE_CALL)
            .replace(regex_1.REGEX.FIND_UNWANTED_VEHICLE_CHANGE, codeConstants_1.VELOCITAS.VEHICLE_CALL_AS_ARGUMENT)
            .replace(regex_1.REGEX.FIND_PRINTF_STATEMENTS, codeConstants_1.VELOCITAS.INFO_LOGGER_SIGNATURE)
            .replace(regex_1.REGEX.FIND_PRINT_STATEMENTS, codeConstants_1.VELOCITAS.INFO_LOGGER_SIGNATURE);
    }
}
exports.PipelineStep = PipelineStep;
