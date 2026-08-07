"""Stateless structural mesh-quality evaluation."""

from __future__ import annotations

from domain.mesh.analysis.mesh_metrics import MeshMetrics
from domain.mesh.analysis.mesh_quality import MeshQuality
from domain.mesh.bounding_box import BoundingBox


class MeshQualityEvaluator:
    """Evaluate structural analyzability from calculated mesh results."""

    def evaluate(
        self,
        metrics: MeshMetrics,
        bounding_box: BoundingBox | None,
    ) -> tuple[MeshQuality, tuple[str, ...]]:
        """Return a quality classification and its warnings."""

        warnings: list[str] = []

        if metrics.vertex_count == 0:
            warnings.append("Mesh contains no vertices.")
            return MeshQuality.EMPTY, tuple(warnings)

        if bounding_box is None:
            warnings.append("Mesh bounding box is unavailable.")

        if metrics.face_count == 0:
            warnings.append("Mesh contains no faces.")

        if (
            metrics.face_count > 0
            and metrics.triangle_count < metrics.face_count
        ):
            warnings.append("Mesh contains non-triangular faces.")

        if bounding_box is None or metrics.face_count == 0:
            return MeshQuality.INCOMPLETE, tuple(warnings)

        return MeshQuality.ANALYZABLE, tuple(warnings)
