"""Stateless calculation of derived mesh-region metrics."""

from __future__ import annotations

from collections import Counter
from math import acos, degrees, isfinite, sqrt
from typing import Any

from domain.mesh.bounding_box import Point3D
from domain.mesh.mesh_entity import MeshEntity
from domain.recognition.region.entities.region import Region
from domain.recognition.region.value_objects.region_analysis import (
    RegionAnalysis,
)


class RegionAnalysisCalculator:
    """Calculate geometric evidence without modifying the source region."""

    def calculate(
        self,
        mesh: MeshEntity,
        region: Region,
    ) -> RegionAnalysis:
        """Return derived metrics for a region and its source mesh."""

        if mesh.mesh_data is None:
            raise ValueError("Region analysis requires mesh data.")

        vertices = mesh.mesh_data.vertices
        faces = mesh.mesh_data.faces

        if not self._is_indexed(vertices):
            raise TypeError("Mesh vertices must be an indexed collection.")

        if not self._is_indexed(faces):
            raise TypeError("Mesh faces must be an indexed collection.")

        if not region.triangle_indices:
            raise ValueError("Region analysis requires at least one triangle.")

        edge_counts: Counter[tuple[int, int]] = Counter()
        weighted_normals: list[tuple[Point3D, float]] = []

        for triangle_index in region.triangle_indices:
            if triangle_index < 0 or triangle_index >= len(faces):
                raise IndexError(
                    "Region references a triangle outside the source mesh."
                )

            indices = self._triangle_indices(faces[triangle_index], vertices)
            normal, triangle_area = self._normal_and_area(
                indices,
                vertices,
            )
            weighted_normals.append((normal, triangle_area))

            first, second, third = indices
            edge_counts.update(
                (
                    tuple(sorted((first, second))),
                    tuple(sorted((second, third))),
                    tuple(sorted((third, first))),
                )
            )

        average_normal, normal_variance = self._normal_distribution(
            weighted_normals
        )
        maximum_deviation = self._maximum_deviation(
            average_normal,
            weighted_normals,
        )

        return RegionAnalysis(
            average_normal=average_normal,
            normal_variance=normal_variance,
            maximum_angular_deviation=maximum_deviation,
            triangle_count=len(region.triangle_indices),
            boundary_edge_count=sum(
                1 for count in edge_counts.values() if count == 1
            ),
            area=region.area,
        )

    def _triangle_indices(
        self,
        face: object,
        vertices: Any,
    ) -> tuple[int, int, int]:
        """Return validated vertex indices for one triangular face."""

        if not self._is_indexed(face) or len(face) != 3:
            raise ValueError("Region analysis requires triangular faces.")

        indices = tuple(int(index) for index in face)

        if any(index < 0 or index >= len(vertices) for index in indices):
            raise IndexError("Triangle references a vertex outside the mesh.")

        return indices[0], indices[1], indices[2]

    def _normal_and_area(
        self,
        indices: tuple[int, int, int],
        vertices: Any,
    ) -> tuple[Point3D, float]:
        """Return the unit normal and area of one triangle."""

        first, second, third = (
            self._point(vertices[index])
            for index in indices
        )
        first_edge = self._subtract(second, first)
        second_edge = self._subtract(third, first)
        cross = self._cross(first_edge, second_edge)
        magnitude = self._length(cross)

        if magnitude == 0.0:
            return (0.0, 0.0, 0.0), 0.0

        return (
            tuple(component / magnitude for component in cross),
            magnitude / 2.0,
        )

    @classmethod
    def _normal_distribution(
        cls,
        weighted_normals: list[tuple[Point3D, float]],
    ) -> tuple[Point3D, float]:
        """Return area-weighted mean direction and spherical variance."""

        total_area = sum(area for _, area in weighted_normals)

        if total_area == 0.0:
            return (0.0, 0.0, 0.0), 1.0

        resultant = tuple(
            sum(normal[axis] * area for normal, area in weighted_normals)
            / total_area
            for axis in range(3)
        )
        resultant_length = cls._length(resultant)
        variance = max(0.0, min(1.0, 1.0 - resultant_length))

        if resultant_length == 0.0:
            return (0.0, 0.0, 0.0), variance

        return (
            tuple(component / resultant_length for component in resultant),
            variance,
        )

    @staticmethod
    def _maximum_deviation(
        average_normal: Point3D,
        weighted_normals: list[tuple[Point3D, float]],
    ) -> float:
        """Return the largest angular deviation from the mean normal."""

        valid_normals = (
            normal
            for normal, area in weighted_normals
            if area > 0.0
        )

        if average_normal == (0.0, 0.0, 0.0):
            return 180.0

        return max(
            (
                degrees(
                    acos(
                        max(
                            -1.0,
                            min(
                                1.0,
                                sum(
                                    first * second
                                    for first, second in zip(
                                        average_normal,
                                        normal,
                                    )
                                ),
                            ),
                        )
                    )
                )
                for normal in valid_normals
            ),
            default=180.0,
        )

    @staticmethod
    def _point(value: object) -> Point3D:
        """Convert and validate one mesh vertex."""

        if not RegionAnalysisCalculator._is_indexed(value) or len(value) != 3:
            raise ValueError("Mesh vertices must contain three coordinates.")

        point = tuple(float(coordinate) for coordinate in value)

        if not all(isfinite(coordinate) for coordinate in point):
            raise ValueError("Mesh vertices must contain finite coordinates.")

        return point[0], point[1], point[2]

    @staticmethod
    def _is_indexed(value: object) -> bool:
        """Return whether a value provides sized indexed access."""

        return hasattr(value, "__len__") and hasattr(value, "__getitem__")

    @staticmethod
    def _subtract(first: Point3D, second: Point3D) -> Point3D:
        """Subtract two points or vectors."""

        return tuple(a - b for a, b in zip(first, second))

    @staticmethod
    def _cross(first: Point3D, second: Point3D) -> Point3D:
        """Return the three-dimensional cross product."""

        return (
            first[1] * second[2] - first[2] * second[1],
            first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0],
        )

    @staticmethod
    def _length(vector: Point3D) -> float:
        """Return a vector's Euclidean length."""

        return sqrt(sum(component * component for component in vector))
