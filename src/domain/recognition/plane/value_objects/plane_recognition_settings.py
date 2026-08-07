"""Engineering thresholds for fitted-plane recognition."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class PlaneRecognitionSettings:
    """Define explicit quality and acceptance thresholds."""

    maximum_rms_error: float
    maximum_average_error: float
    minimum_support_area: float
    minimum_inlier_ratio: float
    minimum_confidence: float

    def __post_init__(self) -> None:
        """Validate all plane-recognition thresholds."""

        if (
            not isfinite(self.maximum_rms_error)
            or self.maximum_rms_error <= 0.0
        ):
            raise ValueError(
                "Maximum RMS error must be finite and greater than zero."
            )

        if (
            not isfinite(self.maximum_average_error)
            or self.maximum_average_error <= 0.0
        ):
            raise ValueError(
                "Maximum average error must be finite and greater than zero."
            )

        if (
            not isfinite(self.minimum_support_area)
            or self.minimum_support_area <= 0.0
        ):
            raise ValueError(
                "Minimum support area must be finite and greater than zero."
            )

        if not 0.0 <= self.minimum_inlier_ratio <= 1.0:
            raise ValueError(
                "Minimum inlier ratio must be between zero and one."
            )

        if not 0.0 <= self.minimum_confidence <= 1.0:
            raise ValueError(
                "Minimum confidence must be between zero and one."
            )
