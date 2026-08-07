"""Immutable statistics describing a mathematical plane fit."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlaneFitStatistics:
    """Store residual statistics and point classification counts."""

    rms_error: float
    maximum_error: float
    average_error: float
    point_count: int
    inlier_count: int
    outlier_count: int
