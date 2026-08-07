"""Immutable engineering provenance for a fitted plane."""

from __future__ import annotations

from dataclasses import dataclass

from domain.mesh.mesh_entity import MeshEntity
from domain.recognition.plane.entities.plane_candidate import PlaneCandidate
from domain.recognition.plane.value_objects.plane_fit_statistics import (
    PlaneFitStatistics,
)
from domain.recognition.region.entities.region import Region


@dataclass(frozen=True, slots=True)
class PlaneProvenance:
    """Preserve the complete source evidence of a fitted plane."""

    mesh: MeshEntity
    region: Region
    candidate: PlaneCandidate
    statistics: PlaneFitStatistics
