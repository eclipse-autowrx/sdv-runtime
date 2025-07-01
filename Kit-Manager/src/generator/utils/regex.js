// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

Object.defineProperty(exports, "__esModule", { value: true });
exports.REGEX = void 0;
// NOTE: since safari doesn't support lookbehind regex yet. Try to avoid it.
// https://caniuse.com/js-regexp-lookbehind
exports.REGEX = {
    // Everything between multiline comment from template
    EVERYTHING_BETWEEN_MULTILINE: /([^\S\r\n]*\"\"\"[\s\S]*?\"\"\")/gm,
    GET_EVERY_PLUGINS_USAGE: /.*plugins.*/gm,
    // Replace content in on_start method (Here digital.auto code comes in)
    FIND_BEGIN_OF_ON_START_METHOD: /[\t ]*async def on\_start\(self\)\:[\r\n]/gm,
    FIND_VEHICLE_INIT: /self\.Vehicle \= vehicle_client/gm,
    FIND_VEHICLE_OCCURENCE: /vehicle/gm,
    FIND_UNWANTED_VEHICLE_CHANGE: /\(await self\.Vehicle/gm,
    FIND_PRINTF_STATEMENTS: /print\(f/gm,
    FIND_PRINT_STATEMENTS: /print\(/gm,
    FIND_EVERY_LINE_START: /^(?!\s*$)/gm,
    FIND_LINE_BEGINNING_WITH_WHITESPACES: /^\s+/gm,
    FIND_SAMPLE_APP: /SampleApp/gm,
    FIND_SUBSCRIBE_METHOD_CALL: /\.subscribe\(/gm,
};
