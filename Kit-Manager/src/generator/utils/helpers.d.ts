// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the Apache License, Version 2.0 which is available at
// https://www.apache.org/licenses/LICENSE-2.0.
//
// SPDX-License-Identifier: Apache-2.0

export declare const indentCodeSnippet: (decodedSnippet: string, indentCount: number) => string;
export declare const createArrayFromMultilineString: (multilineString: string) => string[];
export declare const createMultilineStringFromArray: (array: string[] | string[][]) => string;
export declare const removeEmptyLines: (array: string[]) => string[];
export declare const insertClassDocString: (array: string[], appName: string) => void;
export declare const delay: (ms: number) => Promise<unknown>;
export declare const decode: (string: string) => string;
export declare const encode: (string: string) => string;
export interface DataPointDefinition {
    path: string;
    required: string;
    access: string;
}
export interface VehicleModel {
    src: string;
    datapoints: DataPointDefinition[];
}
export interface AppManifest {
    name: string;
    vehicleModel: VehicleModel;
    runtime: string[];
}
