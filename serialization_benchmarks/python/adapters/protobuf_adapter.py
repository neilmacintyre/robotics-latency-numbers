from __future__ import annotations

from typing import Any

import big_sensor_pb2
import fixed_numeric_array_pb2
import list_of_nested_pb2
import list_of_triply_nested_pb2
import small_flat_pb2
import wide_flat_pb2

from adapters.base import Adapter
from models import Archetype
from models import BigSensorData
from models import FixedNumericArrayData
from models import ListOfNestedData
from models import ListOfTriplyNestedData
from models import LogicalData
from models import SmallFlatData
from models import WideFlatData


def _set_small(target: Any, value: SmallFlatData) -> None:
    target.timestamp_ns = value.timestamp_ns
    target.sequence = value.sequence
    target.x = value.x
    target.y = value.y
    target.z = value.z
    target.value = value.value
    target.valid = value.valid


def _consume_small(value: Any) -> float:
    return (
        value.timestamp_ns
        + value.sequence
        + value.x
        + value.y
        + value.z
        + value.value
        + int(value.valid)
    )


class ProtobufAdapter(Adapter):
    name = "protobuf"

    _classes = {
        "small_flat": small_flat_pb2.SmallFlat,
        "list_of_nested": list_of_nested_pb2.ListOfNested,
        "list_of_triply_nested": list_of_triply_nested_pb2.ListOfTriplyNested,
        "big_sensor": big_sensor_pb2.BigSensor,
        "fixed_numeric_array": fixed_numeric_array_pb2.FixedNumericArray,
        "wide_flat": wide_flat_pb2.WideFlat,
    }

    def construct_one(self, archetype: Archetype, logical: LogicalData) -> Any:
        if archetype == "small_flat":
            assert isinstance(logical, SmallFlatData)
            message = small_flat_pb2.SmallFlat()
            _set_small(message, logical)
            return message

        if archetype == "list_of_nested":
            assert isinstance(logical, ListOfNestedData)
            message = list_of_nested_pb2.ListOfNested(
                timestamp_ns=logical.timestamp_ns,
                sequence=logical.sequence,
            )
            for value in logical.samples:
                _set_small(message.samples.add(), value)
            return message

        if archetype == "list_of_triply_nested":
            assert isinstance(logical, ListOfTriplyNestedData)
            message = list_of_triply_nested_pb2.ListOfTriplyNested(
                timestamp_ns=logical.timestamp_ns,
                sequence=logical.sequence,
            )
            for level_1_values in logical.items:
                level_1 = message.items.add()
                for level_2_values in level_1_values:
                    level_2 = level_1.items.add()
                    for value in level_2_values:
                        _set_small(level_2.items.add(), value)
            return message

        if archetype == "big_sensor":
            assert isinstance(logical, BigSensorData)
            return big_sensor_pb2.BigSensor(
                timestamp_ns=logical.timestamp_ns,
                sequence=logical.sequence,
                width=logical.width,
                height=logical.height,
                row_stride=logical.row_stride,
                encoding=logical.encoding,
                data=logical.data,
            )

        if archetype == "fixed_numeric_array":
            assert isinstance(logical, FixedNumericArrayData)
            return fixed_numeric_array_pb2.FixedNumericArray(
                timestamp_ns=logical.timestamp_ns,
                sequence=logical.sequence,
                values=logical.values,
            )

        assert isinstance(logical, WideFlatData)
        message = wide_flat_pb2.WideFlat(
            timestamp_ns=logical.timestamp_ns,
            sequence=logical.sequence,
        )
        for index, value in enumerate(logical.channels):
            setattr(message, f"channel_{index:02d}", value)
        return message

    def serialize_one(self, archetype: Archetype, value: Any) -> bytes:
        del archetype
        return value.SerializeToString()

    def deserialize_one(self, archetype: Archetype, payload: bytes) -> float:
        value = self._classes[archetype].FromString(payload)
        if archetype == "small_flat":
            return _consume_small(value)
        if archetype == "list_of_nested":
            return value.timestamp_ns + value.sequence + sum(
                _consume_small(item) for item in value.samples
            )
        if archetype == "list_of_triply_nested":
            return value.timestamp_ns + value.sequence + sum(
                _consume_small(leaf)
                for level_1 in value.items
                for level_2 in level_1.items
                for leaf in level_2.items
            )
        if archetype == "big_sensor":
            materialized = bytes(value.data)
            return (
                value.timestamp_ns
                + value.sequence
                + value.width
                + value.height
                + value.row_stride
                + len(value.encoding)
                + len(materialized)
            )
        if archetype == "fixed_numeric_array":
            return value.timestamp_ns + value.sequence + sum(value.values)
        return value.timestamp_ns + value.sequence + sum(
            getattr(value, f"channel_{index:02d}") for index in range(32)
        )
