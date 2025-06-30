// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the Apache License, Version 2.0 which is available at
// https://www.apache.org/licenses/LICENSE-2.0.
//
// SPDX-License-Identifier: Apache-2.0

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
