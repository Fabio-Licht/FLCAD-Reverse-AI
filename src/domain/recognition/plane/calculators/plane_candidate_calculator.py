"""Explainable calculation of plane-candidate evidence."""

from __future__ import annotations

from domain.recognition.plane.entities.plane_candidate import PlaneCandidate
from domain.recognition.plane.value_objects.plane_candidate_settings import (
    PlaneCandidateSettings,
)
from domain.recognition.region.entities.region import Region
from domain.recognition.region.value_objects.region_analysis import (
    RegionAnalysis,
)
from domain.recognition.region.value_objects.region_features import (
    RegionFeatures,
)


class PlaneCandidateCalculator:
    """Evaluate region evidence without fitting or creating a plane."""

    def calculate(
        self,
        region: Region,
        analysis: RegionAnalysis,
        features: RegionFeatures,
        settings: PlaneCandidateSettings,
    ) -> PlaneCandidate:
        """Return an explainable candidate derived from region evidence."""

        area_support = min(1.0, analysis.area / settings.minimum_area)
        triangle_support = min(
            1.0,
            analysis.triangle_count / settings.minimum_triangle_count,
        )
        confidence = self._bounded(
            features.planarity_score
            * area_support
            * triangle_support
        )
        evidence = (
            self._evidence(
                "planarity",
                features.planarity_score,
                settings.minimum_planarity,
                features.planarity_score >= settings.minimum_planarity,
            ),
            self._evidence(
                "area",
                analysis.area,
                settings.minimum_area,
                analysis.area >= settings.minimum_area,
            ),
            self._evidence(
                "triangle_count",
                analysis.triangle_count,
                settings.minimum_triangle_count,
                analysis.triangle_count >= settings.minimum_triangle_count,
            ),
            self._evidence(
                "normal_consistency",
                features.normal_consistency,
                None,
                True,
            ),
            self._evidence(
                "maximum_angular_deviation_degrees",
                analysis.maximum_angular_deviation,
                None,
                True,
            ),
            self._evidence(
                "confidence",
                confidence,
                settings.minimum_confidence,
                confidence >= settings.minimum_confidence,
            ),
        )

        return PlaneCandidate(
            region=region,
            confidence=confidence,
            evidence=evidence,
            average_normal=analysis.average_normal,
            bounding_box=region.bounding_box,
            area=analysis.area,
            triangle_count=analysis.triangle_count,
        )

    @staticmethod
    def _evidence(
        name: str,
        value: float | int,
        threshold: float | int | None,
        passed: bool,
    ) -> str:
        """Create one stable, human-readable evidence statement."""

        threshold_text = (
            "not_applicable" if threshold is None else str(threshold)
        )
        return (
            f"{name}: value={value}; threshold={threshold_text}; "
            f"passed={str(passed).lower()}"
        )

    @staticmethod
    def _bounded(value: float) -> float:
        """Clamp confidence against floating-point drift."""

        return max(0.0, min(1.0, value))
