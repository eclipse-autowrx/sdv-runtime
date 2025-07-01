// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

/**
 * Initialize a new `ProjectGenerator` with the given `options`.
 *
 * @param {Object} [options]
 * @return {ProjectGenerator} which can be used to generate a repository.
 * @public
 */
export declare class ProjectGenerator {
    private owner;
    private repo;
    private authToken;
    private gitRequestHandler;
    private codeConverter;
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
    /**
     * @param {string} codeSnippet Base64 encoded playground code snippet.
     * @param {string} appName Name of the VehicleApp.
     * @param {string} vspecPayload Base64 encoded Vspec payload.
     * @throws {ProjectGeneratorError}
     */
    runWithPayload(codeSnippet: string, appName: string, vspecPayload: string): Promise<number>;
    /**
     * @param {string} codeSnippet Base64 encoded playground code snippet.
     * @param {string} appName Name of the VehicleApp.
     * @param {VspecUriObject} VspecUriObject Containing Repo and Commit hash.
     * @throws {ProjectGeneratorError}
     */
    private runWithUri;
    private updateContent;
    private convertCode;
    private getNewAppManifestSha;
    private getNewMainPySha;
}
