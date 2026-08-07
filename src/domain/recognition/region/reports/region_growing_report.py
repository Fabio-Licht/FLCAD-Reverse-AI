"""Immutable report returned by region-growing execution."""

from __future__ import annotations

from dataclasses import dataclass

from domain.recognition.region.entities.region import Region


@dataclass(frozen=True, slots=True)
class RegionGrowingReport:
    """Store a segmented region, execution time, and warnings."""

    region: Region
    execution_time: float
    warnings: tuple[str, ...]
