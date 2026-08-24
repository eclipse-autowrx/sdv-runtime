#!/usr/bin/env python3
"""Apply bounded transient-RPC retries to velocitas-sdk 0.14.1.

The runtime intentionally restarts KUKSA Databroker after replacing its VSS
metadata. velocitas-sdk 0.14.1 immediately rethrows an in-flight UNAVAILABLE
response even though its gRPC channel reconnects shortly afterwards.

This build-time patch is deliberately fail-fast: a future SDK source change
must be reviewed instead of being patched partially or silently.
"""

from pathlib import Path

CLIENT_PATH = Path("/home/dev/python-packages/velocitas_sdk/vdb/client.py")

OLD_BLOCK = '''    async def GetDatapoints(self, datapoints: List[str]):
        try:
            response = await self._stub.GetDatapoints(
                GetDatapointsRequest(datapoints=datapoints), metadata=self._metadata
            )
            return response
        except grpc.aio.AioRpcError:  # type: ignore
            logger.exception(
                "Error occured in VehicleDataBrokerClient.GetDatapoints",
            )
            raise

    async def SetDatapoints(self, datapoints):
        try:
            response = await self._stub.SetDatapoints(
                SetDatapointsRequest(datapoints=datapoints), metadata=self._metadata
            )
            return response
        except grpc.aio.AioRpcError:  # type: ignore
            logger.exception(
                "Error occured in VehicleDataBrokerClient.SetDatapoints",
            )
            raise
'''

NEW_BLOCK = '''    async def _call_with_retry(self, method_name: str, request):
        transient_codes = {
            grpc.StatusCode.UNAVAILABLE,
            grpc.StatusCode.DEADLINE_EXCEEDED,
            grpc.StatusCode.CANCELLED,
        }
        delay = 0.25
        for attempt in range(6):
            try:
                method = getattr(self._stub, method_name)
                return await method(request, metadata=self._metadata)
            except grpc.aio.AioRpcError as error:  # type: ignore
                if error.code() not in transient_codes or attempt == 5:
                    logger.exception(
                        "VehicleDataBrokerClient.%s failed", method_name
                    )
                    raise
                logger.warning(
                    "VehicleDataBrokerClient.%s transient failure (%s); "
                    "retrying in %.2fs",
                    method_name,
                    error.code(),
                    delay,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 2.0)

    async def GetDatapoints(self, datapoints: List[str]):
        return await self._call_with_retry(
            "GetDatapoints", GetDatapointsRequest(datapoints=datapoints)
        )

    async def SetDatapoints(self, datapoints):
        return await self._call_with_retry(
            "SetDatapoints", SetDatapointsRequest(datapoints=datapoints)
        )
'''

OLD_METADATA = '''    async def GetMetadata(self, names: list):
        try:
            response = await self._stub.GetMetadata(
                GetMetadataRequest(names=names), metadata=self._metadata
            )
            return response
        except grpc.aio.AioRpcError:  # type: ignore
            logger.exception(
                "Error occured in VehicleDataBrokerClient.GetMetadata",
            )
            raise
'''

NEW_METADATA = '''    async def GetMetadata(self, names: list):
        return await self._call_with_retry(
            "GetMetadata", GetMetadataRequest(names=names)
        )
'''


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one {label} block in {CLIENT_PATH}, found {count}. "
            "Review the patch against the installed velocitas-sdk version."
        )
    return source.replace(old, new, 1)


def main() -> None:
    source = CLIENT_PATH.read_text(encoding="utf-8")
    source = replace_once(source, OLD_BLOCK, NEW_BLOCK, "datapoint RPC")
    source = replace_once(source, OLD_METADATA, NEW_METADATA, "metadata RPC")
    CLIENT_PATH.write_text(source, encoding="utf-8")
    compile(source, str(CLIENT_PATH), "exec")
    print(f"Patched transient VDB retries in {CLIENT_PATH}")


if __name__ == "__main__":
    main()

