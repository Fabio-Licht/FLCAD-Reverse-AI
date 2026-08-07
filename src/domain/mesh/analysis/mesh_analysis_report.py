"""Immutable result of a mesh analysis capability execution."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.mesh.analysis.mesh_metrics import MeshMetrics
from domain.mesh.analysis.mesh_quality import MeshQuality
from domain.mesh.bounding_box import BoundingBox


@dataclass(frozen=True, slots=True)
class MeshAnalysisReport:
    """Report mesh bounds, metrics, quality, timing, and warnings."""

    mesh_uuid: UUID
    bounding_box: BoundingBox | None
    metrics: MeshMetrics
    quality: MeshQuality
    execution_time: float
    warnings: tuple[str, ...]
