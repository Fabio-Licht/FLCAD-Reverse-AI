"""Core entity model for the FLCAD platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.entity.entity_relationship import EntityRelationship
from core.entity.entity_source import EntitySource
from core.entity.entity_state import EntityState
from core.entity.entity_type import EntityType


@dataclass(slots=True, repr=False)
class EngineeringEntity:
    """Represent a common engineering object in the FLCAD platform."""

    name: str
    display_name: str
    entity_type: EntityType
    state: EntityState = EntityState.DRAFT
    source: EntitySource = EntitySource.USER
    confidence: float | None = None
    tags: set[str] = field(default_factory=set)
    custom_properties: dict[str, Any] = field(default_factory=dict)
    relationships: set[tuple[EntityRelationship, UUID]] = field(
        default_factory=set
    )
    components: dict[str, Any] = field(default_factory=dict)
    uuid: UUID = field(default_factory=uuid4, init=False)

    def __repr__(self) -> str:
        """Return a concise representation suitable for diagnostics."""

        return (
            f"{type(self).__name__}("
            f"uuid={self.uuid!r}, "
            f"name={self.name!r}, "
            f"display_name={self.display_name!r}, "
            f"entity_type={self.entity_type.value!r}, "
            f"state={self.state.value!r}, "
            f"source={self.source.value!r}, "
            f"confidence={self.confidence!r}, "
            f"tags={self.tags!r}, "
            f"relationships={len(self.relationships)}, "
            f"components={len(self.components)}"
            f")"
        )
