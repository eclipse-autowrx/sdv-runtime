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
 * Extracts classes from digital.auto prototype to the CodeContext
 * @extends PipelineStep
 */
export declare class ExtractClassesStep extends PipelineStep {
    execute(context: CodeContext): void;
    private identifySeperateClass;
    private lineBelongsToClass;
}
