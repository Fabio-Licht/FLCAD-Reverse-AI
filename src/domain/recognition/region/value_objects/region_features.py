"""Immutable engineering features extracted from region analysis."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegionFeatures:
    """Store reusable features without making recognition decisions."""

    planarity_score: float
    normal_consistency: float
    area_score: float
    triangle_density: float
