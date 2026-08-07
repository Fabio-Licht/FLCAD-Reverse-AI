"""Immutable settings for recognition visualization."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class VisualizationSettings:
    """Configure recognition and reference viewport presentation."""

    region_opacity: float
    plane_opacity: float
    reference_opacity: float
    show_normals: bool
    show_labels: bool
    show_region_ids: bool

    def __post_init__(self) -> None:
        """Validate all visualization opacity values."""

        for name, value in (
            ("region_opacity", self.region_opacity),
            ("plane_opacity", self.plane_opacity),
            ("reference_opacity", self.reference_opacity),
        ):
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within [0, 1].")
