from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from models import Archetype
from models import BatchData
from models import LogicalData


@dataclass(slots=True)
class PreparedValue:
    archetype: Archetype
    value: Any
    is_batch: bool = False


@dataclass(slots=True)
class EncodedValue:
    archetype: Archetype
    value: bytes | tuple[bytes, ...]
    is_batch: bool = False


class Adapter(ABC):
    name: str
    supports_construct_and_serialize = True

    def prepare(self, archetype: Archetype, logical: LogicalData) -> PreparedValue:
        if isinstance(logical, BatchData):
            return PreparedValue(
                archetype,
                tuple(self.construct_one(archetype, item) for item in logical.items),
                is_batch=True,
            )
        return PreparedValue(archetype, self.construct_one(archetype, logical))

    def serialize(self, prepared: PreparedValue) -> EncodedValue:
        if prepared.is_batch:
            return EncodedValue(
                prepared.archetype,
                tuple(
                    self.serialize_one(prepared.archetype, value)
                    for value in prepared.value
                ),
                is_batch=True,
            )
        return EncodedValue(
            prepared.archetype,
            self.serialize_one(prepared.archetype, prepared.value),
        )

    def deserialize(self, encoded: EncodedValue) -> float:
        if encoded.is_batch:
            return sum(
                self.deserialize_one(encoded.archetype, payload)
                for payload in encoded.value
            )
        assert isinstance(encoded.value, bytes)
        return self.deserialize_one(encoded.archetype, encoded.value)

    def construct_and_serialize(
        self, archetype: Archetype, logical: LogicalData
    ) -> EncodedValue:
        return self.serialize(self.prepare(archetype, logical))

    @abstractmethod
    def construct_one(self, archetype: Archetype, logical: LogicalData) -> Any:
        raise NotImplementedError

    @abstractmethod
    def serialize_one(self, archetype: Archetype, value: Any) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def deserialize_one(self, archetype: Archetype, payload: bytes) -> float:
        raise NotImplementedError
