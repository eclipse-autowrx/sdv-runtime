# SDV-Runtime User Guide

## Overview

The `sdv-runtime` Docker container provides a complete environment for Software Defined Vehicles (SDV) development and testing. It connects to [playground.digital.auto](https://playground.digital.auto) for app ideation and coding. Supports amd64 and arm64 architectures.

## Components

- Kuksa Databroker (v0.4.4)
- Vehicle Signal Specification (v4.0)
- Vehicle Model Generator (v0.7.2)
- Kuksa Syncer
- Kuksa Mock Provider
- Velocitas Python SDK (v0.14.1)
- Kit Manager
- Python 3.10

## Running the Container

Basic run:
```
docker run -d -e RUNTIME_NAME=\"MyRuntimeName\" ghcr.io/eclipse-autowrx/sdv-runtime:latest
```

Forward Kuksa port:
```
docker run -d -e RUNTIME_NAME=\"MyRuntimeName\" -p 55555:55555 ghcr.io/eclipse-autowrx/sdv-runtime:latest
```

Custom Kit Server:
```
docker run -d -e RUNTIME_NAME=\"MyRuntimeName\" -e SYNCER_SERVER_URL=\"YOUR_SERVER\" ghcr.io/eclipse-autowrx/sdv-runtime:latest
```

Local self-manager:
```
docker run -d -e RUNTIME_NAME=\"MyRuntimeName\" -e SYNCER_SERVER_URL=\"http://localhost:3090\" -p 3090:3090 ghcr.io/eclipse-autowrx/sdv-runtime:latest
```

## Usage

- Connect to playground.digital.auto using the RUNTIME_NAME.
- Use kuksa-client to interact with Databroker (if port forwarded).
- Inside the container, access tools under /home/dev/.
- Mock signals defined in /home/dev/ws/mock/signals.json.
- Run Python apps via syncer commands.

## Configuration

- **RUNTIME_NAME**: ID for playground registration.
- **SYNCER_SERVER_URL**: Kit server URL (default: https://kit.digitalauto.tech).
- **MOCK_SIGNAL**: Path to mock signals JSON.

## Interacting with Services

- Access shell: `docker exec -it <container_id> bash`
- Start services are handled by start_services.sh. 