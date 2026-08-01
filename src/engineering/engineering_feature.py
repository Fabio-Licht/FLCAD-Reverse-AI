from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class FeatureState(Enum):
    DETECTED = "detected"
    VALIDATED = "validated"
    CONFIRMED = "confirmed"
    LOCKED = "locked"
    ARCHIVED = "archived"


@dataclass(slots=True)
class EngineeringFeature:
    """
    Classe base de todas as Features do FLCAD.

    Esta classe representa um objeto de engenharia.
    Ela não conhece renderização, Qt ou PyVista.
    """

    geometry: Any
    name: str

    id: UUID = field(default_factory=uuid4)

    state: FeatureState = FeatureState.DETECTED

    confidence: float = 0.0

    visible: bool = True

    selected: bool = False

    locked: bool = False

    metadata: dict[str, Any] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    relationships: list[UUID] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)

    modified_at: datetime = field(default_factory=datetime.now)

    # -------------------------------------------------

    def touch(self) -> None:
        self.modified_at = datetime.now()

    # -------------------------------------------------

    def rename(self, new_name: str) -> None:

        self.name = new_name

        self.touch()

    # -------------------------------------------------

    def select(self) -> None:

        self.selected = True

        self.touch()

    def unselect(self) -> None:

        self.selected = False

        self.touch()

    # -------------------------------------------------

    def hide(self) -> None:

        self.visible = False

        self.touch()

    def show(self) -> None:

        self.visible = True

        self.touch()

    # -------------------------------------------------

    def lock(self) -> None:

        self.locked = True

        self.state = FeatureState.LOCKED

        self.touch()

    def unlock(self) -> None:

        self.locked = False

        self.state = FeatureState.CONFIRMED

        self.touch()

    # -------------------------------------------------

    def archive(self) -> None:

        self.state = FeatureState.ARCHIVED

        self.touch()

    # -------------------------------------------------

    def set_state(self, state: FeatureState) -> None:

        self.state = state

        self.touch()

    # -------------------------------------------------

    def set_confidence(self, value: float) -> None:

        self.confidence = max(
            0.0,
            min(1.0, value),
        )

        self.touch()

    # -------------------------------------------------

    def add_tag(self, tag: str) -> None:

        self.tags.add(tag)

        self.touch()

    def remove_tag(self, tag: str) -> None:

        self.tags.discard(tag)

        self.touch()

    # -------------------------------------------------

    def add_relationship(self, feature_id: UUID) -> None:

        if feature_id not in self.relationships:

            self.relationships.append(feature_id)

            self.touch()

    def remove_relationship(self, feature_id: UUID) -> None:

        if feature_id in self.relationships:

            self.relationships.remove(feature_id)

            self.touch()

    # -------------------------------------------------

    @property
    def is_confirmed(self) -> bool:

        return self.state is FeatureState.CONFIRMED

    @property
    def is_locked(self) -> bool:

        return self.locked

    @property
    def is_visible(self) -> bool:

        return self.visible