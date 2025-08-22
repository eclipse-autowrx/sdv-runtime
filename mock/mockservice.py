# /********************************************************************************
# * Copyright (c) 2023 Contributors to the Eclipse Foundation
# *
# * See the NOTICE file(s) distributed with this work for additional
# * information regarding copyright ownership.
# *
# * This program and the accompanying materials are made available under the
# * terms of the Apache License 2.0 which is available at
# * http://www.apache.org/licenses/LICENSE-2.0
# *
# * SPDX-License-Identifier: Apache-2.0
# ********************************************************************************/

import asyncio
import logging
import os
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterator, List

import grpc
from kuksa_client.grpc import Datapoint
from lib.baseservice import BaseService, is_grpc_fatal_error
from lib.json_array_patch import apply_global_patch

# Apply global JSON patch for array serialization
apply_global_patch()
from lib.behaviorexecutor import BehaviorExecutor
from lib.mockeddatapoint import MockedDataPoint
from lib.datapoint import DataPoint
from lib.loader import PythonDslLoader
from lib.types import Event
from lib.action import AnimationAction
from lib.dsl import _mocked_datapoints, _required_datapoint_paths
# Import mock points that have been defined in mock.py
import mock   # noqa # pylint: disable=unused-import

SERVICE_NAME = "mock_service"

log = logging.getLogger(SERVICE_NAME)
log.setLevel(logging.INFO)

# Create a file handler and set the log file name
file_handler = logging.FileHandler("mock_service.log")

# Create a log formatter and set the format of log records
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Add the file handler to the log
log.addHandler(file_handler)

event = threading.Event()

# Set the log level to suppress log messages because we call connect/disconnect of client quite often
logging.getLogger("kuksa_client").setLevel(logging.INFO)

# Data point events from VDB
EVENT_KEY_ACTUATOR_TARGET = "actuator_target"
EVENT_KEY_VALUE = "value"


