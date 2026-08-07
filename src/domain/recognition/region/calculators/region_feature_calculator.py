"""Stateless extraction of reusable region features."""

from __future__ import annotations

from math import isfinite

from domain.recognition.region.entities.region import Region
from domain.recognition.region.value_objects.region_analysis import (
    RegionAnalysis,
)
from domain.recognition.region.value_objects.region_features import (
    RegionFeatures,
)


class RegionFeatureCalculator:
    """Convert region-analysis evidence into reusable numeric features."""

    def calculate(
        self,
        region: Region,
        analysis: RegionAnalysis,
    ) -> RegionFeatures:
        """Return features derived from a region and its analysis."""

        self._validate(region, analysis)

        normal_consistency = self._bounded(
            1.0 - analysis.normal_variance
        )
        angular_consistency = self._bounded(
            1.0 - analysis.maximum_angular_deviation / 180.0
        )
        planarity_score = normal_consistency * angular_consistency
        triangle_density = (
            analysis.triangle_count / analysis.area
            if analysis.area > 0.0
            else 0.0
        )

        return RegionFeatures(
            planarity_score=planarity_score,
            normal_consistency=normal_consistency,
            area_score=analysis.area,
            triangle_density=triangle_density,
        )

    @staticmethod
    def _validate(region: Region, analysis: RegionAnalysis) -> None:
        """Validate that analysis evidence is consistent and finite."""

        if analysis.triangle_count != len(region.triangle_indices):
            raise ValueError(
                "Region analysis triangle count does not match the region."
            )

        if analysis.area != region.area:
            raise ValueError(
                "Region analysis area does not match the region."
            )

        numeric_values = (
            analysis.normal_variance,
            analysis.maximum_angular_deviation,
            analysis.area,
        )

        if not all(isfinite(value) for value in numeric_values):
            raise ValueError("Region analysis metrics must be finite.")

        if not 0.0 <= analysis.normal_variance <= 1.0:
            raise ValueError("Normal variance must be between zero and one.")

        if not 0.0 <= analysis.maximum_angular_deviation <= 180.0:
            raise ValueError(
                "Maximum angular deviation must be between 0 and 180 degrees."
            )

        if analysis.area < 0.0:
            raise ValueError("Region area must not be negative.")

        if analysis.triangle_count < 0:
            raise ValueError("Region triangle count must not be negative.")

    @staticmethod
    def _bounded(value: float) -> float:
        """Clamp a normalized feature against floating-point drift."""

        return max(0.0, min(1.0, value))
