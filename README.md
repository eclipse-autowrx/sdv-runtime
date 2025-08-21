# Introduction
Want to try out SDV (Software Defined Vehicles) without installing lots of things? The sdv-runtime Docker container has everything you need to run your QM apps. It's made for people who are new to SDV and want to learn and practice without a complicated setup.
The `sdv-runtime` connects natively with [playground.digital.auto](https://playground.digital.auto) where you can ideation, coding and present your automotive feature.

Since it is a docker container, it can run on cloud, your PC or even on rapsberry pi. It supports arm64 and arm64.

### Components inside the Docker container
- [Kuksa Databroker](https://github.com/eclipse-kuksa/kuksa-databroker/tree/0.4.4) - `0.4.4`
- [Vehicle Signal Specification](https://github.com/COVESA/vss-tools/tree/v4.0) - `4.0`
- [vehicle-model-generator](https://github.com/eclipse-velocitas/vehicle-model-generator/tree/v0.7.2) - `0.7.2`
- [Kuksa Syncer](kuksa-syncer/)
- [Kuksa Mock Provider](https://github.com/eclipse-kuksa/kuksa-mock-provider) (with modification to the source code)
- [Velocitas Python SDK](https://github.com/eclipse-velocitas/vehicle-app-python-sdk/tree/v0.14.1) - `0.14.1`
- [Kit Manager](kit-manager/)
- [Python](https://www.python.org/downloads/release/python-3100/) - `3.10`

When you run this Docker container, all the tools mentioned above will be ready to use, and you will be connected to the playground natively.



# How to run a runtime

```
docker run -d -e RUNTIME_NAME="MyRuntimeName" ghcr.io/eclipse-autowrx/sdv-runtime:latest

# With custom prefix
docker run -d -e RUNTIME_PREFIX="Kit-" -e RUNTIME_NAME="MyRuntimeName" ghcr.io/eclipse-autowrx/sdv-runtime:latest
```

Video instruction: [https://youtu.be/HQrsGY7XLU4](https://youtu.be/HQrsGY7XLU4)

### Arguments for setting runtime name
`$RUNTIME_NAME`: this is the ID to add your runtime to playground.digital.auto.
`$RUNTIME_PREFIX`: (Optional) Custom prefix for the runtime ID. Default is "Runtime-". Set to empty string for no prefix.

### Forward Kuksa port
To use `kuksa-client` to interact with the data broker from outside the container, add port forwarding to the run command like this:

```
docker run -d -e RUNTIME_NAME="MyRuntimeName" -p 55555:55555 ghcr.io/eclipse-autowrx/sdv-runtime:latest
```


### Arguments for Kit Server URL `$SYNCER_SERVER_URL`

Default value is https://kit.digitalauto.tech. Your can change it to another runtime manager server

```
docker run -d -e RUNTIME_NAME="MyRuntimeName" -e SYNCER_SERVER_URL="YOUR_SERVER" ghcr.io/eclipse-autowrx/sdv-runtime:latest
```

- Run your runtime with the local self manager. In this case everything stay in localhost, no external connection.
```
docker run -d -e RUNTIME_NAME="MyRuntimeName" -e SYNCER_SERVER_URL="http://localhost:3090" -p 3090:3090 ghcr.io/eclipse-autowrx/sdv-runtime:latest
```



# How to build docker image

> Info: Instructions below are for setting up the environment *from scratch* in a CI/CD pipeline. If you only want to build and test the Docker image, go to [Build and push Docker image](#build-and-push-docker-image).

All of these has been included in the Dockerfile. If you want to understand what's going on inside, read more at [dockerfile-explained](doc/dockerfile-explained.md)

## Build and push Docker image

### Multi-architecture build

Using the BuildKit to build multi-architecture Docker image requires an output, it can be either compressed into a local tar ball or push to a container registry. For unknown reasons, the local option doesn't work so we're stuck with the `--push` option at the moment.

```shell
docker buildx create --driver docker-container --driver-opt network=host --driver-opt env.http_proxy=$https_proxy --driver-opt env.https_proxy=$https_proxy --name mybuilder --platform "linux/amd64,linux/arm64" default

docker buildx use mybuilder

docker buildx build --push --platform linux/amd64,linux/arm64 -t eclipse-autowrx/sdv-runtime:latest -f Dockerfile .
```

If you're outside of Bosch's enterprise network, you can skip the `http_proxy https_proxy` driver option. Otherwise, make sure you set up your local proxy beforehand.

### Mono-architecture build

For mono-architecture image build, you can use the default BuildKit in Docker and this option also let us build locally without pushing to a remote registry.

```shell
docker buildx use default # You can use 'docker buildx ls' to check the name beforehand

docker buildx build --platform linux/amd64 -t sdv-runtime:latest -f Dockerfile .
```



## FOR LOCAL DEV TEST

### Create a local image

```shell
docker buildx build --platform linux/amd64 -t local001 -f Dockerfile .
```

### Run local image
```shell
docker run -d -e RUNTIME_NAME="bbb" -p 55555:55555 docker.io/library/local001

# with mount point
docker run -d -e RUNTIME_NAME="bbb" -v /home/nhan/dev/tmp:/home/dev/data -p 55555:55555 docker.io/library/local001

# access docker bash
docker exec -it <container_name_or_id> bash
```