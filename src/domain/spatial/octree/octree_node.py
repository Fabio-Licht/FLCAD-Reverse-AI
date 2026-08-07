"""Storage node used by the generic octree."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from domain.mesh.bounding_box import BoundingBox
from domain.spatial.objects.spatial_object import SpatialObject


SpatialObjectT = TypeVar("SpatialObjectT", bound=SpatialObject)


@dataclass(slots=True)
class OctreeNode(Generic[SpatialObjectT]):
    """Contain spatial objects and optional child nodes."""

    bounding_box: BoundingBox
    objects: list[SpatialObjectT] = field(default_factory=list)
    children: list[OctreeNode[SpatialObjectT]] = field(
        default_factory=list
    )
    depth: int = 0
