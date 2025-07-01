// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

Object.defineProperty(exports, "__esModule", { value: true });
exports.INDENTATION = exports.DIGITAL_AUTO = exports.VELOCITAS = exports.PYTHON = void 0;
exports.PYTHON = {
    CLASS: 'class',
    IMPORT: 'import',
    IMPORT_DEPENDENCY_FROM: 'from',
    COMMENT: '#',
    SYNC_METHOD_START: 'def ',
    ASYNC_METHOD_START: 'async def ',
    AWAIT: 'await',
};
exports.VELOCITAS = {
    MAIN_METHOD: 'async def main():',
    ON_START: 'async def on_start(self):',
    VEHICLE_APP_SUFFIX: 'App',
    CLASS_METHOD_SIGNATURE: '(self, data: DataPointReply)',
    SUBSCRIPTION_SIGNATURE: '.subscribe(self.',
    INFO_LOGGER_SIGNATURE: 'logger.info(',
    VEHICLE_CALL: 'await self.Vehicle',
    VEHICLE_CALL_AS_ARGUMENT: '(self.Vehicle',
    GET_VALUE: '.get()).value',
    IMPORT_SUBSCRIBE_TOPIC: ', subscribe_topic',
    IMPORT_DATAPOINT_REPLY: 'from sdv.vdb.subscriptions import DataPointReply',
    EVENT_LOOP: 'LOOP',
    NEW_EVENT_LOOP: 'asyncio.run(main())',
    VEHICLE_APP_SIGNATURE: '(VehicleApp):',
    ASYNCIO: 'await asyncio',
    PREDEFINED_TOPIC: '_TOPIC =',
    TYPE_IGNORE: '# type',
};
exports.DIGITAL_AUTO = {
    VEHICLE_INIT: 'Vehicle()',
    SET_TEXT: 'set_text',
    NOTIFY: 'notify',
    SUBSCRIBE_CALL: '.subscribe(',
    IMPORT_PLUGINS: 'import plugins',
};
exports.INDENTATION = { COUNT_CLASS: 4, COUNT_METHOD: 8 };
