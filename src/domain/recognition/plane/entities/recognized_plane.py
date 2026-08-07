"""Immutable result of engineering plane recognition."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.recognition.plane.entities.plane import Plane
from domain.recognition.plane.value_objects.plane_provenance import (
    PlaneProvenance,
)


class PlaneEngineeringQuality(str, Enum):
    """Classify compliance with configured engineering thresholds."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"


@dataclass(frozen=True, slots=True)
class RecognizedPlane:
    """Store a plane recognition decision and its supporting warnings."""

    plane: Plane
    provenance: PlaneProvenance
    recognition_confidence: float
    engineering_quality: PlaneEngineeringQuality
    accepted: bool
    warnings: tuple[str, ...]
