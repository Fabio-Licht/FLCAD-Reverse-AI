"""Stateless axis-aligned bounding-box calculation."""

from __future__ import annotations

from math import isfinite
from typing import Iterable

from domain.mesh.bounding_box import BoundingBox, Point3D
from domain.mesh.mesh_data import MeshData


class BoundingBoxCalculator:
    """Calculate bounds from backend-neutral mesh vertices."""

    def calculate(self, mesh_data: MeshData | None) -> BoundingBox | None:
        """Return mesh bounds, or ``None`` when no vertices are available."""

        if mesh_data is None:
            return None

        vertices = iter(mesh_data.vertices)

        try:
            first = self._point(next(vertices))
        except StopIteration:
            return None

        minimum = list(first)
        maximum = list(first)

        for vertex in vertices:
            point = self._point(vertex)

            for axis, coordinate in enumerate(point):
                minimum[axis] = min(minimum[axis], coordinate)
                maximum[axis] = max(maximum[axis], coordinate)

        return BoundingBox(
            minimum=(minimum[0], minimum[1], minimum[2]),
            maximum=(maximum[0], maximum[1], maximum[2]),
        )

    @staticmethod
    def _point(vertex: Iterable[float]) -> Point3D:
        """Convert and validate one three-dimensional vertex."""

        coordinates = tuple(float(value) for value in vertex)

        if len(coordinates) != 3:
            raise ValueError("Mesh vertices must contain three coordinates.")

        if not all(isfinite(value) for value in coordinates):
            raise ValueError("Mesh vertices must contain finite coordinates.")

        return coordinates[0], coordinates[1], coordinates[2]
