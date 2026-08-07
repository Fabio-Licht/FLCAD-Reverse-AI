"""Stateless topology metric calculation for mesh data."""

from __future__ import annotations

from collections.abc import Sized

from domain.mesh.analysis.mesh_metrics import MeshMetrics
from domain.mesh.mesh_data import MeshData


class MeshMetricCalculator:
    """Calculate topology counts without interpreting mesh quality."""

    def calculate(self, mesh_data: MeshData | None) -> MeshMetrics:
        """Return vertex, face, and triangulated-face counts."""

        if mesh_data is None:
            return MeshMetrics(
                vertex_count=0,
                face_count=0,
                triangle_count=0,
            )

        vertex_count = self._length(mesh_data.vertices, "vertices")
        face_count = self._length(mesh_data.faces, "faces")
        triangle_count = sum(
            1
            for face in mesh_data.faces
            if isinstance(face, Sized) and len(face) == 3
        )

        return MeshMetrics(
            vertex_count=vertex_count,
            face_count=face_count,
            triangle_count=triangle_count,
        )

    @staticmethod
    def _length(values: object, label: str) -> int:
        """Return the size of a mesh collection."""

        if not isinstance(values, Sized):
            raise TypeError(f"Mesh {label} must be a sized collection.")

        return len(values)
