#!/bin/sh

# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT


DISABLE_DATABROKER=${DISABLE_DATABROKER:-""}
DATABROKER_ARGS=${DATABROKER_ARGS:-""}
SYNCER_SERVER_URL=${SYNCER_SERVER_URL:-"https://kit.digitalauto.tech"}
VSS_DATA=${VSS_DATA:-""}
RUNTIME_NAME=${RUNTIME_NAME:-"VSS4.0"} # Display name on the playground
MOCK_SIGNAL=${MOCK_SIGNAL:-"/home/dev/ws/mock/signals.json"}
SITE_PACKAGES_DIR="/home/dev/python-packages"
GEN_MODEL_DIR="/home/dev/python-packages/vehicle-model-generator/gen_model"

echo "Running as user: $(id -u -n)"

mosquitto -d -c /etc/mosquitto/mosquitto-no-auth.conf

if [ -z "$DISABLE_DATABROKER" ]; then
    /app/databroker $DATABROKER_ARGS & 
fi

/home/dev/ws/kit-manager/node-km &

sleep 4 # Ensure that the kuksa databroker and mosquitto start before the syncer

#python3 /home/dev/ws/kuksa-syncer/syncer.pyc &   

python3 /home/dev/ws/kuksa-syncer/syncer.py &   

# if [ -n "$VSS_DATA" ]; then
#     cd /home/dev/python-packages/vehicle-model-generator/
#     python3 src/velocitas/model_generator/cli.py "$VSS_DATA"  -I ../vehicle_signal_specification/spec -u ../vehicle_signal_specification/spec/units.yaml 
#     echo "Generated vehicle model from custom vss.json file at $SITE_PACKAGES_DIR/vehicle"
#     rm -rf "$SITE_PACKAGES_DIR/vehicle"
#     cp -r "/home/dev/python-packages/vehicle-model-generator/gen_model/vehicle" "$SITE_PACKAGES_DIR/"
# fi

if [ -n "$MOCK_SIGNAL" ]; then
    python3 /home/dev/ws/mock/mock.py    
    python3 /home/dev/ws/mock/mockprovider.py
    echo "Created mock datapoints from input file, mock provider is now running"
fi    
 
tail -f /dev/null