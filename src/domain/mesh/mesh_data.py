"""Backend-neutral mesh data container."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class MeshData:
    """Store mesh topology and optional vertex-normal data."""

    vertices: Any
    faces: Any
    normals: Any | None = None
