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
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProjectGenerator = void 0;
const http_status_codes_1 = require("http-status-codes");
const code_converter_1 = require("./code-converter");
const constants_1 = require("./utils/constants");
const helpers_1 = require("./utils/helpers");
const gitRequestHandler_1 = require("./gitRequestHandler");

const MAIN_PY_CONTENT =`
# Copyright (c) 2022 Robert Bosch GmbH and Microsoft Corporation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""A sample skeleton vehicle app."""

import asyncio
import json
import logging
import signal

from sdv.util.log import (  # type: ignore
    get_opentelemetry_log_factory,
    get_opentelemetry_log_format,
)
from sdv.vdb.reply import DataPointReply
from sdv.vehicle_app import VehicleApp, subscribe_topic
from vehicle import Vehicle, vehicle  # type: ignore

# Configure the VehicleApp logger with the necessary log config and level.
logging.setLogRecordFactory(get_opentelemetry_log_factory())
logging.basicConfig(format=get_opentelemetry_log_format())
logging.getLogger().setLevel("DEBUG")
logger = logging.getLogger(__name__)

GET_SPEED_REQUEST_TOPIC = "sampleapp/getSpeed"
GET_SPEED_RESPONSE_TOPIC = "sampleapp/getSpeed/response"
DATABROKER_SUBSCRIPTION_TOPIC = "sampleapp/currentSpeed"


class SampleApp(VehicleApp):
    """
    Sample skeleton vehicle app.

    The skeleton subscribes to a getSpeed MQTT topic
    to listen for incoming requests to get
    the current vehicle speed and publishes it to
    a response topic.

    It also subcribes to the VehicleDataBroker
    directly for updates of the
    Vehicle.Speed signal and publishes this
    information via another specific MQTT topic
    """

    def __init__(self, vehicle_client: Vehicle):
        # SampleApp inherits from VehicleApp.
        super().__init__()
        self.Vehicle = vehicle_client

    async def on_start(self):
        """Run when the vehicle app starts"""
        # This method will be called by the SDK when the connection to the
        # Vehicle DataBroker is ready.
        # Here you can subscribe for the Vehicle Signals update (e.g. Vehicle Speed).
        await self.Vehicle.Speed.subscribe(self.on_speed_change)

    async def on_speed_change(self, data: DataPointReply):
        """The on_speed_change callback, this will be executed when receiving a new
        vehicle signal updates."""
        # Get the current vehicle speed value from the received DatapointReply.
        # The DatapointReply containes the values of all subscribed DataPoints of
        # the same callback.
        vehicle_speed = data.get(self.Vehicle.Speed).value

        # Do anything with the received value.
        # Example:
        # - Publishes current speed to MQTT Topic (i.e. DATABROKER_SUBSCRIPTION_TOPIC).
        await self.publish_mqtt_event(
            DATABROKER_SUBSCRIPTION_TOPIC,
            json.dumps({"speed": vehicle_speed}),
        )

    @subscribe_topic(GET_SPEED_REQUEST_TOPIC)
    async def on_get_speed_request_received(self, data: str) -> None:
        """The subscribe_topic annotation is used to subscribe for incoming
        PubSub events, e.g. MQTT event for GET_SPEED_REQUEST_TOPIC.
        """

        # Use the logger with the preferred log level (e.g. debug, info, error, etc)
        logger.debug(
            "PubSub event for the Topic: %s -> is received with the data: %s",
            GET_SPEED_REQUEST_TOPIC,
            data,
        )

        # Getting current speed from VehicleDataBroker using the DataPoint getter.
        vehicle_speed = (await self.Vehicle.Speed.get()).value

        # Do anything with the speed value.
        # Example:
        # - Publishe the vehicle speed to MQTT topic (i.e. GET_SPEED_RESPONSE_TOPIC).
        await self.publish_mqtt_event(
            GET_SPEED_RESPONSE_TOPIC,
            json.dumps(
                {
                    "result": {
                        "status": 0,
                        "message": f"""Current Speed = {vehicle_speed}""",
                    },
                }
            ),
        )


async def main():
    """Main function"""
    logger.info("Starting SampleApp...")
    # Constructing SampleApp and running it.
    vehicle_app = SampleApp(vehicle)
    await vehicle_app.run()


LOOP = asyncio.get_event_loop()
LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
LOOP.run_until_complete(main())
LOOP.close()
`

/**
 * Initialize a new `ProjectGenerator` with the given `options`.
 *
 * @param {Object} [options]
 * @return {ProjectGenerator} which can be used to generate a repository.
 * @public
 */
