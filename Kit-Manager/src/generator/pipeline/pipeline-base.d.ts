// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the Apache License, Version 2.0 which is available at
// https://www.apache.org/licenses/LICENSE-2.0.
//
// SPDX-License-Identifier: Apache-2.0

import { CodeContext } from '../code-converter';
export interface IPipelineStep {
    execute(context: CodeContext): void;
    cleanUpCodeSnippet(arrayToCleanUp: string[] | string[][], codeContext: CodeContext): void;
}
/**
 * Base class for pipeline use case in code converter.
 * To be used to extend the functionality for more detailed pipeline steps.
 */
export declare class PipelineStep implements IPipelineStep {
    /**
     * @param {CodeContext} context
     */
    execute(context: CodeContext): void;
    cleanUpCodeSnippet(arrayToCleanUp: string[] | string[][], codeContext: CodeContext): void;
    adaptCodeBlocksToVelocitasStructure(codeBlock: string): string;
}
