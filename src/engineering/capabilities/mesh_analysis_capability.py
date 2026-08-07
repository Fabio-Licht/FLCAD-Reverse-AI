"""Orchestration capability for mesh-domain analysis."""

from __future__ import annotations

from time import perf_counter

from domain.mesh.analysis.calculators.bounding_box_calculator import (
    BoundingBoxCalculator,
)
from domain.mesh.analysis.calculators.mesh_metric_calculator import (
    MeshMetricCalculator,
)
from domain.mesh.analysis.calculators.mesh_quality_evaluator import (
    MeshQualityEvaluator,
)
from domain.mesh.analysis.mesh_analysis_report import MeshAnalysisReport
from domain.mesh.mesh_entity import MeshEntity


class MeshAnalysisCapability:
    """Coordinate stateless calculators into one mesh analysis report."""

    def __init__(
        self,
        bounding_box_calculator: BoundingBoxCalculator | None = None,
        metric_calculator: MeshMetricCalculator | None = None,
        quality_evaluator: MeshQualityEvaluator | None = None,
    ) -> None:
        self._bounding_box_calculator = (
            bounding_box_calculator or BoundingBoxCalculator()
        )
        self._metric_calculator = (
            metric_calculator or MeshMetricCalculator()
        )
        self._quality_evaluator = (
            quality_evaluator or MeshQualityEvaluator()
        )

    def execute(self, mesh: MeshEntity) -> MeshAnalysisReport:
        """Analyze a mesh entity and return an immutable report."""

        started_at = perf_counter()

        bounding_box = self._bounding_box_calculator.calculate(
            mesh.mesh_data
        )
        metrics = self._metric_calculator.calculate(mesh.mesh_data)
        quality, warnings = self._quality_evaluator.evaluate(
            metrics,
            bounding_box,
        )

        return MeshAnalysisReport(
            mesh_uuid=mesh.uuid,
            bounding_box=bounding_box,
            metrics=metrics,
            quality=quality,
            execution_time=perf_counter() - started_at,
            warnings=warnings,
        )
