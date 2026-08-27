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

log_kit_manager_container() {
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    event=$1
    shift
    echo "$ts [KitManagerContainer] [$event] pid=$$ kitImageVersion=${KIT_IMAGE_VERSION:-unknown} $*"
}

terminate_children() {
    signal=$1
    # Signal-driven shutdown defaults to 0. Natural kit-manager death passes
    # through the child's exit code so Docker restart/alert policies can see it.
    final_exit=${2:-0}
    log_kit_manager_container "CONTAINER_SIGNAL" "signal=$signal kitManagerPid=${KIT_MANAGER_PID:-} databrokerPid=${DATABROKER_PID:-} syncerPid=${SYNCER_PID:-} finalExit=$final_exit"

    if [ -n "${KIT_MANAGER_PID:-}" ] && kill -0 "$KIT_MANAGER_PID" 2>/dev/null; then
        kill "-$signal" "$KIT_MANAGER_PID" 2>/dev/null || true
    fi
    if [ -n "${DATABROKER_PID:-}" ] && kill -0 "$DATABROKER_PID" 2>/dev/null; then
        kill "-$signal" "$DATABROKER_PID" 2>/dev/null || true
    fi
    if [ -n "${SYNCER_PID:-}" ] && kill -0 "$SYNCER_PID" 2>/dev/null; then
        kill "-$signal" "$SYNCER_PID" 2>/dev/null || true
    fi
    if [ -n "${MOCK_PROVIDER_PID:-}" ] && kill -0 "$MOCK_PROVIDER_PID" 2>/dev/null; then
        kill "-$signal" "$MOCK_PROVIDER_PID" 2>/dev/null || true
    fi

    log_kit_manager_container "CONTAINER_STOPPING" "signal=$signal mockProviderPid=${MOCK_PROVIDER_PID:-}"
    if [ -n "${KIT_MANAGER_PID:-}" ]; then
        wait "$KIT_MANAGER_PID" 2>/dev/null || true
    fi
    if [ -n "${DATABROKER_PID:-}" ] && kill -0 "$DATABROKER_PID" 2>/dev/null; then
        kill -KILL "$DATABROKER_PID" 2>/dev/null || true
    fi
    if [ -n "${SYNCER_PID:-}" ] && kill -0 "$SYNCER_PID" 2>/dev/null; then
        kill -KILL "$SYNCER_PID" 2>/dev/null || true
    fi
    if [ -n "${MOCK_PROVIDER_PID:-}" ] && kill -0 "$MOCK_PROVIDER_PID" 2>/dev/null; then
        kill -KILL "$MOCK_PROVIDER_PID" 2>/dev/null || true
    fi
    log_kit_manager_container "CONTAINER_EXIT" "signal=$signal finalExit=$final_exit"
    exit "$final_exit"
}

trap 'terminate_children TERM' TERM
trap 'terminate_children INT' INT
trap 'terminate_children HUP' HUP
trap 'terminate_children QUIT' QUIT

log_kit_manager_container "CONTAINER_STARTING" "user=$(id -u -n)"

mosquitto -d -c /etc/mosquitto/mosquitto-no-auth.conf

if [ -z "$DISABLE_DATABROKER" ]; then
    /app/databroker $DATABROKER_ARGS & 
    DATABROKER_PID=$!
fi

node /home/dev/ws/kit-manager/src/index.js &
KIT_MANAGER_PID=$!
log_kit_manager_container "KIT_MANAGER_CHILD_STARTED" "kitManagerPid=$KIT_MANAGER_PID"

sleep 4 # Ensure that the kuksa databroker and mosquitto start before the syncer

#python3 /home/dev/ws/kuksa-syncer/syncer.pyc &   

python3 /home/dev/ws/kuksa-syncer/syncer.py &   
SYNCER_PID=$!

# if [ -n "$VSS_DATA" ]; then
#     cd /home/dev/python-packages/vehicle-model-generator/
#     python3 src/velocitas/model_generator/cli.py "$VSS_DATA"  -I ../vehicle_signal_specification/spec -u ../vehicle_signal_specification/spec/units.yaml 
#     echo "Generated vehicle model from custom vss.json file at $SITE_PACKAGES_DIR/vehicle"
#     rm -rf "$SITE_PACKAGES_DIR/vehicle"
#     cp -r "/home/dev/python-packages/vehicle-model-generator/gen_model/vehicle" "$SITE_PACKAGES_DIR/"
# fi

if [ -n "$MOCK_SIGNAL" ]; then
    python3 /home/dev/ws/mock/mock.py    
    python3 /home/dev/ws/mock/mockprovider.py &
    MOCK_PROVIDER_PID=$!
    log_kit_manager_container "MOCK_PROVIDER_CHILD_STARTED" "mockProviderPid=$MOCK_PROVIDER_PID"
    echo "Created mock datapoints from input file, mock provider is now running"
fi    
 
# Poll instead of blocking forever in `wait`. Some /bin/sh implementations only
# process traps after wait returns, which can hide shutdown logs during
# `docker compose stop` and lead Docker to escalate to SIGKILL / exit 137.
while kill -0 "$KIT_MANAGER_PID" 2>/dev/null; do
    sleep 1
done
wait "$KIT_MANAGER_PID" 2>/dev/null
KIT_MANAGER_EXIT_CODE=$?
log_kit_manager_container "KIT_MANAGER_CHILD_EXITED" "kitManagerPid=$KIT_MANAGER_PID exitCode=$KIT_MANAGER_EXIT_CODE"
terminate_children TERM "$KIT_MANAGER_EXIT_CODE"
