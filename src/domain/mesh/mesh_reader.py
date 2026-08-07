"""Abstract ingestion boundary for mesh data."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from domain.mesh.mesh_data import MeshData


class MeshReader(ABC):
    """Define the interface implemented by mesh-format readers."""

    @abstractmethod
    def read(self, source: str | Path) -> MeshData:
        """Read a mesh source and return backend-neutral mesh data."""

        raise NotImplementedError
