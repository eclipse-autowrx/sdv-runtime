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
const fs_1 = require("fs");
const path = __importStar(require("path"));
const chai = __importStar(require("chai"));
const chai_as_promised_1 = __importDefault(require("chai-as-promised"));
const code_converter_1 = require("../code-converter");
const helpers_1 = require("../utils/helpers");
chai.use(chai_as_promised_1.default);
const expect = chai.expect;
const APP_NAME = 'test';
const EXAMPLE_INPUT_1 = (0, fs_1.readFileSync)(`${path.join(__dirname, 'files/example_input_1.py')}`, 'utf8');
const EXAMPLE_INPUT_2 = (0, fs_1.readFileSync)(`${path.join(__dirname, 'files/example_input_2.py')}`, 'utf8');
const EXPECTED_OUTPUT_1 = (0, fs_1.readFileSync)(`${path.join(__dirname, 'files/example_output_1.py')}`, 'utf8');
const EXPECTED_DATAPOINTS_1 = [
    {
        path: 'Vehicle.Body.Windshield.Front.Wiping.System.ActualPosition',
        required: 'true',
        access: 'write',
    },
    {
        path: 'Vehicle.Body.Windshield.Front.Wiping.System.Mode',
        required: 'true',
        access: 'write',
    },
    {
        path: 'Vehicle.Body.Windshield.Front.Wiping.Mode',
        required: 'true',
        access: 'write',
    },
    {
        path: 'Vehicle.Body.Windshield.Front.Wiping.System.Frequency',
        required: 'true',
        access: 'write',
    },
    {
        path: 'Vehicle.Body.Windshield.Front.Wiping.System.TargetPosition',
        required: 'true',
        access: 'write',
    },
];
const EXPECTED_DATAPOINTS_2 = [
    {
        path: 'Vehicle.Cabin.Sunroof.Switch',
        required: 'true',
        access: 'write',
    },
];
const EXPECTED_OUTPUT_2 = (0, fs_1.readFileSync)(`${path.join(__dirname, 'files/example_output_2.py')}`, 'utf8');
const VELOCITAS_TEMPLATE_MAINPY = (0, fs_1.readFileSync)(`${path.join(__dirname, 'files/velocitas_template_main.py')}`, 'utf8');
const MQTT_MESSAGE_WITH_FORMAT_STRING = `
format_1 = "test_1"
format_2 = "test_2"
test_1.set_text(f"{format_1} is finished and will format correctly")
test_2.set_text(f"{format_2} is finished and will format correctly")
`;
const EXPECTED_MQTT_PUBLISH_WITH_FORMAT_STRING = [
    [
        '       await self.publish_mqtt_event(',
        '            "test_1",',
        '            json.dumps(',
        '                {',
        '                    "result": {',
        '                        "message": f"""{self.format_1} is finished and will format correctly"""',
        '                    }',
        '                }',
        '            ),',
        '        )',
    ],
    [
        '        await self.publish_mqtt_event(',
        '            "test_2",',
        '            json.dumps(',
        '                {',
        '                    "result": {',
        '                        "message": f"""{self.format_2} is finished and will format correctly"""',
        '                    }',
        '                }',
        '            ),',
        '        )',
    ],
];
const MQTT_MESSAGE_WITHOUT_FORMAT_STRING = 'plugin.notifyTest("Test is finished and will format correctly")';
const EXPECTED_MQTT_PUBLISH_WITHOUT_FORMAT_STRING = [
    '        await self.publish_mqtt_event(',
    '            "notifyTest",',
    '            json.dumps({"result": {"message": """Test is finished and will format correctly"""}}),',
    '        )',
];
describe('Code Converter', () => {
    it('should initialize', () => __awaiter(void 0, void 0, void 0, function* () {
        const codeConverter = new code_converter_1.CodeConverter();
        expect(codeConverter).to.be.instanceof(code_converter_1.CodeConverter);
    }));
    it('should format main.py correctly for example 1', () => __awaiter(void 0, void 0, void 0, function* () {
        const codeConverter = new code_converter_1.CodeConverter();
        const convertedMainPy = codeConverter.convertMainPy(VELOCITAS_TEMPLATE_MAINPY, EXAMPLE_INPUT_1, APP_NAME);
        expect(convertedMainPy.finalizedMainPy).to.be.equal(EXPECTED_OUTPUT_1.trim());
    }));
    it('should format main.py correctly for example 2', () => __awaiter(void 0, void 0, void 0, function* () {
        const codeConverter = new code_converter_1.CodeConverter();
        const convertedMainPy = codeConverter.convertMainPy(VELOCITAS_TEMPLATE_MAINPY, EXAMPLE_INPUT_2, APP_NAME);
        expect(convertedMainPy.finalizedMainPy).to.be.equal(EXPECTED_OUTPUT_2.trim());
    }));
    it('should extract correct datapoints for example 1', () => __awaiter(void 0, void 0, void 0, function* () {
        const codeConverter = new code_converter_1.CodeConverter();
        const convertedMainPy = codeConverter.convertMainPy(VELOCITAS_TEMPLATE_MAINPY, EXAMPLE_INPUT_1, APP_NAME);
        expect(convertedMainPy.dataPoints).to.be.deep.equal(EXPECTED_DATAPOINTS_1);
    }));
    it('should extract correct datapoints for example 2', () => __awaiter(void 0, void 0, void 0, function* () {
        const codeConverter = new code_converter_1.CodeConverter();
        const convertedMainPy = codeConverter.convertMainPy(VELOCITAS_TEMPLATE_MAINPY, EXAMPLE_INPUT_2, APP_NAME);
        expect(convertedMainPy.dataPoints).to.be.deep.equal(EXPECTED_DATAPOINTS_2);
    }));
});
describe('Transform to MQTT', () => {
    it('should transform publish_mqtt_event with format string correctly', () => __awaiter(void 0, void 0, void 0, function* () {
        const codeConverter = new code_converter_1.CodeConverter();
        const convertedMainPy = codeConverter.convertMainPy(VELOCITAS_TEMPLATE_MAINPY, MQTT_MESSAGE_WITH_FORMAT_STRING.trim(), APP_NAME);
        const newMainPyArray = (0, helpers_1.createArrayFromMultilineString)(convertedMainPy.finalizedMainPy.trim());
        expect(newMainPyArray.join()).to.include(EXPECTED_MQTT_PUBLISH_WITH_FORMAT_STRING[0]);
        expect(newMainPyArray.join()).to.include(EXPECTED_MQTT_PUBLISH_WITH_FORMAT_STRING[1]);
    }));
    it('should transform publish_mqtt_event without format string correctly', () => __awaiter(void 0, void 0, void 0, function* () {
        const codeConverter = new code_converter_1.CodeConverter();
        const convertedMainPy = codeConverter.convertMainPy(VELOCITAS_TEMPLATE_MAINPY, MQTT_MESSAGE_WITHOUT_FORMAT_STRING.trim(), APP_NAME);
        const newMainPyArray = (0, helpers_1.createArrayFromMultilineString)(convertedMainPy.finalizedMainPy.trim());
        expect(newMainPyArray.join()).to.include(EXPECTED_MQTT_PUBLISH_WITHOUT_FORMAT_STRING);
    }));
});
