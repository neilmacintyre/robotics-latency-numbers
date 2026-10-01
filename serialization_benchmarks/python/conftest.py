from __future__ import annotations

from dataclasses import dataclass

import pytest

from adapters import Adapter
from adapters import create_adapters
from models import ARCHETYPES
from models import SCALE_PROFILES
from models import Archetype
from models import scale_label

OPERATIONS = ("serialize", "deserialize", "construct_serialize")
ADAPTERS = create_adapters()


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    adapter: Adapter
    archetype: Archetype
    scale: int
    operation: str

    @property
    def id(self) -> str:
        return (
            f"{self.adapter.name}-{self.archetype}-"
            f"{scale_label(self.archetype, self.scale)}-{self.operation}"
        )


def _csv_option(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("serialization benchmarks")
    group.addoption(
        "--serialization-profile",
        choices=tuple(SCALE_PROFILES),
        default="quick",
        help="Topology scale profile to run.",
    )
    group.addoption(
        "--serialization-serializers",
        default=",".join(ADAPTERS),
        help="Comma-separated serializers.",
    )
    group.addoption(
        "--serialization-archetypes",
        default=",".join(ARCHETYPES),
        help="Comma-separated message archetypes.",
    )
    group.addoption(
        "--serialization-operations",
        default=",".join(OPERATIONS),
        help="Comma-separated timed operations.",
    )
    group.addoption(
        "--serialization-case-filter",
        default="",
        help="Only run case IDs containing this substring.",
    )


def _validate_selection(
    selected: tuple[str, ...], valid: set[str], name: str
) -> None:
    unknown = set(selected) - valid
    if unknown:
        raise pytest.UsageError(f"unknown {name}: {', '.join(sorted(unknown))}")


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "bench_case" not in metafunc.fixturenames:
        return

    config = metafunc.config
    serializers = _csv_option(config.getoption("--serialization-serializers"))
    archetypes = _csv_option(config.getoption("--serialization-archetypes"))
    operations = _csv_option(config.getoption("--serialization-operations"))
    case_filter = config.getoption("--serialization-case-filter")
    profile_name = config.getoption("--serialization-profile")

    _validate_selection(serializers, set(ADAPTERS), "serializers")
    _validate_selection(archetypes, set(ARCHETYPES), "archetypes")
    _validate_selection(operations, set(OPERATIONS), "operations")

    profile = SCALE_PROFILES[profile_name]
    cases: list[BenchmarkCase] = []
    for serializer in serializers:
        adapter = ADAPTERS[serializer]
        for archetype_name in archetypes:
            archetype = archetype_name
            for scale in profile[archetype]:
                for operation in operations:
                    if (
                        operation == "construct_serialize"
                        and not adapter.supports_construct_and_serialize
                    ):
                        continue
                    case = BenchmarkCase(adapter, archetype, scale, operation)
                    if not case_filter or case_filter in case.id:
                        cases.append(case)

    metafunc.parametrize("bench_case", cases, ids=[case.id for case in cases])
