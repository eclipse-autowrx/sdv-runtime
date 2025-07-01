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
const project_generator_1 = require("../project-generator");
const chai = __importStar(require("chai"));
const chai_as_promised_1 = __importDefault(require("chai-as-promised"));
const nock_1 = __importDefault(require("nock"));
const constants_1 = require("../utils/constants");
chai.use(chai_as_promised_1.default);
const expect = chai.expect;
const OWNER = 'testOwner';
const REPO = 'testRepo';
const TOKEN = 'testToken';
const BASE64_CODE_SNIPPET = 'VGVzdFNuaXBwZXQ=';
const BASE64_PAYLOAD = 'IntcbiAgICBWZWhpY2xlOiB7XG4gICAgICAgIGNoaWxkcmVuOiB7XG4gICAgICAgIH0sXG4gICAgICAgIGRlc2NyaXB0aW9uOiAnSGlnaC1sZXZlbCB2ZWhpY2xlIGRhdGEuJyxcbiAgICAgICAgdHlwZTogJ2JyYW5jaCcsXG4gICAgICAgIHV1aWQ6ICdjY2M4MjVmOTQxMzk1NDRkYmI1ZjRiZmQwMzNiZWNlNicsXG4gICAgfSxcbn1cbiI=';
const APP_NAME = 'testApp';
const BASE64_CONTENT = 'WwogICB7CiAgICAgICJuYW1lIjoidGVzdGFwcCIsCiAgICAgICJ2ZWhpY2xlTW9kZWwiOnsKICAgICAgICAgInNyYyI6InRlc3RzcmMiCiAgICAgIH0KICAgfQpd';
const MOCK_SHA = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
const vspecUriObject = { repo: 'https://test.com/testOrg/testRepo', commit: '015dd1532922091ce2675755843273c41efbeba8' };
const GITHUB_API_URL = 'https://api.github.com/repos';
const PYTHON_TEMPLATE_URL = `${GITHUB_API_URL}/eclipse-velocitas/vehicle-app-python-template`;
describe('Project Generator', () => {
    it('should initialize', () => __awaiter(void 0, void 0, void 0, function* () {
        const generator = new project_generator_1.ProjectGenerator(OWNER, REPO, TOKEN);
        expect(generator).to.be.instanceof(project_generator_1.ProjectGenerator);
    }));
    // it('should run with URI', async () => {
    //     nock(`${PYTHON_TEMPLATE_URL}`).post('/generate').reply(200);
    //     nock(`${GITHUB_API_URL}/${OWNER}/${REPO}`).get('/contents').reply(200);
    //     nock(`${GITHUB_API_URL}/${OWNER}/${REPO}`).persist().put('/actions/permissions').reply(200);
    //     nock(`${GITHUB_API_URL}/${OWNER}/${REPO}`).get(`/contents/${APP_MANIFEST_PATH}`).reply(200, { content: BASE64_CONTENT });
    //     nock(`${GITHUB_API_URL}/${OWNER}/${REPO}`).get(`/contents/${MAIN_PY_PATH}`).reply(200, { content: BASE64_CONTENT });
    //     nock(`${GITHUB_API_URL}/${OWNER}/${REPO}`).persist().post('/git/blobs').reply(200, { sha: MOCK_SHA });
    //     nock(`${GITHUB_API_URL}/${OWNER}/${REPO}`).get('/git/trees/main').reply(200, { sha: MOCK_SHA });
    //     nock(`${GITHUB_API_URL}/${OWNER}/${REPO}`).post('/git/trees').reply(200, { sha: MOCK_SHA });
    //     nock(`${GITHUB_API_URL}/${OWNER}/${REPO}`)
    //         .get('/git/refs/heads/main')
    //         .reply(200, { object: { sha: MOCK_SHA } });
    //     nock(`${GITHUB_API_URL}/${OWNER}/${REPO}`).post('/git/commits').reply(200, { sha: MOCK_SHA });
    //     nock(`${GITHUB_API_URL}/${OWNER}/${REPO}`).put('/actions/permissions/workflow').reply(200);
    //     nock(`${GITHUB_API_URL}/${OWNER}/${REPO}`).patch('/git/refs/heads/main').reply(200, { content: MOCK_SHA });
    //     const generator = new ProjectGenerator(OWNER, REPO, TOKEN);
    //     const response = await generator.runWithUri(BASE64_CODE_SNIPPET, APP_NAME, vspecUriObject);
    //     expect(response).to.be.equal(200);
    // });
    it('should run with payload', () => __awaiter(void 0, void 0, void 0, function* () {
        (0, nock_1.default)(`${PYTHON_TEMPLATE_URL}`).post('/generate').reply(200);
        (0, nock_1.default)(`${GITHUB_API_URL}/${OWNER}/${REPO}`).get('/contents').reply(200);
        (0, nock_1.default)(`${GITHUB_API_URL}/${OWNER}/${REPO}`).persist().put('/actions/permissions').reply(200);
        (0, nock_1.default)(`${GITHUB_API_URL}/${OWNER}/${REPO}`).get(`/contents/${constants_1.APP_MANIFEST_PATH}`).reply(200, { content: BASE64_CONTENT });
        (0, nock_1.default)(`${GITHUB_API_URL}/${OWNER}/${REPO}`).get(`/contents/${constants_1.MAIN_PY_PATH}`).reply(200, { content: BASE64_CONTENT });
        (0, nock_1.default)(`${GITHUB_API_URL}/${OWNER}/${REPO}`).persist().post('/git/blobs').reply(200, { sha: MOCK_SHA });
        (0, nock_1.default)(`${GITHUB_API_URL}/${OWNER}/${REPO}`).get('/git/trees/main').reply(200, { sha: MOCK_SHA });
        (0, nock_1.default)(`${GITHUB_API_URL}/${OWNER}/${REPO}`).post('/git/trees').reply(200, { sha: MOCK_SHA });
        (0, nock_1.default)(`${GITHUB_API_URL}/${OWNER}/${REPO}`)
            .get('/git/refs/heads/main')
            .reply(200, { object: { sha: MOCK_SHA } });
        (0, nock_1.default)(`${GITHUB_API_URL}/${OWNER}/${REPO}`).post('/git/commits').reply(200, { sha: MOCK_SHA });
        (0, nock_1.default)(`${GITHUB_API_URL}/${OWNER}/${REPO}`).put('/actions/permissions/workflow').reply(200);
        (0, nock_1.default)(`${GITHUB_API_URL}/${OWNER}/${REPO}`).patch('/git/refs/heads/main').reply(200, { content: MOCK_SHA });
        const generator = new project_generator_1.ProjectGenerator(OWNER, REPO, TOKEN);
        const response = yield generator.runWithPayload(BASE64_CODE_SNIPPET, APP_NAME, BASE64_PAYLOAD);
        expect(response).to.be.equal(200);
    }));
    it('should throw an error on repository generation', () => __awaiter(void 0, void 0, void 0, function* () {
        (0, nock_1.default)(`${PYTHON_TEMPLATE_URL}`).post('/generate').reply(422);
        const generator = new project_generator_1.ProjectGenerator(OWNER, REPO, TOKEN);
        yield expect(generator.runWithPayload(BASE64_CODE_SNIPPET, APP_NAME, BASE64_PAYLOAD)).to.eventually.be.rejectedWith(Error);
    }));
});
