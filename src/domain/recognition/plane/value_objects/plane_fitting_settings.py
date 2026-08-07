"""Configuration for mathematical plane fitting."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class PlaneFittingSettings:
    """Define an explicit plane-fitting method and numerical controls."""

    fitting_method: str
    tolerance: float
    outlier_rejection: bool
    maximum_iterations: int

    def __post_init__(self) -> None:
        """Validate plane-fitting configuration values."""

        if not self.fitting_method.strip():
            raise ValueError("Plane fitting method must not be empty.")

        if not isfinite(self.tolerance) or self.tolerance <= 0.0:
            raise ValueError(
                "Plane fitting tolerance must be finite and greater than zero."
            )

        if self.maximum_iterations < 1:
            raise ValueError(
                "Plane fitting maximum iterations must be greater than zero."
            )
