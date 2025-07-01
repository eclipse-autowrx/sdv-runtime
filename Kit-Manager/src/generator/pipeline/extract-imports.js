// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExtractImportsStep = void 0;
const codeConstants_1 = require("../utils/codeConstants");
const pipeline_base_1 = require("./pipeline-base");
/**
 * Extracts imports from digital.auto prototype to the CodeContext
 * @extends PipelineStep
 */
class ExtractImportsStep extends pipeline_base_1.PipelineStep {
    execute(context) {
        context.basicImportsArray = this.identifyBasicImports(context);
        this.cleanUpCodeSnippet(context.basicImportsArray, context);
    }
    identifyBasicImports(context) {
        let basicImportsArray = [];
        basicImportsArray = context.codeSnippetStringArray.filter((stringElement) => stringElement.includes(codeConstants_1.PYTHON.IMPORT));
        return basicImportsArray;
    }
}
exports.ExtractImportsStep = ExtractImportsStep;
