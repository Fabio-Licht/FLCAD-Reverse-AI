"""Backend-independent spatial query definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from domain.mesh.bounding_box import BoundingBox, Point3D


class SpatialQueryType(str, Enum):
    """Identify supported and reserved spatial query families."""

    BOUNDING_BOX = "bounding_box"
    POINT = "point"
    RADIUS = "radius"
    RAY = "ray"
    PLANE = "plane"
    FRUSTUM = "frustum"


@dataclass(frozen=True, slots=True)
class SpatialQuery:
    """Describe a spatial query evaluated against bounding boxes."""

    query_type: SpatialQueryType
    bounds: BoundingBox | None = None
    center: Point3D | None = None
    radius: float | None = None

    def __post_init__(self) -> None:
        """Validate the parameters required by supported query types."""

        if self.query_type is SpatialQueryType.BOUNDING_BOX:
            if self.bounds is None:
                raise ValueError("A bounding-box query requires bounds.")
            return

        if self.query_type is SpatialQueryType.POINT:
            self._validate_center()
            return

        if self.query_type is SpatialQueryType.RADIUS:
            self._validate_center()

            if (
                self.radius is None
                or not isfinite(self.radius)
                or self.radius < 0.0
            ):
                raise ValueError(
                    "A radius query requires a finite, non-negative radius."
                )
            return

        raise NotImplementedError(
            f"{self.query_type.value} queries are reserved for future use."
        )

    @classmethod
    def for_bounding_box(cls, bounds: BoundingBox) -> SpatialQuery:
        """Create a bounding-box intersection query."""

        return cls(
            query_type=SpatialQueryType.BOUNDING_BOX,
            bounds=bounds,
        )

    @classmethod
    def for_point(cls, point: Point3D) -> SpatialQuery:
        """Create a point-containment query."""

        return cls(
            query_type=SpatialQueryType.POINT,
            center=point,
        )

    @classmethod
    def for_radius(
        cls,
        center: Point3D,
        radius: float,
    ) -> SpatialQuery:
        """Create a spherical radius query."""

        return cls(
            query_type=SpatialQueryType.RADIUS,
            center=center,
            radius=radius,
        )

    def intersects(self, bounds: BoundingBox) -> bool:
        """Return whether axis-aligned bounds satisfy this query."""

        if self.query_type is SpatialQueryType.BOUNDING_BOX:
            assert self.bounds is not None
            return self._boxes_intersect(self.bounds, bounds)

        if self.query_type is SpatialQueryType.POINT:
            assert self.center is not None
            return all(
                minimum <= coordinate <= maximum
                for coordinate, minimum, maximum in zip(
                    self.center,
                    bounds.minimum,
                    bounds.maximum,
                )
            )

        if self.query_type is SpatialQueryType.RADIUS:
            assert self.center is not None
            assert self.radius is not None

            distance_squared = sum(
                (
                    minimum - coordinate
                    if coordinate < minimum
                    else coordinate - maximum
                    if coordinate > maximum
                    else 0.0
                )
                ** 2
                for coordinate, minimum, maximum in zip(
                    self.center,
                    bounds.minimum,
                    bounds.maximum,
                )
            )
            return distance_squared <= self.radius * self.radius

        return False

    def _validate_center(self) -> None:
        """Validate a three-dimensional finite query center."""

        if self.center is None or len(self.center) != 3:
            raise ValueError("A spatial query requires a 3D center.")

        if not all(isfinite(value) for value in self.center):
            raise ValueError("A query center must contain finite values.")

    @staticmethod
    def _boxes_intersect(
        first: BoundingBox,
        second: BoundingBox,
    ) -> bool:
        """Return whether two axis-aligned bounding boxes intersect."""

        return all(
            first_minimum <= second_maximum
            and second_minimum <= first_maximum
            for first_minimum, first_maximum, second_minimum, second_maximum
            in zip(
                first.minimum,
                first.maximum,
                second.minimum,
                second.maximum,
            )
        )
