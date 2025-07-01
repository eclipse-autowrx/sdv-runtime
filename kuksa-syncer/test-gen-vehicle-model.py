# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

from vehicle_model_manager import generate_vehicle_model, revert_vehicle_model
# from utils import restartMockProvider
import time
import json

SAMPLE_VEHICLE_MODEL = {
    "Car": {
        "description": "High-level vehicle data.",
        "type": "branch",
        "children": {
            "ADAS": {
                "description": "High-level vehicle data.",
                "type": "branch",
                "children": {
                    "ABS": {
                        "description": "High-level vehicle data.",
                        "type": "branch",
                        "children": {
                            "IsEnabled": {
                                "datatype": "boolean",
                                "description": "Indicates if ABS is enabled. True = Enabled. False = Disabled.",
                                "type": "actuator",
                                "uuid": "cad374fbfdc65df9b777508f04d5b073"
                            },
                            "IsEngaged": {
                                "datatype": "boolean",
                                "description": "Indicates if ABS is currently regulating brake pressure. True = Engaged. False = Not Engaged.",
                                "type": "sensor",
                                "uuid": "6dd21979a2225e31940dc2ece1aa9a04"
                            },
                            "IsError": {
                                "datatype": "string",
                                "description": "Indicates if ABS incurred an error condition. True = Error. False = No Error.",
                                "type": "actuator",
                                "unit": "iso8601",
                                "uuid": "13cfabb3122254128234f9a696f14678"
                            }
                        },
                        "description": "Antilock Braking System signals.",
                        "type": "branch",
                        "uuid": "219270ef27c4531f874bbda63743b330"
                    },
                }
            }
        }
    }
}


# print("Hello")
# stringify the sample vehicle model
stringified_vehicle_model = json.dumps(SAMPLE_VEHICLE_MODEL)

generate_vehicle_model(stringified_vehicle_model)
time.sleep(1)
# restartMockProvider()