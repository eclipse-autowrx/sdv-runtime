// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.encode = exports.decode = exports.delay = exports.insertClassDocString = exports.removeEmptyLines = exports.createMultilineStringFromArray = exports.createArrayFromMultilineString = exports.indentCodeSnippet = void 0;
const codeConstants_1 = require("./codeConstants");
const constants_1 = require("./constants");
const regex_1 = require("./regex");
const buffer_1 = require("buffer");
const indentCodeSnippet = (decodedSnippet, indentCount) => {
    const indent = ' ';
    const indentedCodeSnippet = decodedSnippet.replace(regex_1.REGEX.FIND_EVERY_LINE_START, indent.repeat(indentCount));
    return indentedCodeSnippet;
};
exports.indentCodeSnippet = indentCodeSnippet;
const createArrayFromMultilineString = (multilineString) => {
    return multilineString.split(/\r?\n/);
};
exports.createArrayFromMultilineString = createArrayFromMultilineString;
const createMultilineStringFromArray = (array) => {
    let multilineString = '';
    if (array[0].constructor === Array) {
        array.forEach((stringArray) => {
            stringArray.forEach((stringElement) => {
                multilineString = multilineString.concat(`${stringElement}\n`);
            });
            multilineString = multilineString.concat(`\n`);
        });
    }
    else {
        array.forEach((stringElement) => {
            multilineString = multilineString.concat(`${stringElement}\n`);
        });
    }
    return multilineString.trim();
};
exports.createMultilineStringFromArray = createMultilineStringFromArray;
const removeEmptyLines = (array) => {
    const indexesToRemove = new Set();
    array.forEach((e, index) => {
        if (e === '' && array[index + 1] === '') {
            if (!array[index + 2].includes(codeConstants_1.PYTHON.CLASS) &&
                !array[index + 2].includes(codeConstants_1.VELOCITAS.EVENT_LOOP) &&
                !array[index + 2].includes(codeConstants_1.VELOCITAS.NEW_EVENT_LOOP) &&
                !array[index + 2].includes(codeConstants_1.VELOCITAS.MAIN_METHOD)) {
                indexesToRemove.add(index);
            }
        }
        if (e === codeConstants_1.VELOCITAS.MAIN_METHOD && array[index + 1] === '') {
            indexesToRemove.add(index + 1);
        }
    });
    const arrayWithoutEmtpyLines = array.filter((_element, index) => !indexesToRemove.has(index));
    const indexOfOnStart = arrayWithoutEmtpyLines.indexOf(`${' '.repeat(4)}${codeConstants_1.VELOCITAS.ON_START}`);
    if (arrayWithoutEmtpyLines[indexOfOnStart + 1] === '') {
        arrayWithoutEmtpyLines.splice(indexOfOnStart + 1, 1);
    }
    return arrayWithoutEmtpyLines;
};
exports.removeEmptyLines = removeEmptyLines;
const insertClassDocString = (array, appName) => {
    const vehicleAppClassLine = array.find((line) => line.includes(codeConstants_1.VELOCITAS.VEHICLE_APP_SIGNATURE));
    array.splice(array.indexOf(vehicleAppClassLine) + 1, 0, (0, exports.indentCodeSnippet)(`"""Velocitas App for ${appName}."""`, codeConstants_1.INDENTATION.COUNT_CLASS));
};
exports.insertClassDocString = insertClassDocString;
const delay = (ms) => {
    return new Promise((resolve) => setTimeout(resolve, ms));
};
exports.delay = delay;
const decode = (string) => buffer_1.Buffer.from(string, constants_1.CONTENT_ENCODINGS.base64).toString(constants_1.CONTENT_ENCODINGS.utf8);
exports.decode = decode;
const encode = (string) => buffer_1.Buffer.from(string, constants_1.CONTENT_ENCODINGS.utf8).toString(constants_1.CONTENT_ENCODINGS.base64);
exports.encode = encode;
