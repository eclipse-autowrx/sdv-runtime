# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

# ********************************************************************************/

from typing import Any, List, NamedTuple

from kuksa_client.grpc import VSSClient


class Event(NamedTuple):
    """Structure for holding event data."""

    name: str
    path: str
    value: Any


class ExecutionContext(NamedTuple):
    """Context in which behaviors are executed"""

    calling_signal_path: str
    pending_event_list: List[Event]
    delta_time: float
    client: VSSClient
