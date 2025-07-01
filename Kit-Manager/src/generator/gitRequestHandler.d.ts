// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

/**
 * Initialize a new `GitRequestHandler` with the given `options`.
 *
 * @param {Object} [options]
 * @return {GitRequestHandler} which holds methods to make requests to the GitHub API.
 * @public
 */
export declare class GitRequestHandler {
    private owner;
    private repo;
    private authToken;
    private requestConfig;
    private repositoryPath;
    private pythonTemplateClient;
    private gitClient;
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
    constructor(owner: string, repo: string, authToken: string);
    generateRepo(): Promise<number>;
    createBlob(fileContent: string): Promise<string>;
    updateTree(appManifestBlobSha: string, mainPyBlobSha: string, vspecJsonBlobSha?: string): Promise<number>;
    getFileContentData(filePath: string): Promise<string>;
    private checkRepoAvailability;
    private enableWorkflows;
    private setDefaultWorkflowPermissionToWrite;
    private getBaseTreeSha;
    private createNewTreeSha;
    private getMainBranchSha;
    private createCommitSha;
    private updateMainBranchSha;
}
