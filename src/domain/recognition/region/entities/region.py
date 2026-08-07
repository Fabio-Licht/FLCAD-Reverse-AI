"""Domain entity representing a segmented mesh region."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from domain.mesh.bounding_box import BoundingBox, Point3D


@dataclass(frozen=True, slots=True)
class Region:
    """Represent an immutable snapshot of a segmented mesh region."""

    triangle_indices: tuple[int, ...]
    bounding_box: BoundingBox
    average_normal: Point3D
    area: float
    neighbors: frozenset[UUID] = field(default_factory=frozenset)
    id: UUID = field(default_factory=uuid4)
