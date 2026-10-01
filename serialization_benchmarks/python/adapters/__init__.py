from adapters.base import Adapter
from adapters.capnproto_adapter import CapnProtoAdapter
from adapters.ctypes_adapter import CtypesAdapter
from adapters.flatbuffers_adapter import FlatBuffersAdapter
from adapters.protobuf_adapter import ProtobufAdapter
from adapters.ros2_cdr_adapter import Ros2CdrAdapter


def create_adapters() -> dict[str, Adapter]:
    adapters: tuple[Adapter, ...] = (
        CtypesAdapter(),
        ProtobufAdapter(),
        CapnProtoAdapter(),
        FlatBuffersAdapter(),
        Ros2CdrAdapter(),
    )
    return {adapter.name: adapter for adapter in adapters}


__all__ = ["Adapter", "create_adapters"]
