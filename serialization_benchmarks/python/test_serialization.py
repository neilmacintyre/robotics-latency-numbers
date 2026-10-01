from __future__ import annotations

import math

from adapters.base import EncodedValue
from conftest import BenchmarkCase
from models import LOGICAL_DATA_BUILDERS
from models import scale_label


def _wire_size(encoded: EncodedValue) -> int:
    if encoded.is_batch:
        return sum(len(payload) for payload in encoded.value)
    assert isinstance(encoded.value, bytes)
    return len(encoded.value)


def test_python_serialization(benchmark, bench_case: BenchmarkCase) -> None:
    adapter = bench_case.adapter
    logical = LOGICAL_DATA_BUILDERS[bench_case.archetype](bench_case.scale)
    prepared = adapter.prepare(bench_case.archetype, logical)
    encoded = adapter.serialize(prepared)

    checksum = adapter.deserialize(encoded)
    assert math.isfinite(checksum)

    benchmark.group = (
        f"{bench_case.operation}/{bench_case.archetype}/"
        f"{scale_label(bench_case.archetype, bench_case.scale)}"
    )
    benchmark.extra_info["serializer"] = adapter.name
    benchmark.extra_info["archetype"] = bench_case.archetype
    benchmark.extra_info["scale"] = bench_case.scale
    benchmark.extra_info["operation"] = bench_case.operation
    benchmark.extra_info["wire_bytes"] = _wire_size(encoded)

    if bench_case.operation == "serialize":
        result = benchmark(adapter.serialize, prepared)
        assert _wire_size(result) > 0
        return

    if bench_case.operation == "deserialize":
        result = benchmark(adapter.deserialize, encoded)
        assert math.isfinite(result)
        return

    result = benchmark(
        adapter.construct_and_serialize,
        bench_case.archetype,
        logical,
    )
    assert _wire_size(result) > 0
