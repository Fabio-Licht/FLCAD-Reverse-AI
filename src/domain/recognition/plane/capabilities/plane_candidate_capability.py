"""Orchestration capability for plane-candidate generation."""

from __future__ import annotations

from math import isfinite
from time import perf_counter

from domain.recognition.plane.calculators.plane_candidate_calculator import (
    PlaneCandidateCalculator,
)
from domain.recognition.plane.entities.plane_candidate import PlaneCandidate
from domain.recognition.plane.reports.plane_candidate_report import (
    PlaneCandidateReport,
)
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


class PlaneCandidateCapability:
    """Validate evidence and orchestrate plane-candidate generation."""

    def __init__(
        self,
        calculator: PlaneCandidateCalculator | None = None,
    ) -> None:
        self._calculator = calculator or PlaneCandidateCalculator()

    def execute(
        self,
        region: Region,
        analysis: RegionAnalysis,
        features: RegionFeatures,
        settings: PlaneCandidateSettings,
    ) -> PlaneCandidateReport:
        """Generate a candidate and package its validation warnings."""

        self._validate(region, analysis, features)
        started_at = perf_counter()
        candidate = self._calculator.calculate(
            region,
            analysis,
            features,
            settings,
        )
        execution_time = perf_counter() - started_at

        return PlaneCandidateReport(
            candidate=candidate,
            execution_time=execution_time,
            warnings=self._warnings(
                candidate,
                features,
                settings,
            ),
        )

    @staticmethod
    def _validate(
        region: Region,
        analysis: RegionAnalysis,
        features: RegionFeatures,
    ) -> None:
        """Validate consistency among region evidence inputs."""

        if analysis.triangle_count != len(region.triangle_indices):
            raise ValueError(
                "Region analysis triangle count does not match the region."
            )

        if analysis.area != region.area or features.area_score != analysis.area:
            raise ValueError("Region, analysis, and feature areas do not match.")

        values = (
            analysis.area,
            analysis.maximum_angular_deviation,
            features.planarity_score,
            features.normal_consistency,
            features.area_score,
            features.triangle_density,
        )

        if not all(isfinite(value) for value in values):
            raise ValueError("Plane-candidate evidence must be finite.")

        if not 0.0 <= features.planarity_score <= 1.0:
            raise ValueError("Planarity score must be between zero and one.")

        if not 0.0 <= features.normal_consistency <= 1.0:
            raise ValueError(
                "Normal consistency must be between zero and one."
            )

    @staticmethod
    def _warnings(
        candidate: PlaneCandidate,
        features: RegionFeatures,
        settings: PlaneCandidateSettings,
    ) -> tuple[str, ...]:
        """Return explicit warnings for evidence below thresholds."""

        warnings: list[str] = []

        if features.planarity_score < settings.minimum_planarity:
            warnings.append("Planarity is below the configured minimum.")

        if candidate.area < settings.minimum_area:
            warnings.append("Region area is below the configured minimum.")

        if candidate.triangle_count < settings.minimum_triangle_count:
            warnings.append(
                "Triangle count is below the configured minimum."
            )

        if candidate.confidence < settings.minimum_confidence:
            warnings.append("Candidate confidence is below the configured minimum.")

        return tuple(warnings)
