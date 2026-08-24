# This is for SDV-Runtime running with VSS 4.0

# ---------------------------------------------------------------------------
# Build-time metadata. Pass at build time, e.g.:
#   docker buildx build \
#       --build-arg IMAGE_VERSION=$(git describe --tags --always) \
#       --build-arg VCS_REF=$(git rev-parse HEAD) \
#       --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
#       -t sdv-runtime:$(git describe --tags --always) .
# ---------------------------------------------------------------------------
ARG IMAGE_VERSION="dev"
ARG VCS_REF="unknown"
ARG BUILD_DATE="1970-01-01T00:00:00Z"
# Fixed UID/GID for the runtime user — makes bind-mount permissions predictable.
ARG DEV_UID=10001
ARG DEV_GID=10001

# Different targets need different base images, so prepare aliases here

# AMD is a statically linked MUSL build
FROM ubuntu:22.04 AS target-amd64
ARG DEV_UID
ARG DEV_GID
ENV BUILDTARGET="x86_64-unknown-linux-musl"
COPY --chmod=0755 bin/amd64/databroker-amd64 /app/databroker
COPY --chmod=0755 bin/amd64/node-km-x64 /home/dev/ws/kit-manager/node-km

# Retry apt with a bounded backoff; DO NOT swallow the final failure.
# `nano` was intentionally removed (unnecessary attack surface). `curl` is
# kept for HEALTHCHECK and any user apps that need it.
RUN groupadd -r -g "${DEV_GID}" sdvr \
    && useradd -r -u "${DEV_UID}" -g sdvr -m -d /home/dev dev \
    && chown -R dev:sdvr /app/databroker \
    && chown -R dev:sdvr /home/dev/ && chmod -R u+w /home/dev/ \
    && ( i=0; until apt-get update && apt-get install -y --no-install-recommends \
            python3 mosquitto ca-certificates python-is-python3 python3-pip \
            git curl; \
        do i=$((i+1)); [ $i -ge 3 ] && exit 1; sleep 5; done ) \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ARM64 is a statically linked GRPC build
FROM ubuntu:22.04 AS target-arm64
ARG DEV_UID
ARG DEV_GID
ENV BUILDTARGET="aarch64-unknown-linux-musl"
COPY --chmod=0755 bin/arm64/databroker-arm64 /app/databroker
COPY --chmod=0755 bin/arm64/node-km-arm64 /home/dev/ws/kit-manager/node-km

# Retry apt with a bounded backoff; DO NOT swallow the final failure.
RUN groupadd -r -g "${DEV_GID}" sdvr \
    && useradd -r -u "${DEV_UID}" -g sdvr -m -d /home/dev dev \
    && chown -R dev:sdvr /app/databroker \
    && chown -R dev:sdvr /home/dev/ && chmod -R u+w /home/dev/ \
    && ( i=0; until apt-get update && apt-get install -y --no-install-recommends \
            python3 mosquitto ca-certificates python-is-python3 python3-pip \
            git curl; \
        do i=$((i+1)); [ $i -ge 3 ] && exit 1; sleep 5; done ) \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Python builder stage to create the package environment
FROM ubuntu:22.04 AS python-builder
ARG TARGETARCH

# Install Python and pip (retry with bounded backoff, fail hard on exhaustion)
RUN ( i=0; until apt-get update && apt-get install -y --no-install-recommends \
            python3 python3-pip git build-essential; \
        do i=$((i+1)); [ $i -ge 3 ] && exit 1; sleep 5; done ) \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements file
COPY requirements-docker.txt .
COPY scripts/patch_velocitas_sdk_vdb.py /build/patch_velocitas_sdk_vdb.py

# Create target directory for packages
RUN mkdir -p /home/dev/python-packages

# Install all Python packages to the target directory
ENV PYTHONPATH="/home/dev/python-packages:${PYTHONPATH}"
RUN pip3 install --no-cache-dir --target /home/dev/python-packages -r requirements-docker.txt \
    && python3 /build/patch_velocitas_sdk_vdb.py

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
# Re-declare metadata ARGs for this stage (ARGs don't cross FROM boundaries).
ARG IMAGE_VERSION
ARG VCS_REF
ARG BUILD_DATE

# ---------------------------------------------------------------------------
# OCI image labels — makes `docker inspect`, registries, SBOM tools and
# Kubernetes admission controllers able to identify the image.
# ---------------------------------------------------------------------------
LABEL org.opencontainers.image.title="sdv-runtime" \
      org.opencontainers.image.description="SDV-Runtime: KUKSA databroker, kit-manager, kuksa-syncer, mock provider bundled for the digital.auto playground" \
      org.opencontainers.image.version="${IMAGE_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="https://github.com/eclipse-autowrx/sdv-runtime" \
      org.opencontainers.image.vendor="Microsoft Foundation" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.name="docker.io/library/ubuntu:22.04"

# Copy Python packages from builder stage
COPY --from=python-builder --chown=dev:sdvr /home/dev/python-packages /home/dev/python-packages

# Data files stay 0644; only scripts/binaries get exec.
COPY --chown=dev:sdvr --chmod=0644 data/vss-core/vss.json /home/dev/ws/vss.json
COPY --chown=dev:sdvr --chmod=0644 data/vss-core/default_vss.json /home/dev/ws/default_vss.json
COPY --chown=dev:sdvr --chmod=0755 kuksa-syncer /home/dev/ws/kuksa-syncer/
COPY --chown=dev:sdvr --chmod=0755 mock /home/dev/ws/mock/
COPY --chmod=0644 mosquitto-no-auth.conf /etc/mosquitto/mosquitto-no-auth.conf
COPY --chown=dev:sdvr --chmod=0755 start_services.sh /start_services.sh

ENV PYTHONPATH="/home/dev/python-packages/:${PYTHONPATH}"

# Re-install grpcio for the target platform (+ pin `requests`). Combined into
# one RUN with --no-cache-dir to keep image size down.
RUN pip3 uninstall -y grpcio || true \
    && pip3 install --no-cache-dir --target /home/dev/python-packages \
            grpcio==1.64.1 requests==2.32.3

# Create the SDK compatibility symlink for deployed user apps that
# `from sdv.vehicle_app import ...`.
#
# NOTE: the historical `mv` of pkg_manager.py / vehicle_model_manager.py into
# python-packages was REMOVED — those modules do `from config import CONFIG`
# and `from logger import get_logger`, which only resolve when they sit next
# to their siblings under /home/dev/ws/kuksa-syncer/.
RUN ln -s /home/dev/python-packages/velocitas_sdk /home/dev/python-packages/sdv

# Runtime data directory. Owner rwx + group rx; NEVER world-writable.
RUN mkdir -p /home/dev/data \
    && chown -R dev:sdvr /home/dev/data \
    && chmod -R 0750 /home/dev/data

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

# ---------------------------------------------------------------------------
# Health check. Kit-Manager exposes /health on $KIT_MANAGER_PORT; if that
# responds 2xx the whole stack is considered up.
# --start-period gives services time to boot (kuksa-syncer waits 4s in
# start_services.sh, and databroker + node-km take a moment to bind).
# ---------------------------------------------------------------------------

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${KIT_MANAGER_PORT}/listAllKits" >/dev/null \
    && pgrep -f "python3 /home/dev/ws/kuksa-syncer/syncer.py" >/dev/null \
    || exit 1


WORKDIR /home/dev/

ENTRYPOINT ["/start_services.sh"]