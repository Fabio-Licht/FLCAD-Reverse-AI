"""Read-only inspection state for selected engineering objects."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from application.interaction.property_service import (
    PropertyCollection,
    PropertyService,
)
from application.interaction.selection_service import SelectionTarget


@dataclass(frozen=True, slots=True)
class InspectionSnapshot:
    """Represent the current immutable engineering inspection result."""

    object_id: str
    entity: object
    properties: PropertyCollection


InspectionCallback = Callable[[InspectionSnapshot | None], None]


class InspectionService:
    """Produce and publish read-only engineering inspection information."""

    def __init__(self, property_service: PropertyService) -> None:
        self._property_service = property_service
        self._current: InspectionSnapshot | None = None
        self._callbacks: list[InspectionCallback] = []

    @property
    def current(self) -> InspectionSnapshot | None:
        """Return the currently inspected engineering object."""

        return self._current

    def inspect(self, target: SelectionTarget) -> InspectionSnapshot:
        """Inspect one selected target and publish its properties."""

        snapshot = InspectionSnapshot(
            object_id=target.object_id,
            entity=target.entity,
            properties=self._property_service.properties(
                target.entity,
                target.context,
            ),
        )
        self._current = snapshot
        self._notify()
        return snapshot

    def clear(self) -> None:
        """Clear the current inspection result."""

        self._current = None
        self._notify()

    def subscribe(self, callback: InspectionCallback) -> None:
        """Subscribe to read-only inspection changes."""

        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unsubscribe(self, callback: InspectionCallback) -> None:
        """Remove an inspection-change subscription."""

        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify(self) -> None:
        """Notify inspection observers."""

        for callback in tuple(self._callbacks):
            callback(self._current)
