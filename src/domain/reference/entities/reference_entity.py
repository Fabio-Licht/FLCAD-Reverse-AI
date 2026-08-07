"""Common domain foundation for engineering reference objects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TypeAlias
from uuid import UUID

from core.entity.engineering_entity import EngineeringEntity
from core.entity.entity_type import EntityType


ReferenceColor: TypeAlias = tuple[float, float, float]


@dataclass(slots=True, repr=False, kw_only=True)
class ReferenceEntity(EngineeringEntity, ABC):
    """Define shared state for all engineering reference objects."""

    visible: bool = True
    selected: bool = False
    locked: bool = False
    color: ReferenceColor = (1.0, 1.0, 1.0)
    opacity: float = 1.0
    layer: str = "default"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> UUID:
        """Expose the common engineering entity identity."""

        return self.uuid

    @property
    @abstractmethod
    def reference_type(self) -> EntityType:
        """Return the domain type represented by this reference."""

        raise NotImplementedError
