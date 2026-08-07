"""Starting element for a region-growing operation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegionSeed:
    """Identify the triangle from which region growth starts."""

    triangle_index: int

    def __post_init__(self) -> None:
        """Validate the triangle index."""

        if self.triangle_index < 0:
            raise ValueError("Region seed triangle index must not be negative.")
