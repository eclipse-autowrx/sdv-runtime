// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

Object.defineProperty(exports, "__esModule", { value: true });
exports.ProjectGeneratorError = void 0;
const axios_1 = require("axios");
/**
 * ProjectGeneratorError puts all relevant information together
 *
 * @property {string} error.name                          - Name of the error.
 * @property {string} error.message                       - Error message.
 * @property {number | undefined} error.statusCode        - API response status code.
 * @property {string | undefined} error.statusText        - API response status text.
 * @property {string[] | undefined} error.responseMessage - Contains API response messages if available.
 */
class ProjectGeneratorError extends axios_1.AxiosError {
    constructor(error) {
        var _a, _b, _c, _d;
        const errors = ((_a = error.response) === null || _a === void 0 ? void 0 : _a.data).errors;
        super(error.message);
        this.name = 'ProjectGeneratorError';
        this.statusCode = (_b = error.response) === null || _b === void 0 ? void 0 : _b.status;
        this.statusText = (_c = error.response) === null || _c === void 0 ? void 0 : _c.statusText;
        this.responseMessages = errors ? errors : ((_d = error.response) === null || _d === void 0 ? void 0 : _d.data).message;
    }
}
exports.ProjectGeneratorError = ProjectGeneratorError;
