"""Orchestration capability for engineering plane recognition."""

from __future__ import annotations

from math import isfinite
from time import perf_counter

from domain.recognition.plane.calculators.plane_recognition_calculator import (
    PlaneRecognitionCalculator,
)
from domain.recognition.plane.entities.plane import Plane
from domain.recognition.plane.reports.plane_recognition_report import (
    PlaneRecognitionReport,
)
from domain.recognition.plane.value_objects.plane_fit_statistics import (
    PlaneFitStatistics,
)
from domain.recognition.plane.value_objects.plane_recognition_settings import (
    PlaneRecognitionSettings,
)
from domain.recognition.plane.value_objects.plane_provenance import (
    PlaneProvenance,
)


class PlaneRecognitionCapability:
    """Validate fit evidence and orchestrate plane recognition."""

    def __init__(
        self,
        calculator: PlaneRecognitionCalculator | None = None,
    ) -> None:
        self._calculator = calculator or PlaneRecognitionCalculator()

    def execute(
        self,
        plane: Plane,
        provenance: PlaneProvenance,
        settings: PlaneRecognitionSettings,
    ) -> PlaneRecognitionReport:
        """Evaluate a fitted plane and return its recognition report."""

        self._validate(plane, provenance)
        started_at = perf_counter()
        recognized_plane = self._calculator.calculate(
            plane,
            provenance,
            settings,
        )
        execution_time = perf_counter() - started_at

        return PlaneRecognitionReport(
            recognized_plane=recognized_plane,
            execution_time=execution_time,
            warnings=recognized_plane.warnings,
        )

    @staticmethod
    def _validate(plane: Plane, provenance: PlaneProvenance) -> None:
        """Validate plane and statistics without recognition calculations."""

        statistics = provenance.statistics

        if plane.source_region_id != provenance.region.id:
            raise ValueError("Plane source does not match its provenance region.")

        if provenance.candidate.region is not provenance.region:
            raise ValueError(
                "Plane candidate does not own the provenance region."
            )

        numeric_values = (
            plane.support_area,
            statistics.rms_error,
            statistics.maximum_error,
            statistics.average_error,
        )

        if not all(isfinite(value) for value in numeric_values):
            raise ValueError("Plane recognition inputs must be finite.")

        if plane.support_area < 0.0:
            raise ValueError("Plane support area must not be negative.")

        if any(
            error < 0.0
            for error in (
                statistics.rms_error,
                statistics.maximum_error,
                statistics.average_error,
            )
        ):
            raise ValueError("Plane fitting errors must not be negative.")

        if statistics.point_count < 1:
            raise ValueError("Plane fit must contain at least one point.")

        if not 0 <= statistics.inlier_count <= statistics.point_count:
            raise ValueError("Plane fit contains an invalid inlier count.")

        if statistics.outlier_count != (
            statistics.point_count - statistics.inlier_count
        ):
            raise ValueError("Plane fit point classifications are inconsistent.")
