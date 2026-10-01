from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

Archetype = Literal[
    "small_flat",
    "list_of_nested",
    "list_of_triply_nested",
    "big_sensor",
    "fixed_numeric_array",
    "wide_flat",
]

ARCHETYPES: tuple[Archetype, ...] = (
    "small_flat",
    "list_of_nested",
    "list_of_triply_nested",
    "big_sensor",
    "fixed_numeric_array",
    "wide_flat",
)


@dataclass(frozen=True, slots=True)
class SmallFlatData:
    timestamp_ns: int
    sequence: int
    x: float
    y: float
    z: float
    value: float
    valid: bool


@dataclass(frozen=True, slots=True)
class ListOfNestedData:
    timestamp_ns: int
    sequence: int
    samples: tuple[SmallFlatData, ...]


@dataclass(frozen=True, slots=True)
class ListOfTriplyNestedData:
    timestamp_ns: int
    sequence: int
    items: tuple[tuple[tuple[SmallFlatData, ...], ...], ...]


@dataclass(frozen=True, slots=True)
class BigSensorData:
    timestamp_ns: int
    sequence: int
    width: int
    height: int
    row_stride: int
    encoding: str
    data: bytes


@dataclass(frozen=True, slots=True)
class FixedNumericArrayData:
    timestamp_ns: int
    sequence: int
    values: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class WideFlatData:
    timestamp_ns: int
    sequence: int
    channels: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class BatchData:
    items: tuple[SmallFlatData, ...]


LogicalData = (
    SmallFlatData
    | ListOfNestedData
    | ListOfTriplyNestedData
    | BigSensorData
    | FixedNumericArrayData
    | WideFlatData
    | BatchData
)

_BYTE_PATTERN = bytes(range(256))

SCALE_PROFILES: dict[str, dict[Archetype, tuple[int, ...]]] = {
    "quick": {
        "small_flat": (1, 256, 4096),
        "list_of_nested": (0, 64, 4096),
        "list_of_triply_nested": (1, 4, 16),
        "big_sensor": (0, 64 * 1024, 4 * 1024 * 1024),
        "fixed_numeric_array": (36,),
        "wide_flat": (0, 50, 100),
    },
    "core": {
        "small_flat": (1, 16, 256, 4096, 65536),
        "list_of_nested": (0, 1, 8, 64, 512, 4096),
        "list_of_triply_nested": (1, 2, 4, 8, 16),
        "big_sensor": (
            0,
            1024,
            64 * 1024,
            1024 * 1024,
            4 * 1024 * 1024,
            16 * 1024 * 1024,
        ),
        "fixed_numeric_array": (36,),
        "wide_flat": (0, 25, 50, 75, 100),
    },
    "stress": {
        "small_flat": (65536,),
        "list_of_nested": (4096,),
        "list_of_triply_nested": (16,),
        "big_sensor": (64 * 1024 * 1024,),
        "fixed_numeric_array": (36,),
        "wide_flat": (100,),
    },
}


def scale_label(archetype: Archetype, scale: int) -> str:
    if archetype == "big_sensor":
        if scale >= 1024 * 1024:
            return f"{scale // (1024 * 1024)}MiB"
        if scale >= 1024:
            return f"{scale // 1024}KiB"
        return f"{scale}B"
    if archetype == "list_of_triply_nested":
        return f"fanout-{scale}-leaves-{scale**3}"
    if archetype == "wide_flat":
        return f"density-{scale}pct"
    if archetype == "fixed_numeric_array":
        return "36-doubles"
    return f"count-{scale}"


def make_small_flat(index: int = 0) -> SmallFlatData:
    value = float(index + 1)
    return SmallFlatData(
        timestamp_ns=1_700_000_000_000_000_000 + index,
        sequence=index & 0xFFFFFFFF,
        x=value * 0.25,
        y=value * -0.5,
        z=value * 0.75,
        value=value * 1.25,
        valid=(index & 1) == 0,
    )


def make_small_flat_batch(message_count: int) -> BatchData:
    return BatchData(
        tuple(make_small_flat(index) for index in range(message_count))
    )


def make_list_of_nested(sample_count: int) -> ListOfNestedData:
    return ListOfNestedData(
        timestamp_ns=1_700_000_000_000_000_000,
        sequence=7,
        samples=tuple(make_small_flat(index) for index in range(sample_count)),
    )


def make_list_of_triply_nested(fanout: int) -> ListOfTriplyNestedData:
    next_index = 0
    level_1: list[tuple[tuple[SmallFlatData, ...], ...]] = []
    for _ in range(fanout):
        level_2: list[tuple[SmallFlatData, ...]] = []
        for _ in range(fanout):
            leaves = tuple(
                make_small_flat(next_index + offset)
                for offset in range(fanout)
            )
            next_index += fanout
            level_2.append(leaves)
        level_1.append(tuple(level_2))
    return ListOfTriplyNestedData(
        timestamp_ns=1_700_000_000_000_000_000,
        sequence=11,
        items=tuple(level_1),
    )


def make_big_sensor(data_size: int) -> BigSensorData:
    repeats, remainder = divmod(data_size, len(_BYTE_PATTERN))
    data = _BYTE_PATTERN * repeats + _BYTE_PATTERN[:remainder]
    width = 1024 if data_size else 0
    height = (data_size + width - 1) // width if width else 0
    return BigSensorData(
        timestamp_ns=1_700_000_000_000_000_000,
        sequence=13,
        width=width,
        height=height,
        row_stride=width,
        encoding="8UC1",
        data=data,
    )


def make_fixed_numeric_array() -> FixedNumericArrayData:
    return FixedNumericArrayData(
        timestamp_ns=1_700_000_000_000_000_000,
        sequence=17,
        values=tuple(float(index) * 0.125 for index in range(36)),
    )


def make_wide_flat(populated_percent: int) -> WideFlatData:
    populated_channels = populated_percent * 32 // 100
    return WideFlatData(
        timestamp_ns=1_700_000_000_000_000_000,
        sequence=19,
        channels=tuple(
            float(index + 1) if index < populated_channels else 0.0
            for index in range(32)
        ),
    )


LOGICAL_DATA_BUILDERS: dict[Archetype, Callable[[int], LogicalData]] = {
    "small_flat": make_small_flat_batch,
    "list_of_nested": make_list_of_nested,
    "list_of_triply_nested": make_list_of_triply_nested,
    "big_sensor": make_big_sensor,
    "fixed_numeric_array": lambda _value_count: make_fixed_numeric_array(),
    "wide_flat": make_wide_flat,
}
