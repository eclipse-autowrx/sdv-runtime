// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

import { CodeContext } from '../code-converter';
import { PipelineStep } from './pipeline-base';
/**
 * Prepares digital.auto prototype code snippet to be used to extract all relevant and needed information.
 * @extends PipelineStep
 */
export declare class PrepareCodeSnippetStep extends PipelineStep {
    execute(context: CodeContext): void;
    private removeSubstringsFromArray;
}
