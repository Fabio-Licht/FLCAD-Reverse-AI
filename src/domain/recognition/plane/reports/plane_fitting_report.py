"""Immutable report returned by mathematical plane fitting."""

from __future__ import annotations

from dataclasses import dataclass

from domain.recognition.plane.entities.plane import Plane
from domain.recognition.plane.value_objects.plane_fit_statistics import (
    PlaneFitStatistics,
)
from domain.recognition.plane.value_objects.plane_provenance import (
    PlaneProvenance,
)


@dataclass(frozen=True, slots=True)
class PlaneFittingReport:
    """Store a fitted plane, statistics, timing, and warnings."""

    plane: Plane
    statistics: PlaneFitStatistics
    provenance: PlaneProvenance
    execution_time: float
    warnings: tuple[str, ...]
