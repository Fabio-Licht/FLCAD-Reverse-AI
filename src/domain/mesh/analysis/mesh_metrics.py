"""Immutable metrics produced by mesh analysis."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MeshMetrics:
    """Store topology counts calculated from mesh data."""

    vertex_count: int
    face_count: int
    triangle_count: int
