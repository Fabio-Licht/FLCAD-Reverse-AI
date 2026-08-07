"""Axis-aligned bounds for mesh-domain data."""

from __future__ import annotations

from dataclasses import dataclass


Point3D = tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Represent immutable axis-aligned three-dimensional bounds."""

    minimum: Point3D
    maximum: Point3D

    def __post_init__(self) -> None:
        """Validate that each minimum coordinate precedes its maximum."""

        if any(
            minimum > maximum
            for minimum, maximum in zip(self.minimum, self.maximum)
        ):
            raise ValueError(
                "Bounding-box minimum coordinates must not exceed maxima."
            )
