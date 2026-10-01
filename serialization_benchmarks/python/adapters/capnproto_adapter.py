from __future__ import annotations

from typing import Any

from capnproto import load

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
    target.timestampNs = value.timestamp_ns
    target.sequence = value.sequence
    target.x = value.x
    target.y = value.y
    target.z = value.z
    target.value = value.value
    target.valid = value.valid


def _consume_small(value: Any) -> float:
    return (
        value.timestampNs
        + value.sequence
        + value.x
        + value.y
        + value.z
        + value.value
        + int(value.valid)
    )


class CapnProtoAdapter(Adapter):
    name = "capnproto"

    def __init__(self) -> None:
        self._schemas = {
            "small_flat": load("small_flat"),
            "list_of_nested": load("list_of_nested"),
            "list_of_triply_nested": load("list_of_triply_nested"),
            "big_sensor": load("big_sensor"),
            "fixed_numeric_array": load("fixed_numeric_array"),
            "wide_flat": load("wide_flat"),
        }

    def construct_one(self, archetype: Archetype, logical: LogicalData) -> Any:
        schema = self._schemas[archetype]
        if archetype == "small_flat":
            assert isinstance(logical, SmallFlatData)
            message = schema.SmallFlat.new_message()
            _set_small(message, logical)
            return message

        if archetype == "list_of_nested":
            assert isinstance(logical, ListOfNestedData)
            message = schema.ListOfNested.new_message(
                timestampNs=logical.timestamp_ns,
                sequence=logical.sequence,
            )
            samples = message.init("samples", len(logical.samples))
            for target, value in zip(samples, logical.samples):
                _set_small(target, value)
            return message

        if archetype == "list_of_triply_nested":
            assert isinstance(logical, ListOfTriplyNestedData)
            message = schema.ListOfTriplyNested.new_message(
                timestampNs=logical.timestamp_ns,
                sequence=logical.sequence,
            )
            level_1_items = message.init("items", len(logical.items))
            for level_1, level_1_values in zip(level_1_items, logical.items):
                level_2_items = level_1.init("items", len(level_1_values))
                for level_2, level_2_values in zip(level_2_items, level_1_values):
                    leaves = level_2.init("items", len(level_2_values))
                    for target, value in zip(leaves, level_2_values):
                        _set_small(target, value)
            return message

        if archetype == "big_sensor":
            assert isinstance(logical, BigSensorData)
            return schema.BigSensor.new_message(
                timestampNs=logical.timestamp_ns,
                sequence=logical.sequence,
                width=logical.width,
                height=logical.height,
                rowStride=logical.row_stride,
                encoding=logical.encoding,
                data=logical.data,
            )

        if archetype == "fixed_numeric_array":
            assert isinstance(logical, FixedNumericArrayData)
            message = schema.FixedNumericArray.new_message(
                timestampNs=logical.timestamp_ns,
                sequence=logical.sequence,
            )
            values = message.init("values", len(logical.values))
            for index, value in enumerate(logical.values):
                values[index] = value
            return message

        assert isinstance(logical, WideFlatData)
        message = schema.WideFlat.new_message(
            timestampNs=logical.timestamp_ns,
            sequence=logical.sequence,
        )
        for index, value in enumerate(logical.channels):
            setattr(message, f"channel{index:02d}", value)
        return message

    def serialize_one(self, archetype: Archetype, value: Any) -> bytes:
        del archetype
        payload = value.to_bytes()
        value.clear_write_flag()
        return payload

    def deserialize_one(self, archetype: Archetype, payload: bytes) -> float:
        schema = self._schemas[archetype]
        struct_name = {
            "small_flat": "SmallFlat",
            "list_of_nested": "ListOfNested",
            "list_of_triply_nested": "ListOfTriplyNested",
            "big_sensor": "BigSensor",
            "fixed_numeric_array": "FixedNumericArray",
            "wide_flat": "WideFlat",
        }[archetype]
        struct_type = getattr(schema, struct_name)
        with struct_type.from_bytes(payload) as value:
            if archetype == "small_flat":
                return _consume_small(value)
            if archetype == "list_of_nested":
                return value.timestampNs + value.sequence + sum(
                    _consume_small(item) for item in value.samples
                )
            if archetype == "list_of_triply_nested":
                return value.timestampNs + value.sequence + sum(
                    _consume_small(leaf)
                    for level_1 in value.items
                    for level_2 in level_1.items
                    for leaf in level_2.items
                )
            if archetype == "big_sensor":
                materialized = bytes(value.data)
                return (
                    value.timestampNs
                    + value.sequence
                    + value.width
                    + value.height
                    + value.rowStride
                    + len(value.encoding)
                    + len(materialized)
                )
            if archetype == "fixed_numeric_array":
                return value.timestampNs + value.sequence + sum(value.values)
            return value.timestampNs + value.sequence + sum(
                getattr(value, f"channel{index:02d}") for index in range(32)
            )
