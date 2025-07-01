// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

import { DataPointDefinition } from './utils/helpers';
export declare class CodeContext {
    appName: string;
    basicImportsArray: string[];
    variablesArray: string[][];
    variableNames: string[];
    memberVariables: string;
    seperateClassesArray: string[][];
    seperateClasses: string;
    seperateMethodsArray: string[][];
    seperateMethods: string;
    codeSnippetStringArray: string[];
    codeSnippetForTemplate: string;
}
/**
 * Result of code conversion containing finalizedMainPy as string and
 * an array of DataPointDefinition
 * @type CodeConversionResult
 * @prop {string} finalizedMainPy Finalized main.py.
 * @prop {DataPointDefinition[]} dataPoints Array of datapoints for AppManifest.json.
 */
export interface CodeConversionResult {
    finalizedMainPy: string;
    dataPoints: DataPointDefinition[];
}
/**
 * Initialize a new `CodeConverter`.
 *
 * @return {CodeConverter} which is used to convert digital.auto prototype to a functioning velocitas structure.
 * @public
 */
export declare class CodeConverter {
    private codeContext;
    /**
     * Converts main.py from digital.auto to velocitas structure.
     * @param {string} mainPyContentData
     * @param {string} codeSnippet
     * @param {string} appName
     * @return {CodeConversionResult} Result of code conversion.
     * @public
     */
    convertMainPy(mainPyContentData: string, codeSnippet: string, appName: string): CodeConversionResult;
    private adaptCodeSnippet;
    private extractMainPyBaseStructure;
    private addCodeSnippetToMainPy;
    private finalizeMainPy;
    private adaptToMqtt;
    private transformToMqttPublish;
    private generateMqttPublishString;
    private identifyDatapoints;
}
