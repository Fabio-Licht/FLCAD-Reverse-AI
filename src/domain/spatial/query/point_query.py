"""Immutable point-query value object."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from domain.mesh.bounding_box import Point3D


@dataclass(frozen=True, slots=True)
class PointQuery:
    """Describe a point query with an optional spatial tolerance."""

    point: Point3D
    tolerance: float | None = None

    def __post_init__(self) -> None:
        """Validate point coordinates and optional tolerance."""

        if len(self.point) != 3 or not all(
            isfinite(value) for value in self.point
        ):
            raise ValueError("A point query requires a finite 3D point.")

        if self.tolerance is not None and (
            not isfinite(self.tolerance) or self.tolerance < 0.0
        ):
            raise ValueError(
                "Point-query tolerance must be finite and non-negative."
            )
