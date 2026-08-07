"""Configuration for engineering reference-plane creation."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from domain.reference.entities.reference_entity import ReferenceColor


@dataclass(frozen=True, slots=True)
class ReferencePlaneSettings:
    """Define default presentation state for a reference plane."""

    default_name_prefix: str
    default_color: ReferenceColor
    default_layer: str
    default_visibility: bool
    default_opacity: float

    def __post_init__(self) -> None:
        """Validate reference-plane defaults."""

        if not self.default_name_prefix.strip():
            raise ValueError("Reference name prefix must not be empty.")

        if len(self.default_color) != 3 or not all(
            isfinite(component) and 0.0 <= component <= 1.0
            for component in self.default_color
        ):
            raise ValueError("Reference color components must be within [0, 1].")

        if not self.default_layer.strip():
            raise ValueError("Reference layer must not be empty.")

        if (
            not isfinite(self.default_opacity)
            or not 0.0 <= self.default_opacity <= 1.0
        ):
            raise ValueError("Reference opacity must be within [0, 1].")
