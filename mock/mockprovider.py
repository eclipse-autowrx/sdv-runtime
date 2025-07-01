# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

# ********************************************************************************/

import asyncio
import logging
import os
import signal
import sys
import threading
from mockservice import MockService

SERVICE_NAME = "mock_provider"

log = logging.getLogger(SERVICE_NAME)
log.setLevel(logging.INFO)

event = threading.Event()

# Set the log level to suppress log messages because we call connect/disconnect of client quite often
logging.getLogger("kuksa_client").setLevel(logging.INFO)

# Mock Service bind "host:port"
MOCK_ADDRESS = os.getenv("MOCK_ADDR", "127.0.0.1:50053")
VDB_ADDRESS = os.getenv("VDB_ADDRESS", "127.0.0.1:55555")


async def main():
    """Main function"""
    mock_service = MockService(MOCK_ADDRESS, VDB_ADDRESS)
    mock_service.main_loop()


if __name__ == "__main__":
    pid = os.getpid()
    with open("/home/dev/mockprovider.pid", "w") as f:
        f.write(str(pid))
    logging.basicConfig(level=logging.INFO)
    log.setLevel(logging.DEBUG)
    LOOP = asyncio.get_event_loop()
    LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
    LOOP.run_until_complete(main())
    LOOP.close()
