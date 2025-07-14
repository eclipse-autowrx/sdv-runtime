# SDV-Runtime Developer Guide

## Overview

The `sdv-runtime` project provides a Docker container for Software Defined Vehicles (SDV) development. It includes tools like Kuksa Databroker, Vehicle Signal Specification (VSS), Kuksa Syncer, Mock Provider, Velocitas Python SDK, and Kit Manager. This guide is for developers maintaining and contributing to the project.

## Project Structure

- **bin/**: Contains pre-built binaries for amd64 and arm64 architectures (e.g., databroker, node-km).
- **data/**: VSS JSON files, merged specifications, and Python packages.
- **doc/**: Documentation files.
- **Kit-Manager/**: Node.js application for managing kits, code conversion, and project generation.
- **kuksa-syncer/**: Python scripts for syncing with Kuksa, handling commands from the Kit Server, managing vehicle models, and mock signals.
- **mock/**: Mock provider for simulating vehicle signals.
- **overlays/**: Extension VSS specification files.
- **vehicle_signal_specification/** and **vehicle-model-generator/**: Submodules for VSS and model generation.
- **Dockerfile**: Builds the multi-architecture Docker image.
- **start_services.sh**: Script to start services inside the container.
- **README.md**: Basic project information and usage.

## Key Components

### Kuksa Syncer
- Located in `kuksa-syncer/`.
- Connects to a Kit Server via Socket.IO.
- Handles commands like running Python/bin apps, subscribing to APIs, managing mock signals, generating/reverting vehicle models, and installing Python packages.
- Interacts with Kuksa Databroker for signal values.

### Kit Manager
- Located in `Kit-Manager/`.
- Node.js server using Express and Socket.IO.
- Manages kit and client registrations.
- Converts playground code to Velocitas format.
- Generates projects based on code snippets and VSS payloads.

### Mock Provider
- Located in `mock/`.
- Simulates vehicle data points based on `signals.json`.
- Connects to Databroker and provides mocked behaviors and values.

### Dockerfile
- Multi-stage build for amd64 and arm64.
- Installs dependencies, clones submodules, generates VSS models.

## Building the Docker Image

### Multi-architecture Build
```
docker buildx create --driver docker-container --driver-opt network=host --name mybuilder --platform \"linux/amd64,linux/arm64\" default
docker buildx use mybuilder
docker buildx build --push --platform linux/amd64,linux/arm64 -t your-repo/sdv-runtime:latest -f Dockerfile .
```

### Mono-architecture Build
```
docker buildx use default
docker buildx build --platform linux/amd64 -t sdv-runtime:latest -f Dockerfile .
```

## Development Setup

1. Clone the repository.
2. Install dependencies:
   - Python 3.10+ for kuksa-syncer.
   - Node.js for Kit-Manager (`npm install` in Kit-Manager/).
3. For local testing, run services manually or use the start script.

## Contributing

- Follow standard Git workflow: fork, branch, PR.
- Update docs in `doc/`.
- Ensure changes work on both architectures.

## Maintenance Tips

- Update submodules (VSS, vehicle-model-generator) to latest compatible versions.
- Monitor dependencies in `requirements.txt`.
- Test Docker builds regularly. 