"""Orthogonal least-squares strategy for mathematical planes."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from domain.mesh.bounding_box import Point3D
from domain.recognition.plane.strategies.plane_fitting_strategy import (
    PlaneFittingStrategy,
    PlaneStrategyResult,
)
from domain.recognition.plane.value_objects.plane_fitting_settings import (
    PlaneFittingSettings,
)


class LeastSquaresPlaneFittingStrategy(PlaneFittingStrategy):
    """Fit a plane by minimizing orthogonal squared point distances."""

    def fit(
        self,
        points: Sequence[Point3D],
        settings: PlaneFittingSettings,
    ) -> PlaneStrategyResult:
        """Fit points and optionally reject tolerance-based outliers."""

        point_array = np.asarray(points, dtype=float)

        if point_array.ndim != 2 or point_array.shape[1] != 3:
            raise ValueError("Plane fitting requires three-dimensional points.")

        if len(point_array) < 3:
            raise ValueError("Plane fitting requires at least three points.")

        if not np.all(np.isfinite(point_array)):
            raise ValueError("Plane fitting requires finite support points.")

        inliers = np.ones(len(point_array), dtype=bool)

        for _ in range(settings.maximum_iterations):
            origin, normal = self._fit_inliers(point_array[inliers])
            residuals = self._residuals(point_array, origin, normal)

            if not settings.outlier_rejection:
                break

            updated_inliers = residuals <= settings.tolerance

            if np.count_nonzero(updated_inliers) < 3:
                raise ValueError(
                    "Outlier rejection left fewer than three support points."
                )

            if np.array_equal(updated_inliers, inliers):
                inliers = updated_inliers
                break

            inliers = updated_inliers

        origin, normal = self._fit_inliers(point_array[inliers])
        residuals = self._residuals(point_array, origin, normal)

        return (
            self._point(origin),
            self._point(normal),
            tuple(float(value) for value in residuals),
            tuple(bool(value) for value in inliers),
        )

    def _fit_inliers(
        self,
        points: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return centroid and stable least-squares normal."""

        origin = np.mean(points, axis=0)
        centered = points - origin
        covariance = centered.T @ centered
        eigenvalues, eigenvectors = np.linalg.eigh(covariance)

        if eigenvalues[1] <= np.finfo(float).eps:
            raise ValueError("Plane support points are geometrically collinear.")

        normal = eigenvectors[:, 0]
        dominant_axis = int(np.argmax(np.abs(normal)))

        if normal[dominant_axis] < 0.0:
            normal = -normal

        return origin, normal

    @staticmethod
    def _residuals(
        points: np.ndarray,
        origin: np.ndarray,
        normal: np.ndarray,
    ) -> np.ndarray:
        """Return absolute orthogonal point-to-plane distances."""

        return np.abs((points - origin) @ normal)

    @staticmethod
    def _point(value: np.ndarray) -> Point3D:
        """Convert a three-component array to a domain point."""

        return float(value[0]), float(value[1]), float(value[2])
