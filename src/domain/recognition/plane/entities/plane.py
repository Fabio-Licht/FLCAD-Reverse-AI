"""Immutable mathematical plane produced by geometric fitting."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from domain.mesh.bounding_box import BoundingBox, Point3D


@dataclass(frozen=True, slots=True)
class Plane:
    """Represent a fitted finite-support mathematical plane."""

    source_region_id: UUID
    origin: Point3D
    normal: Point3D
    support_area: float
    bounding_box: BoundingBox
    id: UUID = field(default_factory=uuid4)
