from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import Any

from cstructs import BigSensor
from cstructs import FixedNumericArray
from cstructs import ListOfNested
from cstructs import ListOfTriplyNested
from cstructs import NestedListLevel1
from cstructs import NestedListLevel2
from cstructs import SmallFlat
from cstructs import WideFlat

from adapters.base import Adapter
from models import Archetype
from models import BigSensorData
from models import FixedNumericArrayData
from models import ListOfNestedData
from models import ListOfTriplyNestedData
from models import LogicalData
from models import SmallFlatData
from models import WideFlatData


class _ListHeader(ctypes.Structure):
    _fields_ = [
        ("timestamp_ns", ctypes.c_uint64),
        ("sequence", ctypes.c_uint32),
        ("count", ctypes.c_size_t),
    ]


class _CountHeader(ctypes.Structure):
    _fields_ = [("count", ctypes.c_size_t)]


class _BigSensorHeader(ctypes.Structure):
    _fields_ = [
        ("timestamp_ns", ctypes.c_uint64),
        ("sequence", ctypes.c_uint32),
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
        ("row_stride", ctypes.c_uint32),
        ("encoding_size", ctypes.c_size_t),
        ("data_size", ctypes.c_size_t),
    ]


@dataclass(slots=True)
class _Owned:
    value: Any
    owners: tuple[Any, ...] = ()


def _small(value: SmallFlatData) -> SmallFlat:
    return SmallFlat(
        timestamp_ns=value.timestamp_ns,
        sequence=value.sequence,
        x=value.x,
        y=value.y,
        z=value.z,
        value=value.value,
        valid=value.valid,
    )


def _consume_small(value: SmallFlat) -> float:
    return (
        value.timestamp_ns
        + value.sequence
        + value.x
        + value.y
        + value.z
        + value.value
        + int(value.valid)
    )


