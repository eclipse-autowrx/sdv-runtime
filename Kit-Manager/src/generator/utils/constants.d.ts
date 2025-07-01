// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

export declare const GITHUB_API_URL = "https://api.github.com/repos";
export declare const PYTHON_TEMPLATE_URL: string;
export declare const CONTENT_ENCODINGS: {
    utf8: string;
    base64: string;
};
export declare const GIT_DATA_TYPES: {
    blob: string;
    tree: string;
    commit: string;
};
export declare const GIT_DATA_MODES: {
    fileBlob: string;
    executableBlob: string;
    subdirectoryTree: string;
    submoduleCommit: string;
    symlinkPathBlob: string;
};
export declare const DEFAULT_REPOSITORY_DESCRIPTION = "Template generated from eclipse-velocitas";
export declare const DEFAULT_COMMIT_MESSAGE = "Update content with digital.auto code";
export declare const MS_TO_WAIT_FOR_GITHUB = 4000;
export declare const LOCAL_VSPEC_PATH = "app/vspec.json";
export declare const APP_MANIFEST_PATH = "app/AppManifest.json";
export declare const MAIN_PY_PATH = "app/src/main.py";
