"""Immutable derived metrics for a segmented mesh region."""

from __future__ import annotations

from dataclasses import dataclass

from domain.mesh.bounding_box import Point3D


@dataclass(frozen=True, slots=True)
class RegionAnalysis:
    """Store geometry-derived evidence calculated for a region."""

    average_normal: Point3D
    normal_variance: float
    maximum_angular_deviation: float
    triangle_count: int
    boundary_edge_count: int
    area: float
