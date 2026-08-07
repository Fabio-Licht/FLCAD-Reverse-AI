"""Immutable result returned by the Spatial Query Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from domain.spatial.objects.spatial_object import SpatialObject


SpatialObjectT = TypeVar("SpatialObjectT", bound=SpatialObject)


@dataclass(frozen=True, slots=True)
class SpatialQueryResult(Generic[SpatialObjectT]):
    """Store query matches and backend-neutral execution diagnostics."""

    objects: tuple[SpatialObjectT, ...]
    visited_nodes: int
    execution_time: float
    candidate_count: int
