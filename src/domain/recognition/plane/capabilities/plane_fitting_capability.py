"""Orchestration capability for mathematical plane fitting."""

from __future__ import annotations

from time import perf_counter

from domain.mesh.mesh_entity import MeshEntity
from domain.recognition.plane.calculators.plane_fitting_calculator import (
    PlaneFittingCalculator,
)
from domain.recognition.plane.entities.plane_candidate import PlaneCandidate
from domain.recognition.plane.reports.plane_fitting_report import (
    PlaneFittingReport,
)
from domain.recognition.plane.value_objects.plane_fit_statistics import (
    PlaneFitStatistics,
)
from domain.recognition.plane.value_objects.plane_fitting_settings import (
    PlaneFittingSettings,
)
from domain.recognition.plane.value_objects.plane_provenance import (
    PlaneProvenance,
)


class PlaneFittingCapability:
    """Validate inputs and orchestrate strategy-driven plane fitting."""

    def __init__(
        self,
        calculator: PlaneFittingCalculator | None = None,
    ) -> None:
        self._calculator = calculator or PlaneFittingCalculator()

    def execute(
        self,
        mesh: MeshEntity,
        candidate: PlaneCandidate,
        settings: PlaneFittingSettings,
    ) -> PlaneFittingReport:
        """Fit a candidate and package its numerical diagnostics."""

        self._validate(mesh, candidate)
        started_at = perf_counter()
        plane, statistics = self._calculator.calculate(
            mesh,
            candidate,
            settings,
        )
        execution_time = perf_counter() - started_at
        provenance = PlaneProvenance(
            mesh=mesh,
            region=candidate.region,
            candidate=candidate,
            statistics=statistics,
        )

        return PlaneFittingReport(
            plane=plane,
            statistics=statistics,
            provenance=provenance,
            execution_time=execution_time,
            warnings=self._warnings(statistics, settings),
        )

    @staticmethod
    def _validate(mesh: MeshEntity, candidate: PlaneCandidate) -> None:
        """Validate source availability and candidate traceability."""

        if mesh.mesh_data is None:
            raise ValueError("Plane fitting requires mesh data.")

        if not candidate.region.triangle_indices:
            raise ValueError("Plane candidate region contains no triangles.")

        if candidate.triangle_count != len(candidate.region.triangle_indices):
            raise ValueError(
                "Plane candidate triangle count does not match its region."
            )

        if candidate.area != candidate.region.area:
            raise ValueError("Plane candidate area does not match its region.")

    @staticmethod
    def _warnings(
        statistics: PlaneFitStatistics,
        settings: PlaneFittingSettings,
    ) -> tuple[str, ...]:
        """Return numerical warnings without accepting or rejecting the fit."""

        warnings: list[str] = []

        if statistics.maximum_error > settings.tolerance:
            warnings.append("Maximum inlier error exceeds the fitting tolerance.")

        if statistics.outlier_count > 0:
            warnings.append("Plane fitting excluded one or more outlier points.")

        return tuple(warnings)
