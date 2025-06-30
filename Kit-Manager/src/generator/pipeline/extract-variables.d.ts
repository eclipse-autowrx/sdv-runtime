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
 * Extracts variables from digital.auto prototype to the CodeContext
 * @extends PipelineStep
 */
export declare class ExtractVariablesStep extends PipelineStep {
    execute(context: CodeContext): void;
    private identifyVariables;
    private identifyVariableNames;
    private prepareMemberVariables;
}
