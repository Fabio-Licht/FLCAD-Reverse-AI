"""Structural contract for objects accepted by spatial indexes."""

from __future__ import annotations

from typing import Protocol

from domain.mesh.bounding_box import BoundingBox


class SpatialObject(Protocol):
    """Expose the axis-aligned bounds of a spatial object."""

    def bounding_box(self) -> BoundingBox:
        """Return the object's current axis-aligned bounds."""

        ...
