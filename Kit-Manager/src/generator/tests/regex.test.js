// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const regex_1 = require("../utils/regex");
const chai = __importStar(require("chai"));
const chai_as_promised_1 = __importDefault(require("chai-as-promised"));
chai.use(chai_as_promised_1.default);
const expect = chai.expect;
const multiline = `
DO NOT REPLACE
"""
This text can be replaced
This text can be replaced
This text can be replaced
This text can be replaced
This text can be replaced
This text can be replaced
This text can be replaced
"""
DO NOT REPLACE
`;
const indentedMultiline = `
    DO NOT REPLACE
    """
    This text can be replaced
    This text can be replaced
    This text can be replaced
    This text can be replaced
    This text can be replaced
    This text can be replaced
    This text can be replaced
    """
    DO NOT REPLACE
`;
const multilineOneLine = `DO NOT REPLACE """ This text can be replaced """ DO NOT REPLACE`;
const indentedMultilineOneLine = `  DO NOT REPLACE """ This text can be replaced """ DO NOT REPLACE`;
const multilineTwoLines = `
DO NOT REPLACE
""" This text can be replaced
This text can be replaced """
DO NOT REPLACE
`;
const indentedMultilineTwoLines = `
    DO NOT REPLACE
    """ This text can be replaced
    This text can be replaced """
    DO NOT REPLACE
`;
const expectedMultilineOutput = `
DO NOT REPLACE

DO NOT REPLACE
`;
const expectedIndentedMultilineOutput = `
    DO NOT REPLACE

    DO NOT REPLACE
`;
const expectedOneLineOutput = 'DO NOT REPLACE DO NOT REPLACE';
const expectedIndentedOneLineOutput = '  DO NOT REPLACE DO NOT REPLACE';
describe('Regex', () => {
    it('should find and replace multiline comments', () => __awaiter(void 0, void 0, void 0, function* () {
        const convertedMultiline = multiline.replace(regex_1.REGEX.EVERYTHING_BETWEEN_MULTILINE, '');
        const convertedIndentedMultiline = indentedMultiline.replace(regex_1.REGEX.EVERYTHING_BETWEEN_MULTILINE, '');
        const convertedMultilineOneLine = multilineOneLine.replace(regex_1.REGEX.EVERYTHING_BETWEEN_MULTILINE, '');
        const convertedIndentedMultilineOneLine = indentedMultilineOneLine.replace(regex_1.REGEX.EVERYTHING_BETWEEN_MULTILINE, '');
        const convertedMultilineTwoLines = multilineTwoLines.replace(regex_1.REGEX.EVERYTHING_BETWEEN_MULTILINE, '');
        const convertedIndentedMultilineTwoLines = indentedMultilineTwoLines.replace(regex_1.REGEX.EVERYTHING_BETWEEN_MULTILINE, '');
        expect(convertedMultiline).to.be.equal(expectedMultilineOutput);
        expect(convertedIndentedMultiline).to.be.equal(expectedIndentedMultilineOutput);
        expect(convertedMultilineOneLine).to.be.equal(expectedOneLineOutput);
        expect(convertedIndentedMultilineOneLine).to.be.equal(expectedIndentedOneLineOutput);
        expect(convertedMultilineTwoLines).to.be.equal(expectedMultilineOutput);
        expect(convertedIndentedMultilineTwoLines).to.be.equal(expectedIndentedMultilineOutput);
    }));
});
