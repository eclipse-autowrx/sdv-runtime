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
    && for i in 1 2 3; do apt-get update && apt-get install -y --no-install-recommends python3 mosquitto ca-certificates python-is-python3 python3-pip nano git && break || sleep 5; done \
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
    && for i in 1 2 3; do apt-get update && apt-get install -y --no-install-recommends python3 mosquitto ca-certificates python-is-python3 python3-pip nano git && break || sleep 5; done \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* 

# Python builder stage to create the package environment
FROM ubuntu:22.04 AS python-builder
ARG TARGETARCH

# Install Python and pip
RUN for i in 1 2 3; do apt-get update && apt-get install -y python3 python3-pip git build-essential && break || sleep 5; done \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements file
COPY requirements-docker.txt .

# Create target directory for packages
RUN mkdir -p /home/dev/python-packages

# Install all Python packages to the target directory
ENV PYTHONPATH="/home/dev/python-packages:${PYTHONPATH}"
RUN pip3 install --no-cache-dir --target /home/dev/python-packages -r requirements-docker.txt

# Copy VSS specification from submodule and overlay files
COPY vehicle_signal_specification ./vehicle_signal_specification
COPY overlays ./overlays
COPY units.yaml ./vehicle_signal_specification/spec/units.yaml

# Generate extended VSS JSON with overlay files
RUN cd vehicle_signal_specification/vss-tools/ \
    && pip3 install --no-deps --target /home/dev/python-packages . \
    && python3 vspec2json.py -I ../spec -u ../spec/units.yaml \
        -o /build/overlays/diagnostics_extension.vspec \
        -o /build/overlays/passenger_extension.vspec \
        -o /build/overlays/occupant_extension.vspec \
        ../spec/VehicleSignalSpecification.vspec vss.json

# Copy vehicle-model-generator submodule and generate complete models with extensions
COPY vehicle-model-generator ./vehicle-model-generator
RUN cd vehicle-model-generator/ \
    && cp -r src/velocitas/ /home/dev/python-packages/velocitas/ \
    && python3 -m velocitas.model_generator.cli /build/vehicle_signal_specification/vss-tools/vss.json \
        -I /build/vehicle_signal_specification/spec \
        -u /build/vehicle_signal_specification/spec/units.yaml \
    && mv ./gen_model/vehicle /home/dev/python-packages/

# Copy VSS and vehicle_signal_specification to the target
RUN cp -r vehicle_signal_specification /home/dev/python-packages/ \
    && cp vehicle_signal_specification/vss-tools/vss.json /home/dev/python-packages/ \
    && cp -r /home/dev/python-packages/vehicle /home/dev/python-packages/std_vehicle || true

# Now adding generic parts
FROM target-$TARGETARCH AS target
ARG TARGETARCH

# Copy Python packages from builder stage
COPY --from=python-builder --chown=dev:sdvr /home/dev/python-packages /home/dev/python-packages

# Copy other necessary files
COPY --chown=dev:sdvr --chmod=0755 data/vss-core/vss.json /home/dev/ws/vss.json
COPY --chown=dev:sdvr --chmod=0755 data/vss-core/default_vss.json /home/dev/ws/default_vss.json
COPY requirements.txt .
COPY --chown=dev:sdvr --chmod=0755 kuksa-syncer /home/dev/ws/kuksa-syncer/
COPY --chown=dev:sdvr --chmod=0755 mock /home/dev/ws/mock/
COPY mosquitto-no-auth.conf /etc/mosquitto/mosquitto-no-auth.conf
COPY --chown=dev:sdvr --chmod=0755 start_services.sh /start_services.sh

ENV PYTHONPATH="/home/dev/python-packages/:${PYTHONPATH}"

# Re-install grpcio to ensure it's built for the target platform
RUN pip3 uninstall -y grpcio && pip3 install grpcio==1.64.1
RUN pip3 install requests

# Create symlinks and move files as in original
RUN ln -s /home/dev/python-packages/velocitas_sdk /home/dev/python-packages/sdv \
    && mv /home/dev/ws/kuksa-syncer/vehicle_model_manager.py /home/dev/ws/kuksa-syncer/pkg_manager.py /home/dev/python-packages/
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
ENV RUNTIME_PREFIX="Runtime-"
EXPOSE $KUKSA_DATABROKER_PORT $KIT_MANAGER_PORT

RUN mkdir /home/dev/data
RUN chown -R dev /home/dev/data
RUN chmod -R 777 /home/dev/data

WORKDIR /home/dev/

ENTRYPOINT ["/start_services.sh"]