"""Immutable radius-query value object."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from domain.mesh.bounding_box import Point3D


@dataclass(frozen=True, slots=True)
class RadiusQuery:
    """Describe a spherical query by its center and radius."""

    center: Point3D
    radius: float

    def __post_init__(self) -> None:
        """Validate the spherical query parameters."""

        if len(self.center) != 3 or not all(
            isfinite(value) for value in self.center
        ):
            raise ValueError("A radius query requires a finite 3D center.")

        if not isfinite(self.radius) or self.radius < 0.0:
            raise ValueError(
                "A radius query requires a finite, non-negative radius."
            )
