"""Immutable bounding-box-query value object."""

from __future__ import annotations

from dataclasses import dataclass

from domain.mesh.bounding_box import BoundingBox


@dataclass(frozen=True, slots=True)
class BoundingBoxQuery:
    """Describe an axis-aligned bounding-box query."""

    bounding_box: BoundingBox
