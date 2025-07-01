// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

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
exports.GitRequestHandler = void 0;
const axios_1 = __importDefault(require("axios"));
const project_generator_error_1 = require("./project-generator-error");
const http_status_codes_1 = require("http-status-codes");
const constants_1 = require("./utils/constants");
const helpers_1 = require("./utils/helpers");
/**
 * Initialize a new `GitRequestHandler` with the given `options`.
 *
 * @param {Object} [options]
 * @return {GitRequestHandler} which holds methods to make requests to the GitHub API.
 * @public
 */
class GitRequestHandler {
    /**
     * Parameter will be used to call the GitHub API as follows:
     * https://api.github.com/repos/OWNER/REPO
     *
     * PAT or Oauth token with scope for atleast:
     * user, public_repo, repo, notifications, gist
     * @param {string} owner
     * @param {string} repo
     * @param {string} authToken as PAT or Oauth Token
     */
    constructor(owner, repo, authToken) {
        this.owner = owner;
        this.repo = repo;
        this.authToken = authToken;
        this.requestConfig = {
            headers: {
                'Content-Type': 'application/json',
                Accept: 'application/vnd.github+json',
                Authorization: `Bearer ${this.authToken}`,
            },
        };
        this.repositoryPath = `${constants_1.GITHUB_API_URL}/${this.owner}/${this.repo}`;
        this.pythonTemplateClient = axios_1.default.create(Object.assign({ baseURL: constants_1.PYTHON_TEMPLATE_URL }, this.requestConfig));
        this.gitClient = axios_1.default.create(Object.assign({ baseURL: this.repositoryPath }, this.requestConfig));
    }
    generateRepo() {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                yield this.pythonTemplateClient.post('/generate', {
                    owner: this.owner,
                    name: this.repo,
                    description: constants_1.DEFAULT_REPOSITORY_DESCRIPTION,
                    include_all_branches: false,
                    private: true,
                });
            }
            catch (error) {
                if (axios_1.default.isAxiosError(error)) {
                    throw new project_generator_error_1.ProjectGeneratorError(error);
                }
                else {
                    throw error;
                }
            }
            const responseStatus = yield this.checkRepoAvailability();
            yield this.enableWorkflows(false);
            return responseStatus;
        });
    }
    createBlob(fileContent) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const response = yield this.gitClient.post('/git/blobs', {
                    content: fileContent,
                    encoding: constants_1.CONTENT_ENCODINGS.base64,
                });
                const blobSha = response.data.sha;
                return blobSha;
            }
            catch (error) {
                if (axios_1.default.isAxiosError(error)) {
                    throw new project_generator_error_1.ProjectGeneratorError(error);
                }
                else {
                    throw error;
                }
            }
        });
    }
    updateTree(appManifestBlobSha, mainPyBlobSha, vspecJsonBlobSha = '') {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const baseTreeSha = yield this.getBaseTreeSha();
                const newTreeSha = yield this.createNewTreeSha(appManifestBlobSha, mainPyBlobSha, vspecJsonBlobSha, baseTreeSha);
                const mainBranchSha = yield this.getMainBranchSha();
                const newCommitSha = yield this.createCommitSha(mainBranchSha, newTreeSha);
                yield (0, helpers_1.delay)(constants_1.MS_TO_WAIT_FOR_GITHUB);
                yield this.setDefaultWorkflowPermissionToWrite();
                yield this.enableWorkflows(true);
                yield this.updateMainBranchSha(newCommitSha);
                return http_status_codes_1.StatusCodes.OK;
            }
            catch (error) {
                throw error;
            }
        });
    }
    getFileContentData(filePath) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const fileContentResponse = yield this.gitClient.get(`/contents/${filePath}`);
                const fileContentData = fileContentResponse.data.content;
                return fileContentData;
            }
            catch (error) {
                throw error;
            }
        });
    }
    checkRepoAvailability() {
        var _a;
        return __awaiter(this, void 0, void 0, function* () {
            let retries = 0;
            let success = false;
            let responseStatus = http_status_codes_1.StatusCodes.INTERNAL_SERVER_ERROR;
            const maxRetries = 20;
            while (retries < maxRetries && !success) {
                try {
                    const response = yield this.gitClient.get('/contents');
                    responseStatus = response.status;
                    success = true;
                    return responseStatus;
                }
                catch (error) {
                    if (axios_1.default.isAxiosError(error)) {
                        console.log(`Check #${retries + 1} if Repository is generated failed. Retrying.`);
                        responseStatus = (_a = error.response) === null || _a === void 0 ? void 0 : _a.status;
                    }
                    else {
                        throw error;
                    }
                }
                retries++;
            }
            return responseStatus;
        });
    }
    enableWorkflows(isEnabled) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                yield this.gitClient.put('/actions/permissions', {
                    enabled: isEnabled,
                });
                return true;
            }
            catch (error) {
                console.log(error);
                return false;
            }
        });
    }
    setDefaultWorkflowPermissionToWrite() {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                yield this.gitClient.put('/actions/permissions/workflow', {
                    default_workflow_permissions: 'write',
                });
                return true;
            }
            catch (error) {
                console.log(error);
                return false;
            }
        });
    }
    getBaseTreeSha() {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const response = yield this.gitClient.get('/git/trees/main');
                const baseTreeSha = response.data.sha;
                return baseTreeSha;
            }
            catch (error) {
                throw error;
            }
        });
    }
    createNewTreeSha(appManifestBlobSha, mainPyBlobSha, vspecJsonBlobSha, baseTreeSha) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const treeArray = [
                    {
                        path: constants_1.APP_MANIFEST_PATH,
                        mode: constants_1.GIT_DATA_MODES.fileBlob,
                        type: constants_1.GIT_DATA_TYPES.blob,
                        sha: appManifestBlobSha,
                    },
                    {
                        path: constants_1.MAIN_PY_PATH,
                        mode: constants_1.GIT_DATA_MODES.fileBlob,
                        type: constants_1.GIT_DATA_TYPES.blob,
                        sha: mainPyBlobSha,
                    },
                ];
                if (vspecJsonBlobSha) {
                    treeArray.push({
                        path: constants_1.LOCAL_VSPEC_PATH,
                        mode: constants_1.GIT_DATA_MODES.fileBlob,
                        type: constants_1.GIT_DATA_TYPES.blob,
                        sha: vspecJsonBlobSha,
                    });
                }
                const response = yield this.gitClient.post('/git/trees', {
                    tree: treeArray,
                    base_tree: baseTreeSha,
                });
                const newTreeSha = response.data.sha;
                return newTreeSha;
            }
            catch (error) {
                throw error;
            }
        });
    }
    getMainBranchSha() {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const response = yield this.gitClient.get('/git/refs/heads/main');
                const mainBranchSha = response.data.object.sha;
                return mainBranchSha;
            }
            catch (error) {
                throw error;
            }
        });
    }
    createCommitSha(mainBranchSha, newTreeSha) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const response = yield this.gitClient.post('/git/commits', {
                    tree: newTreeSha,
                    message: constants_1.DEFAULT_COMMIT_MESSAGE,
                    parents: [mainBranchSha],
                });
                const commitSha = response.data.sha;
                return commitSha;
            }
            catch (error) {
                throw error;
            }
        });
    }
    updateMainBranchSha(newCommitSha) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const response = yield this.gitClient.patch('/git/refs/heads/main', {
                    sha: newCommitSha,
                });
                const patchResponse = response.data;
                return patchResponse;
            }
            catch (error) {
                throw error;
            }
        });
    }
}
exports.GitRequestHandler = GitRequestHandler;
