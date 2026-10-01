from __future__ import annotations

from typing import Any

import flatbuffers
from robotics_numbers.msg_archetypes import BigSensor
from robotics_numbers.msg_archetypes import FixedNumericArray
from robotics_numbers.msg_archetypes import FixedNumericValues
from robotics_numbers.msg_archetypes import ListOfNested
from robotics_numbers.msg_archetypes import ListOfTriplyNested
from robotics_numbers.msg_archetypes import NestedListLevel1
from robotics_numbers.msg_archetypes import NestedListLevel2
from robotics_numbers.msg_archetypes import SmallFlat
from robotics_numbers.msg_archetypes import WideFlat

from adapters.base import Adapter
from models import Archetype
from models import BigSensorData
from models import FixedNumericArrayData
from models import ListOfNestedData
from models import ListOfTriplyNestedData
from models import LogicalData
from models import SmallFlatData
from models import WideFlatData


def _build_small(builder: flatbuffers.Builder, value: SmallFlatData) -> int:
    SmallFlat.Start(builder)
    SmallFlat.AddTimestampNs(builder, value.timestamp_ns)
    SmallFlat.AddSequence(builder, value.sequence)
    SmallFlat.AddX(builder, value.x)
    SmallFlat.AddY(builder, value.y)
    SmallFlat.AddZ(builder, value.z)
    SmallFlat.AddValue(builder, value.value)
    SmallFlat.AddValid(builder, value.valid)
    return SmallFlat.End(builder)


def _consume_small(value: Any) -> float:
    return (
        value.TimestampNs()
        + value.Sequence()
        + value.X()
        + value.Y()
        + value.Z()
        + value.Value()
        + int(value.Valid())
    )


def _offset_vector(
    builder: flatbuffers.Builder, offsets: list[int], start_vector: Any
) -> int:
    start_vector(builder, len(offsets))
    for offset in reversed(offsets):
        builder.PrependUOffsetTRelative(offset)
    return builder.EndVector()


