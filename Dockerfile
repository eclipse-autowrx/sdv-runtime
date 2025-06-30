# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

# This is for SDV-Runtime running with VSS 4.0

# Different targets need different base images, so prepare aliases here

# AMD is a statically linked MUSL build
FROM ubuntu:22.04 AS target-amd64
ENV BUILDTARGET="x86_64-unknown-linux-musl"
COPY --chmod=0755 bin/amd64/databroker-amd64 /app/databroker
COPY --chmod=0755 bin/amd64/node-km-x64 /home/dev/ws/kit-manager/node-km


RUN groupadd -r sdvr && useradd -r -g sdvr dev \
    && chown -R dev:sdvr /app/databroker \
    && chown -R dev:sdvr /home/dev/ && chmod -R u+w /home/dev/ \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3 mosquitto \
    ca-certificates python-is-python3 python3-pip nano \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ARM64 is a statically linked GRPC build
FROM ubuntu:22.04 AS target-arm64
ENV BUILDTARGET="aarch64-unknown-linux-musl"
COPY --chmod=0755 bin/arm64/databroker-arm64 /app/databroker
COPY --chmod=0755 bin/arm64/node-km-arm64 /home/dev/ws/kit-manager/node-km


RUN groupadd -r sdvr && useradd -r -g sdvr dev \
    && chown -R dev:sdvr /app/databroker \
    && chown -R dev:sdvr /home/dev/ && chmod -R u+w /home/dev/ \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3 mosquitto \
    ca-certificates python-is-python3 python3-pip nano \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* 


# Now adding generic parts
FROM target-$TARGETARCH AS target
ARG TARGETARCH

COPY --chown=dev:sdvr --chmod=0755 data/vss-core/vss.json /home/dev/ws/vss.json
COPY --chown=dev:sdvr --chmod=0755 data/vss-core/default_vss.json /home/dev/ws/default_vss.json
COPY requirements.txt .
COPY --chown=dev:sdvr --chmod=0755 data/python-packages /home/dev/python-packages
COPY --chown=dev:sdvr --chmod=0755 kuksa-syncer /home/dev/ws/kuksa-syncer/
COPY --chown=dev:sdvr --chmod=0755 mock /home/dev/ws/mock/
COPY mosquitto-no-auth.conf /etc/mosquitto/mosquitto-no-auth.conf
COPY --chown=dev:sdvr --chmod=0755 start_services.sh /start_services.sh

ENV PYTHONPATH="/home/dev/python-packages/:${PYTHONPATH}"
RUN pip uninstall -y grpcio && pip install grpcio
RUN pip install requests

RUN ln -s /home/dev/python-packages/velocitas_sdk /home/dev/python-packages/sdv \
    && mv /home/dev/ws/kuksa-syncer/vehicle_model_manager.py /home/dev/ws/kuksa-syncer/pkg_manager.py home/dev/python-packages/
    #&& python -m py_compile /home/dev/ws/kuksa-syncer/syncer.py \
    #&& mv /home/dev/ws/kuksa-syncer/__pycache__/syncer.cpython-310.pyc /home/dev/ws/kuksa-syncer/syncer.pyc \
    #&& find /home/dev/ws/kuksa-syncer/ -mindepth 1 ! -name 'syncer.pyc' ! -name 'subpiper' ! -path '/home/dev/ws/kuksa-syncer/subpiper/*' -delete

USER dev

ENV ENVIRONMENT="prototype"
ENV ARCH=$TARGETARCH
ENV USERNAME="dev"
ENV KUKSA_DATABROKER_ADDR=0.0.0.0
ENV KUKSA_DATABROKER_PORT=55555
ENV KIT_MANAGER_PORT=3090
ENV KUKSA_DATABROKER_METADATA_FILE=/home/dev/ws/vss.json
EXPOSE $KUKSA_DATABROKER_PORT $KIT_MANAGER_PORT

RUN mkdir /home/dev/data
RUN chown -R dev /home/dev/data
RUN chmod -R 777 /home/dev/data

WORKDIR /home/dev/

ENTRYPOINT ["/start_services.sh"]