class CtypesAdapter(Adapter):
    name = "ctypes"

    def construct_one(self, archetype: Archetype, logical: LogicalData) -> _Owned:
        if archetype == "small_flat":
            assert isinstance(logical, SmallFlatData)
            return _Owned(_small(logical))

        if archetype == "list_of_nested":
            assert isinstance(logical, ListOfNestedData)
            samples = (SmallFlat * len(logical.samples))(
                *(_small(value) for value in logical.samples)
            )
            value = ListOfNested(
                timestamp_ns=logical.timestamp_ns,
                sequence=logical.sequence,
                samples_count=len(samples),
                samples=ctypes.cast(samples, ctypes.POINTER(SmallFlat)),
            )
            return _Owned(value, (samples,))

        if archetype == "list_of_triply_nested":
            assert isinstance(logical, ListOfTriplyNestedData)
            owners: list[Any] = []
            level_1_values: list[NestedListLevel1] = []
            for level_1_data in logical.items:
                level_2_values: list[NestedListLevel2] = []
                for level_2_data in level_1_data:
                    leaves = (SmallFlat * len(level_2_data))(
                        *(_small(value) for value in level_2_data)
                    )
                    owners.append(leaves)
                    level_2_values.append(
                        NestedListLevel2(
                            items_count=len(leaves),
                            items=ctypes.cast(leaves, ctypes.POINTER(SmallFlat)),
                        )
                    )
                level_2 = (NestedListLevel2 * len(level_2_values))(*level_2_values)
                owners.append(level_2)
                level_1_values.append(
                    NestedListLevel1(
                        items_count=len(level_2),
                        items=ctypes.cast(
                            level_2, ctypes.POINTER(NestedListLevel2)
                        ),
                    )
                )
            level_1 = (NestedListLevel1 * len(level_1_values))(*level_1_values)
            owners.append(level_1)
            value = ListOfTriplyNested(
                timestamp_ns=logical.timestamp_ns,
                sequence=logical.sequence,
                items_count=len(level_1),
                items=ctypes.cast(level_1, ctypes.POINTER(NestedListLevel1)),
            )
            return _Owned(value, tuple(owners))

        if archetype == "big_sensor":
            assert isinstance(logical, BigSensorData)
            encoding = logical.encoding.encode()
            data = (ctypes.c_uint8 * len(logical.data)).from_buffer_copy(logical.data)
            value = BigSensor(
                timestamp_ns=logical.timestamp_ns,
                sequence=logical.sequence,
                width=logical.width,
                height=logical.height,
                row_stride=logical.row_stride,
                encoding=encoding,
                data_size=len(data),
                data=ctypes.cast(data, ctypes.POINTER(ctypes.c_uint8)),
            )
            return _Owned(value, (encoding, data))

        if archetype == "fixed_numeric_array":
            assert isinstance(logical, FixedNumericArrayData)
            values = (ctypes.c_double * 36)(*logical.values)
            return _Owned(
                FixedNumericArray(
                    timestamp_ns=logical.timestamp_ns,
                    sequence=logical.sequence,
                    values=values,
                )
            )

        assert isinstance(logical, WideFlatData)
        fields = {
            f"channel_{index:02d}": value
            for index, value in enumerate(logical.channels)
        }
        return _Owned(
            WideFlat(
                timestamp_ns=logical.timestamp_ns,
                sequence=logical.sequence,
                **fields,
            )
        )

    def serialize_one(self, archetype: Archetype, owned: _Owned) -> bytes:
        value = owned.value
        if archetype in ("small_flat", "fixed_numeric_array", "wide_flat"):
            return bytes(value)

        if archetype == "list_of_nested":
            header = _ListHeader(
                timestamp_ns=value.timestamp_ns,
                sequence=value.sequence,
                count=value.samples_count,
            )
            output = bytearray(bytes(header))
            for index in range(value.samples_count):
                output.extend(bytes(value.samples[index]))
            return bytes(output)

        if archetype == "list_of_triply_nested":
            header = _ListHeader(
                timestamp_ns=value.timestamp_ns,
                sequence=value.sequence,
                count=value.items_count,
            )
            output = bytearray(bytes(header))
            for level_1_index in range(value.items_count):
                level_1 = value.items[level_1_index]
                output.extend(bytes(_CountHeader(count=level_1.items_count)))
                for level_2_index in range(level_1.items_count):
                    level_2 = level_1.items[level_2_index]
                    output.extend(bytes(_CountHeader(count=level_2.items_count)))
                    for leaf_index in range(level_2.items_count):
                        output.extend(bytes(level_2.items[leaf_index]))
            return bytes(output)

        encoding = value.encoding or b""
        header = _BigSensorHeader(
            timestamp_ns=value.timestamp_ns,
            sequence=value.sequence,
            width=value.width,
            height=value.height,
            row_stride=value.row_stride,
            encoding_size=len(encoding),
            data_size=value.data_size,
        )
        return (
            bytes(header)
            + encoding
            + ctypes.string_at(value.data, value.data_size)
        )

    def deserialize_one(self, archetype: Archetype, payload: bytes) -> float:
        if archetype == "small_flat":
            return _consume_small(SmallFlat.from_buffer_copy(payload))

        if archetype == "fixed_numeric_array":
            value = FixedNumericArray.from_buffer_copy(payload)
            return value.timestamp_ns + value.sequence + sum(value.values)

        if archetype == "wide_flat":
            value = WideFlat.from_buffer_copy(payload)
            return value.timestamp_ns + value.sequence + sum(
                getattr(value, f"channel_{index:02d}") for index in range(32)
            )

        if archetype == "list_of_nested":
            header_size = ctypes.sizeof(_ListHeader)
            item_size = ctypes.sizeof(SmallFlat)
            header = _ListHeader.from_buffer_copy(payload[:header_size])
            checksum = header.timestamp_ns + header.sequence
            offset = header_size
            for _ in range(header.count):
                checksum += _consume_small(
                    SmallFlat.from_buffer_copy(payload, offset)
                )
                offset += item_size
            return checksum

        if archetype == "list_of_triply_nested":
            list_header_size = ctypes.sizeof(_ListHeader)
            count_header_size = ctypes.sizeof(_CountHeader)
            item_size = ctypes.sizeof(SmallFlat)
            header = _ListHeader.from_buffer_copy(payload[:list_header_size])
            checksum = header.timestamp_ns + header.sequence
            offset = list_header_size
            for _ in range(header.count):
                level_1 = _CountHeader.from_buffer_copy(payload, offset)
                offset += count_header_size
                for _ in range(level_1.count):
                    level_2 = _CountHeader.from_buffer_copy(payload, offset)
                    offset += count_header_size
                    for _ in range(level_2.count):
                        checksum += _consume_small(
                            SmallFlat.from_buffer_copy(payload, offset)
                        )
                        offset += item_size
            return checksum

        header_size = ctypes.sizeof(_BigSensorHeader)
        header = _BigSensorHeader.from_buffer_copy(payload[:header_size])
        encoding_start = header_size
        data_start = encoding_start + header.encoding_size
        materialized = bytes(payload[data_start : data_start + header.data_size])
        return (
            header.timestamp_ns
            + header.sequence
            + header.width
            + header.height
            + header.row_stride
            + header.encoding_size
            + len(materialized)
        )
