"""Immutable report returned by reference-plane creation."""

from __future__ import annotations

from dataclasses import dataclass

from domain.reference.entities.reference_plane import ReferencePlane


@dataclass(frozen=True, slots=True)
class ReferencePlaneReport:
    """Store a registered reference plane, timing, and warnings."""

    reference_plane: ReferencePlane
    execution_time: float
    warnings: tuple[str, ...]
