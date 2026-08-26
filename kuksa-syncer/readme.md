# Start Data broker

## Start with port
```bash
docker run --rm -it -p 55555:55555 ghcr.io/eclipse-kuksa/kuksa-databroker:main --insecure
```

## Start with docker network

```bash
docker network create kuksa
```

```bash
docker run -it --rm --name Server --network kuksa ghcr.io/eclipse-kuksa/kuksa-databroker:main --insecure
```


### Test with docker cli

```bash
docker run -it --rm --network kuksa ghcr.io/eclipse-kuksa/kuksa-databroker-cli:main --server Server:55555
```



# Message from server to RT

```json
{
    "request_from": "omSQcmWWkuqzh2kuAwGc", 
    "cmd": "run_python_app", 
    "to_kit_id": "RunTime-arm64-001", 
    "data": {
        "code": "from sdv_model import Vehicle\nimport plugins\nfrom browser import aio\n\nvehicle = Vehicle()"
    }
}
```


# Support command
List all support cmd below as a list
- deploy_request
- run_python_app
- stop_python_app
- run_bin_app
- subscribe_apis
- unsubscribe_apis
- list_mock_signal
- write_signals_value
- reset_signals_value
- generate_vehicle_model
- revert_vehicle_model
- list_python_packages
- install_python_packages
- get-runtime-info
- read-file
- write-file





## CMD: deploy_request
```json
{
    "cmd": "deploy_request",
    "prototype": {},
    "username" : "".
    ...
}
```

## CMD: subscribe_apis
```json
{
    ...
    "cmd": "subscribe_apis",
    "apis": [
        "Vehicle.ABC",
        "Vehicle.X.Y.Z"
    ]
}
```

## CMD: unsubscribe_apis
```json
{
    ...
    "request_from": "client-id",
    "cmd": "unsubscribe_apis"
}
```

## CMD: list_mock_signal
```json
{
    ...
    "request_from": "client-id",
    "cmd": "list_mock_signal"
}
```

## CMD: set_mock_signals
```json
{
    ...
    "request_from": "client-id",
    "cmd": "set_mock_signals",
    "data": {}
}
```

## CMD: write_signals_value

```json
{
    ...
    "request_from": "client-id",
    "cmd": "write_signals_value",
    "data": {}
}
```

## CMD: reset_signals_value
```json
{
    ...
    "request_from": "client-id",
    "cmd": "reset_signals_value"
}
```

## CMD: generate_vehicle_model
```json
{
    ...
    "request_from": "client-id",
    "cmd": "generate_vehicle_model"
}
```

## CMD: revert_vehicle_model
```json
{
    ...
    "request_from": "client-id",
    "cmd": "revert_vehicle_model"
}
```

## CMD: list_python_packages

```json
{
    ...
    "request_from": "client-id",
    "cmd": "list_python_packages"
}
```


## CMD: install_python_packages

```json
{
    ...
    "request_from": "client-id",
    "cmd": "install_python_packages"
}
```


## CMD: run_python_app
```json
{
    ...
    "request_from": "client-id",
    "cmd": "run_python_app",
    "data": {
        "code": "python code",
    },
    "usedAPIs": []
}
```

## CMD: run_bin_app
```json
{
    ...
    "request_from": "client-id",
    "cmd": "run_bin_app",
    "data": "app_name",
    "usedAPIs": []
}
```

## CMD: stop_python_app
```json
{
    ...
    "request_from": "client-id",
    "cmd": "stop_python_app"
}
```

## CMD: read-file

Read a file from the kit filesystem. Only paths under `/app/remote_access/`
are allowed (`signal-config.json`, `vss.json`). Requests are resolved with
`realpath` confinement; path traversal and paths outside that tree are rejected
with `has_error: true`. `/app/remote_access/vss.json` may be a symlink to the
databroker metadata file and remains allowed. Prefer top-level `file_path`;
legacy `data` as a path string or `{ "path": "..." }` is still accepted.

```json
{
    "request_from": "client-id",
    "cmd": "read-file",
    "data": "",
    "file_path": "/app/remote_access/vss.json",
    "prototype": { "name": "no-name", "id": "no-id" },
    "username": "no"
}
```

Reply (`read-file`):

```json
{
    "kit_id": "Runtime-...",
    "request_from": "client-id",
    "cmd": "read-file",
    "result": "<file-body>",
    "has_error": false,
    "file_path": "/app/remote_access/vss.json"
}
```

## CMD: write-file

Write a file on the kit. Same `/app/remote_access/` confinement as `read-file`.
Prefer top-level `file_path` / `file_content`; legacy `data: { "path", "content" }`
is still accepted. Content is normalized to LF with trailing newlines stripped.
`/app/remote_access/vss.json` is a symlink to `/home/dev/ws/vss.json` so writes
stay aligned with the databroker metadata file.

```json
{
    "request_from": "client-id",
    "cmd": "write-file",
    "data": "",
    "file_path": "/app/remote_access/signal-config.json",
    "file_content": "{}",
    "prototype": { "name": "no-name", "id": "no-id" },
    "username": "no"
}
```

Reply:

```json
{
    "kit_id": "Runtime-...",
    "request_from": "client-id",
    "cmd": "write-file",
    "result": "Success",
    "has_error": false,
    "file_path": "/app/remote_access/signal-config.json",
    "data": {
        "path": "/app/remote_access/signal-config.json",
        "bytes_written": 2
    }
}
```
