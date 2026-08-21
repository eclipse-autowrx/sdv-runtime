// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

const config = {
    port: parseInt(process.env.KIT_MANAGER_PORT, 10) || 3090
}

module.exports = config;