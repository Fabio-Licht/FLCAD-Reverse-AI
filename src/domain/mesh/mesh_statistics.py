"""Engineering metrics associated with a mesh."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MeshStatistics:
    """Store calculated mesh metrics without owning mesh geometry."""

    vertex_count: int
    face_count: int
    triangle_count: int
    surface_area: float | None = None
    volume: float | None = None
