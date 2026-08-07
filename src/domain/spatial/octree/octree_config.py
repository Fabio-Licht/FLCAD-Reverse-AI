"""Configuration value object for the generic octree."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class OctreeConfig:
    """Define explicit octree subdivision limits."""

    max_depth: int
    max_objects_per_node: int
    minimum_cell_size: float

    def __post_init__(self) -> None:
        """Validate octree configuration values."""

        if self.max_depth < 0:
            raise ValueError("Octree maximum depth must not be negative.")

        if self.max_objects_per_node < 1:
            raise ValueError(
                "Octree node capacity must be greater than zero."
            )

        if (
            not isfinite(self.minimum_cell_size)
            or self.minimum_cell_size < 0.0
        ):
            raise ValueError(
                "Octree minimum cell size must be finite and non-negative."
            )
