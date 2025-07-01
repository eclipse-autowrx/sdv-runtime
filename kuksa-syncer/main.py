# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

import time
import asyncio
import signal

from sdv.vdb.reply import DataPointReply
from sdv.vehicle_app import VehicleApp
from vehicle import FarmMachinery, vehicle

print("002")

class TestApp(VehicleApp):

    def __init__(self, vehicle_client: FarmMachinery):
        super().__init__()
        self.FarmMachinery = vehicle_client

    async def on_start(self):
        print("01")
        current = (await self.FarmMachinery.Diagnostics.Power.Current.get()).value
        print("current", current)

async def main():
    vehicle_app = TestApp(vehicle)
    await vehicle_app.run()


LOOP = asyncio.get_event_loop()
LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
LOOP.run_until_complete(main())
LOOP.close()