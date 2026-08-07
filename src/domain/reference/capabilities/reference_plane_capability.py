"""Orchestration capability for engineering reference-plane creation."""

from __future__ import annotations

from time import perf_counter

from domain.recognition.plane.entities.recognized_plane import RecognizedPlane
from domain.reference.factories.reference_plane_factory import (
    ReferencePlaneFactory,
)
from domain.reference.managers.reference_manager import ReferenceManager
from domain.reference.reports.reference_plane_report import (
    ReferencePlaneReport,
)
from domain.reference.value_objects.reference_plane_settings import (
    ReferencePlaneSettings,
)


class ReferencePlaneCapability:
    """Validate, create, and register an engineering reference plane."""

    def __init__(
        self,
        manager: ReferenceManager,
        factory: ReferencePlaneFactory | None = None,
    ) -> None:
        self._manager = manager
        self._factory = factory or ReferencePlaneFactory()

    def execute(
        self,
        recognized_plane: RecognizedPlane,
        settings: ReferencePlaneSettings,
    ) -> ReferencePlaneReport:
        """Create and register a reference from an accepted plane."""

        self._validate(recognized_plane)
        started_at = perf_counter()
        reference_plane = self._factory.create(recognized_plane, settings)
        registered = self._manager.add(reference_plane)
        execution_time = perf_counter() - started_at

        if not registered:
            raise ValueError("Reference plane identity is already registered.")

        return ReferencePlaneReport(
            reference_plane=reference_plane,
            execution_time=execution_time,
            warnings=recognized_plane.warnings,
        )

    @staticmethod
    def _validate(recognized_plane: RecognizedPlane) -> None:
        """Validate recognition acceptance and provenance consistency."""

        if not recognized_plane.accepted:
            raise ValueError(
                "Only an accepted recognized plane can become a reference."
            )

        provenance = recognized_plane.provenance

        if recognized_plane.plane.source_region_id != provenance.region.id:
            raise ValueError("Recognized plane provenance region is inconsistent.")

        if provenance.candidate.region is not provenance.region:
            raise ValueError("Plane candidate provenance is inconsistent.")
