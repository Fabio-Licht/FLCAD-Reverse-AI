"""In-memory manager for engineering reference objects."""

from __future__ import annotations

from uuid import UUID

from domain.reference.entities.reference_entity import ReferenceEntity


class ReferenceManager:
    """Manage reference identity, naming, and logical state queries."""

    def __init__(self) -> None:
        self._references: dict[UUID, ReferenceEntity] = {}

    def add(self, reference: ReferenceEntity) -> bool:
        """Register a reference if its identity and name are unique."""

        if reference.id in self._references:
            return False

        if self.find_by_name(reference.name) is not None:
            raise ValueError(f"Reference name already exists: {reference.name}")

        self._references[reference.id] = reference
        return True

    def remove(self, reference_id: UUID) -> ReferenceEntity | None:
        """Remove and return a reference by identity."""

        return self._references.pop(reference_id, None)

    def find_by_id(self, reference_id: UUID) -> ReferenceEntity | None:
        """Return a reference by identity."""

        return self._references.get(reference_id)

    def find_by_name(self, name: str) -> ReferenceEntity | None:
        """Return the reference with an exact name match."""

        return next(
            (
                reference
                for reference in self._references.values()
                if reference.name == name
            ),
            None,
        )

    def all(self) -> tuple[ReferenceEntity, ...]:
        """Return all references in registration order."""

        return tuple(self._references.values())

    def visible(self) -> tuple[ReferenceEntity, ...]:
        """Return logically visible references."""

        return tuple(
            reference
            for reference in self._references.values()
            if reference.visible
        )

    def selected(self) -> tuple[ReferenceEntity, ...]:
        """Return logically selected references."""

        return tuple(
            reference
            for reference in self._references.values()
            if reference.selected
        )
