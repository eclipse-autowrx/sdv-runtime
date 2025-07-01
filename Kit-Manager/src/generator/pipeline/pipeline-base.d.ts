// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

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