class FlatBuffersAdapter(Adapter):
    name = "flatbuffers"
    supports_construct_and_serialize = False

    def construct_one(self, archetype: Archetype, logical: LogicalData) -> Any:
        del archetype
        return logical

    def serialize_one(self, archetype: Archetype, value: Any) -> bytes:
        builder = flatbuffers.Builder(1024)

        if archetype == "small_flat":
            assert isinstance(value, SmallFlatData)
            root = _build_small(builder, value)

        elif archetype == "list_of_nested":
            assert isinstance(value, ListOfNestedData)
            offsets = [_build_small(builder, item) for item in value.samples]
            samples = _offset_vector(
                builder, offsets, ListOfNested.StartSamplesVector
            )
            ListOfNested.Start(builder)
            ListOfNested.AddTimestampNs(builder, value.timestamp_ns)
            ListOfNested.AddSequence(builder, value.sequence)
            ListOfNested.AddSamples(builder, samples)
            root = ListOfNested.End(builder)

        elif archetype == "list_of_triply_nested":
            assert isinstance(value, ListOfTriplyNestedData)
            level_1_offsets: list[int] = []
            for level_1_values in value.items:
                level_2_offsets: list[int] = []
                for level_2_values in level_1_values:
                    leaf_offsets = [
                        _build_small(builder, leaf) for leaf in level_2_values
                    ]
                    leaves = _offset_vector(
                        builder, leaf_offsets, NestedListLevel2.StartItemsVector
                    )
                    NestedListLevel2.Start(builder)
                    NestedListLevel2.AddItems(builder, leaves)
                    level_2_offsets.append(NestedListLevel2.End(builder))
                level_2 = _offset_vector(
                    builder, level_2_offsets, NestedListLevel1.StartItemsVector
                )
                NestedListLevel1.Start(builder)
                NestedListLevel1.AddItems(builder, level_2)
                level_1_offsets.append(NestedListLevel1.End(builder))
            level_1 = _offset_vector(
                builder, level_1_offsets, ListOfTriplyNested.StartItemsVector
            )
            ListOfTriplyNested.Start(builder)
            ListOfTriplyNested.AddTimestampNs(builder, value.timestamp_ns)
            ListOfTriplyNested.AddSequence(builder, value.sequence)
            ListOfTriplyNested.AddItems(builder, level_1)
            root = ListOfTriplyNested.End(builder)

        elif archetype == "big_sensor":
            assert isinstance(value, BigSensorData)
            encoding = builder.CreateString(value.encoding)
            data = builder.CreateByteVector(value.data)
            BigSensor.Start(builder)
            BigSensor.AddTimestampNs(builder, value.timestamp_ns)
            BigSensor.AddSequence(builder, value.sequence)
            BigSensor.AddWidth(builder, value.width)
            BigSensor.AddHeight(builder, value.height)
            BigSensor.AddRowStride(builder, value.row_stride)
            BigSensor.AddEncoding(builder, encoding)
            BigSensor.AddData(builder, data)
            root = BigSensor.End(builder)

        elif archetype == "fixed_numeric_array":
            assert isinstance(value, FixedNumericArrayData)
            values = FixedNumericValues.CreateFixedNumericValues(
                builder, value.values
            )
            FixedNumericArray.Start(builder)
            FixedNumericArray.AddValues(builder, values)
            FixedNumericArray.AddTimestampNs(builder, value.timestamp_ns)
            FixedNumericArray.AddSequence(builder, value.sequence)
            root = FixedNumericArray.End(builder)

        else:
            assert isinstance(value, WideFlatData)
            WideFlat.Start(builder)
            WideFlat.AddTimestampNs(builder, value.timestamp_ns)
            WideFlat.AddSequence(builder, value.sequence)
            for index, channel in enumerate(value.channels):
                getattr(WideFlat, f"AddChannel{index:02d}")(builder, channel)
            root = WideFlat.End(builder)

        builder.Finish(root)
        return bytes(builder.Output())

    def deserialize_one(self, archetype: Archetype, payload: bytes) -> float:
        if archetype == "small_flat":
            return _consume_small(SmallFlat.SmallFlat.GetRootAs(payload))

        if archetype == "list_of_nested":
            value = ListOfNested.ListOfNested.GetRootAs(payload)
            return value.TimestampNs() + value.Sequence() + sum(
                _consume_small(value.Samples(index))
                for index in range(value.SamplesLength())
            )

        if archetype == "list_of_triply_nested":
            value = ListOfTriplyNested.ListOfTriplyNested.GetRootAs(payload)
            checksum = value.TimestampNs() + value.Sequence()
            for level_1_index in range(value.ItemsLength()):
                level_1 = value.Items(level_1_index)
                for level_2_index in range(level_1.ItemsLength()):
                    level_2 = level_1.Items(level_2_index)
                    checksum += sum(
                        _consume_small(level_2.Items(leaf_index))
                        for leaf_index in range(level_2.ItemsLength())
                    )
            return checksum

        if archetype == "big_sensor":
            value = BigSensor.BigSensor.GetRootAs(payload)
            materialized = value.DataAsNumpy().tobytes()
            encoding = value.Encoding() or b""
            return (
                value.TimestampNs()
                + value.Sequence()
                + value.Width()
                + value.Height()
                + value.RowStride()
                + len(encoding)
                + len(materialized)
            )

        if archetype == "fixed_numeric_array":
            value = FixedNumericArray.FixedNumericArray.GetRootAs(payload)
            values = value.Values()
            return value.TimestampNs() + value.Sequence() + sum(values.Values())

        value = WideFlat.WideFlat.GetRootAs(payload)
        return value.TimestampNs() + value.Sequence() + sum(
            getattr(value, f"Channel{index:02d}")() for index in range(32)
        )
