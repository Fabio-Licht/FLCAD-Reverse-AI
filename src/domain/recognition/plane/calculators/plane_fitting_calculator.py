"""Strategy-driven mathematical plane-fitting calculation."""

from __future__ import annotations

from math import sqrt
from typing import Any

from domain.mesh.bounding_box import Point3D
from domain.mesh.mesh_entity import MeshEntity
from domain.recognition.plane.entities.plane import Plane
from domain.recognition.plane.entities.plane_candidate import PlaneCandidate
from domain.recognition.plane.strategies.least_squares_plane_fitting_strategy import (
    LeastSquaresPlaneFittingStrategy,
)
from domain.recognition.plane.strategies.plane_fitting_strategy import (
    PlaneFittingStrategy,
)
from domain.recognition.plane.value_objects.plane_fit_statistics import (
    PlaneFitStatistics,
)
from domain.recognition.plane.value_objects.plane_fitting_settings import (
    PlaneFittingSettings,
)


class PlaneFittingCalculator:
    """Resolve support points and delegate plane fitting to a strategy."""

    def __init__(
        self,
        strategy: PlaneFittingStrategy | None = None,
    ) -> None:
        self._strategy = strategy or LeastSquaresPlaneFittingStrategy()

    def calculate(
        self,
        mesh: MeshEntity,
        candidate: PlaneCandidate,
        settings: PlaneFittingSettings,
    ) -> tuple[Plane, PlaneFitStatistics]:
        """Return a fitted plane and residual statistics."""

        if settings.fitting_method != "least_squares":
            raise ValueError(
                f"Unsupported plane fitting method: {settings.fitting_method}"
            )

        points = self._support_points(mesh, candidate)
        origin, normal, residuals, inliers = self._strategy.fit(
            points,
            settings,
        )
        inlier_errors = tuple(
            error
            for error, is_inlier in zip(residuals, inliers)
            if is_inlier
        )
        inlier_count = len(inlier_errors)
        statistics = PlaneFitStatistics(
            rms_error=sqrt(
                sum(error * error for error in inlier_errors)
                / inlier_count
            ),
            maximum_error=max(inlier_errors),
            average_error=sum(inlier_errors) / inlier_count,
            point_count=len(points),
            inlier_count=inlier_count,
            outlier_count=len(points) - inlier_count,
        )
        plane = Plane(
            source_region_id=candidate.region.id,
            origin=origin,
            normal=normal,
            support_area=candidate.area,
            bounding_box=candidate.bounding_box,
        )

        return plane, statistics

    def _support_points(
        self,
        mesh: MeshEntity,
        candidate: PlaneCandidate,
    ) -> tuple[Point3D, ...]:
        """Resolve unique source-mesh vertices referenced by the region."""

        if mesh.mesh_data is None:
            raise ValueError("Plane fitting requires mesh data.")

        vertices = mesh.mesh_data.vertices
        faces = mesh.mesh_data.faces

        if not self._is_indexed(vertices) or not self._is_indexed(faces):
            raise TypeError("Mesh vertices and faces must support indexed access.")

        vertex_indices: set[int] = set()

        for triangle_index in candidate.region.triangle_indices:
            if triangle_index < 0 or triangle_index >= len(faces):
                raise IndexError(
                    "Plane candidate references a triangle outside the mesh."
                )

            face = faces[triangle_index]

            if not self._is_indexed(face) or len(face) != 3:
                raise ValueError("Plane fitting requires triangular faces.")

            for value in face:
                vertex_index = int(value)

                if vertex_index < 0 or vertex_index >= len(vertices):
                    raise IndexError(
                        "Triangle references a vertex outside the mesh."
                    )

                vertex_indices.add(vertex_index)

        return tuple(
            self._point(vertices[index])
            for index in sorted(vertex_indices)
        )

    @staticmethod
    def _point(value: object) -> Point3D:
        """Convert one backend-neutral mesh vertex to a point."""

        if not PlaneFittingCalculator._is_indexed(value) or len(value) != 3:
            raise ValueError("Mesh vertices must contain three coordinates.")

        return float(value[0]), float(value[1]), float(value[2])

    @staticmethod
    def _is_indexed(value: object) -> bool:
        """Return whether a value provides sized indexed access."""

        return hasattr(value, "__len__") and hasattr(value, "__getitem__")
