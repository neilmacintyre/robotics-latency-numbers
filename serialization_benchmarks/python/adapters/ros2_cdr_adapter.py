from __future__ import annotations

from typing import Any

import numpy as np
from robotics_benchmark_msgs import create_typestore

from adapters.base import Adapter
from models import Archetype
from models import BigSensorData
from models import FixedNumericArrayData
from models import ListOfNestedData
from models import ListOfTriplyNestedData
from models import LogicalData
from models import SmallFlatData
from models import WideFlatData


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


class Ros2CdrAdapter(Adapter):
    name = "ros2_cdr"

    def __init__(self) -> None:
        self._store = create_typestore()
        self._classes = {
            name: self._store.types[f"robotics_benchmark_msgs/msg/{name}"]
            for name in (
                "SmallFlat",
                "ListOfNested",
                "ListOfTriplyNested",
                "NestedListLevel1",
                "NestedListLevel2",
                "BigSensor",
                "FixedNumericArray",
                "WideFlat",
            )
        }
        self._type_names = {
            "small_flat": "robotics_benchmark_msgs/msg/SmallFlat",
            "list_of_nested": "robotics_benchmark_msgs/msg/ListOfNested",
            "list_of_triply_nested": (
                "robotics_benchmark_msgs/msg/ListOfTriplyNested"
            ),
            "big_sensor": "robotics_benchmark_msgs/msg/BigSensor",
            "fixed_numeric_array": (
                "robotics_benchmark_msgs/msg/FixedNumericArray"
            ),
            "wide_flat": "robotics_benchmark_msgs/msg/WideFlat",
        }

    def _small(self, value: SmallFlatData) -> Any:
        return self._classes["SmallFlat"](
            timestamp_ns=value.timestamp_ns,
            sequence=value.sequence,
            x=value.x,
            y=value.y,
            z=value.z,
            value=value.value,
            valid=value.valid,
        )

    def construct_one(self, archetype: Archetype, logical: LogicalData) -> Any:
        if archetype == "small_flat":
            assert isinstance(logical, SmallFlatData)
            return self._small(logical)

        if archetype == "list_of_nested":
            assert isinstance(logical, ListOfNestedData)
            return self._classes["ListOfNested"](
                timestamp_ns=logical.timestamp_ns,
                sequence=logical.sequence,
                samples=[self._small(item) for item in logical.samples],
            )

        if archetype == "list_of_triply_nested":
            assert isinstance(logical, ListOfTriplyNestedData)
            return self._classes["ListOfTriplyNested"](
                timestamp_ns=logical.timestamp_ns,
                sequence=logical.sequence,
                items=[
                    self._classes["NestedListLevel1"](
                        items=[
                            self._classes["NestedListLevel2"](
                                items=[self._small(leaf) for leaf in level_2]
                            )
                            for level_2 in level_1
                        ]
                    )
                    for level_1 in logical.items
                ],
            )

        if archetype == "big_sensor":
            assert isinstance(logical, BigSensorData)
            return self._classes["BigSensor"](
                timestamp_ns=logical.timestamp_ns,
                sequence=logical.sequence,
                width=logical.width,
                height=logical.height,
                row_stride=logical.row_stride,
                encoding=logical.encoding,
                data=np.frombuffer(logical.data, dtype=np.uint8),
            )

        if archetype == "fixed_numeric_array":
            assert isinstance(logical, FixedNumericArrayData)
            return self._classes["FixedNumericArray"](
                timestamp_ns=logical.timestamp_ns,
                sequence=logical.sequence,
                values=np.asarray(logical.values, dtype=np.float64),
            )

        assert isinstance(logical, WideFlatData)
        fields = {
            f"channel_{index:02d}": value
            for index, value in enumerate(logical.channels)
        }
        return self._classes["WideFlat"](
            timestamp_ns=logical.timestamp_ns,
            sequence=logical.sequence,
            **fields,
        )

    def serialize_one(self, archetype: Archetype, value: Any) -> bytes:
        return bytes(self._store.serialize_cdr(value, self._type_names[archetype]))

    def deserialize_one(self, archetype: Archetype, payload: bytes) -> float:
        value = self._store.deserialize_cdr(payload, self._type_names[archetype])
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
            materialized = value.data.tobytes()
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
            return value.timestamp_ns + value.sequence + float(value.values.sum())
        return value.timestamp_ns + value.sequence + sum(
            getattr(value, f"channel_{index:02d}") for index in range(32)
        )