class ProjectGenerator {
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
        this.codeConverter = new code_converter_1.CodeConverter();
        this.gitRequestHandler = new gitRequestHandler_1.GitRequestHandler(this.owner, this.repo, this.authToken);
    }
    /**
     * @param {string} codeSnippet Base64 encoded playground code snippet.
     * @param {string} appName Name of the VehicleApp.
     * @param {string} vspecPayload Base64 encoded Vspec payload.
     * @throws {ProjectGeneratorError}
     */
    runWithPayload(codeSnippet, appName, vspecPayload) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                // let decodedVspecPayload = JSON.parse((0, helpers_1.decode)(vspecPayload));
                const convertedCode = yield this.convertCode(appName, codeSnippet);
                // console.log("convertedCode", convertedCode)
                // yield this.gitRequestHandler.generateRepo();
                // Delay is introduced to make sure that the git API creates
                // everything we need before doing other API requests
                // yield (0, helpers_1.delay)(constants_1.MS_TO_WAIT_FOR_GITHUB);
                // const encodedVspec = (0, helpers_1.encode)(`${JSON.stringify(decodedVspecPayload, null, 4)}\n`);
                // const vspecJsonBlobSha = yield this.gitRequestHandler.createBlob(encodedVspec);
                // yield this.updateContent(appName, codeSnippet, `./${constants_1.LOCAL_VSPEC_PATH}`, vspecJsonBlobSha);
                return convertedCode;
            }
            catch (error) {
                throw error;
            }
        });
    }
    /**
     * @param {string} codeSnippet Base64 encoded playground code snippet.
     * @param {string} appName Name of the VehicleApp.
     * @param {VspecUriObject} VspecUriObject Containing Repo and Commit hash.
     * @throws {ProjectGeneratorError}
     */
    runWithUri(codeSnippet, appName, vspecUriObject) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                // Assumption for now is, that all individual vspecs are a fork of COVESA following this path
                // const vspecUriString = `${vspecUriObject.repo}/tree/${vspecUriObject.commit}/spec`;
                // yield this.gitRequestHandler.generateRepo();
                // Delay is introduced to make sure that the git API creates
                // everything we need before doing other API requests
                // yield (0, helpers_1.delay)(constants_1.MS_TO_WAIT_FOR_GITHUB);
                const convertedCode = yield this.convertCode(appName, codeSnippet);
                console.log("convertedCode", convertedCode)
                // yield this.updateContent(appName, codeSnippet, vspecUriString);
                return http_status_codes_1.StatusCodes.OK;
            }
            catch (error) {
                throw error;
            }
        });
    }
    updateContent(appName, codeSnippet, vspecPath, vspecJsonBlobSha) {
        return __awaiter(this, void 0, void 0, function* () {
            // const convertedCode = yield this.convertCode(appName, codeSnippet);
            // console.log("convertedCode", convertedCode)
            // const appManifestBlobSha = yield this.getNewAppManifestSha(appName, vspecPath, convertedCode.dataPoints);
            // const mainPyBlobSha = yield this.getNewMainPySha(convertedCode.finalizedMainPy);
            // yield this.gitRequestHandler.updateTree(appManifestBlobSha, mainPyBlobSha, vspecJsonBlobSha);
            return http_status_codes_1.StatusCodes.OK;
        });
    }
    convertCode(appName, codeSnippet) {
        return __awaiter(this, void 0, void 0, function* () {
            // const mainPyContentData = yield this.gitRequestHandler.getFileContentData(constants_1.MAIN_PY_PATH);
            const mainPyContentData = MAIN_PY_CONTENT;
            const decodedMainPyContentData = (0, helpers_1.decode)(mainPyContentData);
            const decodedBase64CodeSnippet = (0, helpers_1.decode)(codeSnippet);
            const convertedCode = this.codeConverter.convertMainPy(MAIN_PY_CONTENT, decodedBase64CodeSnippet, appName);
            return convertedCode;
        });
    }
    getNewAppManifestSha(appName, vspecPath, dataPoints) {
        return __awaiter(this, void 0, void 0, function* () {
            const appManifestContentData = yield this.gitRequestHandler.getFileContentData(constants_1.APP_MANIFEST_PATH);
            let decodedAppManifestContent = JSON.parse((0, helpers_1.decode)(appManifestContentData));
            decodedAppManifestContent[0].name = appName.toLowerCase();
            decodedAppManifestContent[0].vehicleModel.src = vspecPath;
            decodedAppManifestContent[0].vehicleModel.datapoints = dataPoints;
            const encodedAppManifestContent = (0, helpers_1.encode)(`${JSON.stringify(decodedAppManifestContent, null, 4)}\n`);
            // const appManifestBlobSha = yield this.gitRequestHandler.createBlob(encodedAppManifestContent);
            return appManifestBlobSha;
        });
    }
    getNewMainPySha(finalizedMainPy) {
        return __awaiter(this, void 0, void 0, function* () {
            const encodedFinalizedMainPy = (0, helpers_1.encode)(`${finalizedMainPy}\n`);
            // const mainPyBlobSha = yield this.gitRequestHandler.createBlob(encodedFinalizedMainPy);
            return mainPyBlobSha;
        });
    }
}
exports.ProjectGenerator = ProjectGenerator;
