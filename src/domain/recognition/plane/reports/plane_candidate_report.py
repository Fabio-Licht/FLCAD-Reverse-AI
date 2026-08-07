"""Immutable report returned by plane-candidate detection."""

from __future__ import annotations

from dataclasses import dataclass

from domain.recognition.plane.entities.plane_candidate import PlaneCandidate


@dataclass(frozen=True, slots=True)
class PlaneCandidateReport:
    """Store a generated candidate, execution time, and warnings."""

    candidate: PlaneCandidate
    execution_time: float
    warnings: tuple[str, ...]
