"""Immutable report returned by engineering plane recognition."""

from __future__ import annotations

from dataclasses import dataclass

from domain.recognition.plane.entities.recognized_plane import RecognizedPlane


@dataclass(frozen=True, slots=True)
class PlaneRecognitionReport:
    """Store a recognized plane, execution time, and warnings."""

    recognized_plane: RecognizedPlane
    execution_time: float
    warnings: tuple[str, ...]
