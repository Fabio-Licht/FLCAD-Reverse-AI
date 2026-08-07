"""Engineering evaluation of a mathematically fitted plane."""

from __future__ import annotations

from domain.recognition.plane.entities.plane import Plane
from domain.recognition.plane.entities.recognized_plane import (
    PlaneEngineeringQuality,
    RecognizedPlane,
)
from domain.recognition.plane.value_objects.plane_fit_statistics import (
    PlaneFitStatistics,
)
from domain.recognition.plane.value_objects.plane_provenance import (
    PlaneProvenance,
)
from domain.recognition.plane.value_objects.plane_recognition_settings import (
    PlaneRecognitionSettings,
)


class PlaneRecognitionCalculator:
    """Evaluate fit evidence and decide engineering-plane acceptance."""

    def calculate(
        self,
        plane: Plane,
        provenance: PlaneProvenance,
        settings: PlaneRecognitionSettings,
    ) -> RecognizedPlane:
        """Return an explainable engineering recognition decision."""

        statistics = provenance.statistics
        inlier_ratio = statistics.inlier_count / statistics.point_count
        rms_quality = self._error_quality(
            statistics.rms_error,
            settings.maximum_rms_error,
        )
        average_quality = self._error_quality(
            statistics.average_error,
            settings.maximum_average_error,
        )
        area_quality = min(
            1.0,
            plane.support_area / settings.minimum_support_area,
        )
        confidence = min(
            rms_quality,
            average_quality,
            area_quality,
            inlier_ratio,
        )
        warnings = self._warnings(
            plane,
            statistics,
            settings,
            inlier_ratio,
            confidence,
        )
        engineering_compliant = all(
            (
                statistics.rms_error <= settings.maximum_rms_error,
                statistics.average_error <= settings.maximum_average_error,
                plane.support_area >= settings.minimum_support_area,
                inlier_ratio >= settings.minimum_inlier_ratio,
            )
        )
        engineering_quality = (
            PlaneEngineeringQuality.COMPLIANT
            if engineering_compliant
            else PlaneEngineeringQuality.NON_COMPLIANT
        )

        return RecognizedPlane(
            plane=plane,
            provenance=provenance,
            recognition_confidence=confidence,
            engineering_quality=engineering_quality,
            accepted=(
                engineering_compliant
                and confidence >= settings.minimum_confidence
            ),
            warnings=warnings,
        )

    @staticmethod
    def _error_quality(error: float, maximum_error: float) -> float:
        """Convert an error limit into a bounded quality contribution."""

        if error <= maximum_error:
            return 1.0

        return maximum_error / error

    @staticmethod
    def _warnings(
        plane: Plane,
        statistics: PlaneFitStatistics,
        settings: PlaneRecognitionSettings,
        inlier_ratio: float,
        confidence: float,
    ) -> tuple[str, ...]:
        """Return explicit reasons for evidence below thresholds."""

        warnings: list[str] = []

        if statistics.rms_error > settings.maximum_rms_error:
            warnings.append("RMS fitting error exceeds the configured maximum.")

        if statistics.average_error > settings.maximum_average_error:
            warnings.append(
                "Average fitting error exceeds the configured maximum."
            )

        if plane.support_area < settings.minimum_support_area:
            warnings.append("Plane support area is below the configured minimum.")

        if inlier_ratio < settings.minimum_inlier_ratio:
            warnings.append("Inlier ratio is below the configured minimum.")

        if confidence < settings.minimum_confidence:
            warnings.append("Recognition confidence is below the configured minimum.")

        return tuple(warnings)
