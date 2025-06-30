# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT


from lib.dsl import (
    create_animation_action,
    create_behavior,
    create_event_trigger,
    create_set_action,
    get_datapoint_value,
    mock_datapoint,
)
import json
import os

from lib.trigger import ClockTrigger, EventType


json_path = os.getenv("MOCK_SIGNAL", "/home/dev/ws/mock/signals.json")

with open(json_path, 'r') as f:
    listOfSignals = json.load(f)

for signal in listOfSignals:   
    try:
        mock_datapoint(
            path=signal["signal"],
            initial_value=signal["value"],
            behaviors=[
            create_behavior(
                trigger=create_event_trigger(EventType.ACTUATOR_TARGET),
                action=create_set_action("$event.value"),
                )
            ],
        )
    except:
        print("Error occured with this signal")
        continue
