"""Topology-based mesh region-growing calculation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from math import acos, degrees, isfinite, sqrt
from typing import Any

from domain.mesh.bounding_box import BoundingBox, Point3D
from domain.mesh.mesh_entity import MeshEntity
from domain.recognition.region.entities.region import Region
from domain.recognition.region.value_objects.region_seed import RegionSeed
from domain.recognition.region.value_objects.region_settings import (
    RegionSettings,
)


@dataclass(frozen=True, slots=True)
class _TriangleData:
    """Store geometry required internally during region growth."""

    indices: tuple[int, int, int]
    normal: Point3D
    centroid: Point3D
    area: float


class RegionGrowingCalculator:
    """Grow connected triangles using geometric threshold criteria."""

    def calculate(
        self,
        mesh: MeshEntity,
        seed: RegionSeed,
        settings: RegionSettings,
    ) -> Region:
        """Return the connected region grown from the supplied seed."""

        if mesh.mesh_data is None:
            raise ValueError("Region growing requires mesh data.")

        vertices = mesh.mesh_data.vertices
        faces = mesh.mesh_data.faces

        if not self._is_indexed(vertices):
            raise TypeError("Mesh vertices must be an indexed sequence.")

        if not self._is_indexed(faces):
            raise TypeError("Mesh faces must be an indexed sequence.")

        if seed.triangle_index >= len(faces):
            raise IndexError("Region seed triangle index is outside the mesh.")

        triangles = tuple(
            self._triangle_data(face, vertices)
            for face in faces
        )
        adjacency = self._build_adjacency(triangles)
        selected = self._grow(
            triangles,
            adjacency,
            seed.triangle_index,
            settings,
        )

        return self._create_region(selected, triangles, vertices)

    def _grow(
        self,
        triangles: tuple[_TriangleData, ...],
        adjacency: dict[int, set[int]],
        seed_index: int,
        settings: RegionSettings,
    ) -> tuple[int, ...]:
        """Traverse adjacent triangles that satisfy configured criteria."""

        accepted = {seed_index}
        pending = deque([seed_index])

        while pending:
            current_index = pending.popleft()
            current = triangles[current_index]

            for candidate_index in adjacency[current_index]:
                if candidate_index in accepted:
                    continue

                candidate = triangles[candidate_index]

                if not self._normal_is_compatible(
                    current.normal,
                    candidate.normal,
                    settings.normal_angle_tolerance,
                ):
                    continue

                if self._distance(
                    current.centroid,
                    candidate.centroid,
                ) > settings.maximum_distance:
                    continue

                accepted.add(candidate_index)
                pending.append(candidate_index)

        return tuple(sorted(accepted))

    def _create_region(
        self,
        triangle_indices: tuple[int, ...],
        triangles: tuple[_TriangleData, ...],
        vertices: Any,
    ) -> Region:
        """Create the immutable region snapshot from accepted triangles."""

        points = tuple(
            self._point(vertices[vertex_index])
            for triangle_index in triangle_indices
            for vertex_index in triangles[triangle_index].indices
        )
        minimum = tuple(min(point[axis] for point in points) for axis in range(3))
        maximum = tuple(max(point[axis] for point in points) for axis in range(3))
        area = sum(triangles[index].area for index in triangle_indices)
        weighted_normal = tuple(
            sum(
                triangles[index].normal[axis] * triangles[index].area
                for index in triangle_indices
            )
            for axis in range(3)
        )

        return Region(
            triangle_indices=triangle_indices,
            bounding_box=BoundingBox(minimum=minimum, maximum=maximum),
            average_normal=self._normalized(weighted_normal),
            area=area,
        )

    def _triangle_data(
        self,
        face: object,
        vertices: Any,
    ) -> _TriangleData:
        """Calculate the topology and geometry of one triangle."""

        if not self._is_indexed(face) or len(face) != 3:
            raise ValueError("Region growing requires triangular faces.")

        indices = tuple(int(index) for index in face)

        if any(index < 0 or index >= len(vertices) for index in indices):
            raise IndexError("Triangle references a vertex outside the mesh.")

        first, second, third = (
            self._point(vertices[index])
            for index in indices
        )
        first_edge = self._subtract(second, first)
        second_edge = self._subtract(third, first)
        cross = self._cross(first_edge, second_edge)
        magnitude = self._length(cross)
        normal = (
            (0.0, 0.0, 0.0)
            if magnitude == 0.0
            else tuple(component / magnitude for component in cross)
        )

        return _TriangleData(
            indices=(indices[0], indices[1], indices[2]),
            normal=normal,
            centroid=tuple(
                (first[axis] + second[axis] + third[axis]) / 3.0
                for axis in range(3)
            ),
            area=magnitude / 2.0,
        )

    @staticmethod
    def _build_adjacency(
        triangles: tuple[_TriangleData, ...],
    ) -> dict[int, set[int]]:
        """Build triangle adjacency from shared undirected edges."""

        edge_owners: dict[tuple[int, int], list[int]] = defaultdict(list)
        adjacency = {index: set() for index in range(len(triangles))}

        for triangle_index, triangle in enumerate(triangles):
            first, second, third = triangle.indices

            for edge in (
                (first, second),
                (second, third),
                (third, first),
            ):
                edge_owners[tuple(sorted(edge))].append(triangle_index)

        for owners in edge_owners.values():
            for position, first in enumerate(owners):
                for second in owners[position + 1:]:
                    adjacency[first].add(second)
                    adjacency[second].add(first)

        return adjacency

    @staticmethod
    def _normal_is_compatible(
        first: Point3D,
        second: Point3D,
        tolerance: float,
    ) -> bool:
        """Return whether two normals are within an angular tolerance."""

        if first == (0.0, 0.0, 0.0) or second == (0.0, 0.0, 0.0):
            return False

        dot = max(-1.0, min(1.0, sum(a * b for a, b in zip(first, second))))
        return degrees(acos(dot)) <= tolerance

    @staticmethod
    def _point(value: object) -> Point3D:
        """Convert and validate one backend-neutral mesh vertex."""

        if not RegionGrowingCalculator._is_indexed(value) or len(value) != 3:
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
        """Return the three-dimensional vector cross product."""

        return (
            first[1] * second[2] - first[2] * second[1],
            first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0],
        )

    @staticmethod
    def _length(vector: Point3D) -> float:
        """Return a vector's Euclidean length."""

        return sqrt(sum(component * component for component in vector))

    @classmethod
    def _normalized(cls, vector: Point3D) -> Point3D:
        """Return a stable normalized vector."""

        magnitude = cls._length(vector)

        if magnitude == 0.0:
            return 0.0, 0.0, 0.0

        return tuple(component / magnitude for component in vector)

    @staticmethod
    def _distance(first: Point3D, second: Point3D) -> float:
        """Return the Euclidean distance between two points."""

        return sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))