class MockService(BaseService):
    """Service implementation which reads custom mocking configuration
    from mock.py and then simulated the programmed behavior of the mocked
    datapoints."""

    def __init__(self, service_address: str, databroker_address: str):
        log.info("Initialization ...")
        super().__init__(service_address, SERVICE_NAME, databroker_address)
        self._ids: Dict[str, Any] = dict()
        self._registered = False
        self._last_tick = time.perf_counter()
        self._pending_event_list: List[Event] = list()
        self._mocked_datapoints: Dict[str, MockedDataPoint] = dict()
        self._last_activity_time = time.perf_counter()
        self._idle_threshold = float(os.getenv("MOCK_IDLE_THRESHOLD", "30.0"))  # seconds of inactivity before entering idle mode
        self._is_idle = False
        self._base_sleep_duration = float(os.getenv("MOCK_BASE_SLEEP", "0.1"))  # base sleep time in active mode
        self._idle_sleep_duration = float(os.getenv("MOCK_IDLE_SLEEP", "1.0"))  # sleep time when idle

    # this will work if mock.py is provided
    def on_databroker_connected(self):
        """Callback when a connection to the data broker is established."""
        log.info("Databroker connected!")
        if not self._registered:
            self.check_for_new_mocks(True)
            self._feed_initial_values()

    # this will work on the fly
    def check_for_new_mocks(self, changed=False):
        new_datapoints = set([d["path"] for d in _mocked_datapoints if "path" in d] + _required_datapoint_paths)
        if set(self._mocked_datapoints.keys()) != new_datapoints:
            changed = True
            log.info("Datapoint added/removed")
        else:
            for dict in _mocked_datapoints:
                if dict["behaviors"] != self._mocked_datapoints[dict["path"]].behaviors:
                    changed = True
                    log.info("Behavior added")

        if changed:
            loader_result = PythonDslLoader().load(self._client)
            self._mocked_datapoints = loader_result.mocked_datapoints

            for _, datapoint in self._mocked_datapoints.items():
                datapoint.datapoint.value_listener = self._on_datapoint_updated

            self._behavior_executor = BehaviorExecutor(
                self._mocked_datapoints, self._pending_event_list, self._client
            )
            self._subscribe_to_mocked_datapoints()
            if self._registered is False:
                self._registered = True
            self._update_activity_timestamp()

    def _update_activity_timestamp(self):
        """Update the last activity timestamp and exit idle mode if needed."""
        current_time = time.perf_counter()
        self._last_activity_time = current_time
        if self._is_idle:
            self._is_idle = False
            log.info("Mock service exiting idle mode - activity detected")

    def _check_idle_state(self):
        """Check if the service should enter idle mode based on inactivity."""
        current_time = time.perf_counter()
        time_since_activity = current_time - self._last_activity_time
        
        if not self._is_idle and time_since_activity > self._idle_threshold:
            self._is_idle = True
            log.info("Mock service entering idle mode - no activity for %.1f seconds", time_since_activity)
        
        return self._is_idle

    def _has_active_animations(self):
        """Check if there are any active animations running."""
        for _, datapoint in self._mocked_datapoints.items():
            for behavior in datapoint.behaviors:
                action = behavior._action
                if type(action) is AnimationAction:
                    if not action._animator.is_done():
                        return True
        return False

    def main_loop(self):
        """Main execution loop which checks if behaviors shall be executed."""
        # wait for datapoints to be registered
        while not self._registered:
            time.sleep(1)

        try:
            while True:
                self.check_for_new_mocks()
                current_tick_time = time.perf_counter()
                delta_time: float = current_tick_time - self._last_tick
                
                # Check for idle state
                is_idle = self._check_idle_state()
                has_events = len(self._pending_event_list) > 0
                has_animations = self._has_active_animations()
                
                # Only execute behaviors and animations if not idle or if there's activity
                if not is_idle or has_events or has_animations:
                    if has_events or has_animations:
                        self._update_activity_timestamp()
                    
                    self._behavior_executor.execute(delta_time)

                    for _, datapoint in self._mocked_datapoints.items():
                        for behavior in datapoint.behaviors:
                            action = behavior._action
                            if type(action) is AnimationAction:
                                if not action._animator.is_done():
                                    action._animator.tick(delta_time)

                self._last_tick = time.perf_counter()

                # Use different sleep durations based on idle state
                if is_idle and not has_events and not has_animations:
                    time.sleep(self._idle_sleep_duration)
                else:
                    time.sleep(self._base_sleep_duration)
        except Exception as exception:
            log.exception(exception)

    def _on_datapoint_updated(self, datapoint: DataPoint):
        """Callback whenever the value of a datapoint datapoint changes."""
        self._update_activity_timestamp()
        self._set_datapoint(datapoint.path, datapoint.value)

    def _feed_initial_values(self):
        """Provide initial values of all mocked datapoints to data broker."""
        for mocked in self._mocked_datapoints.values():
            if mocked.datapoint.data_type is not None:
                self._set_datapoint(mocked.datapoint.path, mocked.datapoint.value)

    def _mock_update_request_handler(
        self,
        response_iter: Iterator,
        type,
    ) -> None:
        """Callback when an update event is received from data broker."""
        try:
            for updates in response_iter:
                for path, dp in updates.items():
                    if dp is not None:
                        # else it would register a new event at startup because event with value None would occur
                        if dp.value is not None:
                            raw_value = dp.value
                            self._pending_event_list.append(
                                Event(type, path, raw_value)
                            )
                            self._update_activity_timestamp()
        except Exception as e:
            log.exception(e)
            raise

    def _subscribe_to_mocked_datapoints(self):
        """Subscribe to mocked datapoints."""
        nbr_datapoints = len(_mocked_datapoints)
        log.info("Subscribing to %d mocked datapoints...", nbr_datapoints)
        log.debug(_mocked_datapoints)

        if self._mocked_datapoints:
            response_iter_target = self._client.subscribe_target_values(self._mocked_datapoints)
            response_iter_current = self._client.subscribe_current_values(self._mocked_datapoints)

            self._executor = ThreadPoolExecutor()
            self._executor.submit(self._mock_update_request_handler, response_iter_target, EVENT_KEY_ACTUATOR_TARGET)
            self._executor.submit(self._mock_update_request_handler, response_iter_current, EVENT_KEY_VALUE)

    def _set_datapoint(self, path: str, value: Any):
        """Set the value of a datapoint within databroker."""
        try:
            log.info("Feeding '%s' with value %s", path, value)
            
            # Convert array values to string format expected by kuksa_client
            if isinstance(value, list):
                # Ensure list contains proper numeric values, not strings
                converted_list = []
                for item in value:
                    if isinstance(item, str) and item.isdigit():
                        converted_list.append(int(item))
                    elif isinstance(item, str) and item.lower() in ['true', 'false']:
                        # Handle boolean strings properly
                        converted_list.append(item.lower() == 'true')
                    elif isinstance(item, str):
                        try:
                            converted_list.append(float(item))
                        except ValueError:
                            converted_list.append(item)  # Keep as string
                    else:
                        converted_list.append(item)
                
                # Convert Python list to JSON string format: [1,125] 
                import json
                formatted_value = json.dumps(converted_list, separators=(',', ':'))
            else:
                formatted_value = value
                
            self._client.set_current_values({path: Datapoint(formatted_value)})
            # remove events set through set_datapoint
            event_to_remove = None
            for event in self._pending_event_list:
                if "value" == event.name and event.path == path:
                    event_to_remove = event

            if event_to_remove is not None:
                self._pending_event_list.remove(event_to_remove)
        except grpc.RpcError as err:
            log.warning("Feeding %s failed", path, exc_info=True)
            self._connected = is_grpc_fatal_error(err)
            raise err
