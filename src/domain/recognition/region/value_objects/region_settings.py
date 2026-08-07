"""Configuration for topology-based region growing."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class RegionSettings:
    """Define explicit criteria for a region-growing operation."""

    normal_angle_tolerance: float
    maximum_distance: float
    minimum_region_size: int

    def __post_init__(self) -> None:
        """Validate all region-growing criteria."""

        if (
            not isfinite(self.normal_angle_tolerance)
            or not 0.0 <= self.normal_angle_tolerance <= 180.0
        ):
            raise ValueError(
                "Normal-angle tolerance must be between 0 and 180 degrees."
            )

        if (
            not isfinite(self.maximum_distance)
            or self.maximum_distance < 0.0
        ):
            raise ValueError(
                "Maximum distance must be finite and non-negative."
            )

        if self.minimum_region_size < 1:
            raise ValueError("Minimum region size must be greater than zero.")
