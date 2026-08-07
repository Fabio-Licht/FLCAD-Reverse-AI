"""Configuration for plane-candidate generation."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class PlaneCandidateSettings:
    """Define explicit evidence thresholds for plane candidates."""

    minimum_planarity: float
    minimum_area: float
    minimum_triangle_count: int
    minimum_confidence: float

    def __post_init__(self) -> None:
        """Validate all candidate-generation thresholds."""

        if (
            not isfinite(self.minimum_planarity)
            or not 0.0 <= self.minimum_planarity <= 1.0
        ):
            raise ValueError("Minimum planarity must be between zero and one.")

        if not isfinite(self.minimum_area) or self.minimum_area <= 0.0:
            raise ValueError("Minimum area must be finite and greater than zero.")

        if self.minimum_triangle_count < 1:
            raise ValueError(
                "Minimum triangle count must be greater than zero."
            )

        if (
            not isfinite(self.minimum_confidence)
            or not 0.0 <= self.minimum_confidence <= 1.0
        ):
            raise ValueError("Minimum confidence must be between zero and one.")
