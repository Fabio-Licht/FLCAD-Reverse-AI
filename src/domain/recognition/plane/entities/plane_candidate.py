"""Immutable candidate for a possible engineering plane."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.mesh.bounding_box import BoundingBox, Point3D
from domain.recognition.region.entities.region import Region


@dataclass(frozen=True, slots=True)
class PlaneCandidate:
    """Represent plane-like evidence without creating plane geometry."""

    region: Region
    confidence: float
    evidence: tuple[str, ...]
    average_normal: Point3D
    bounding_box: BoundingBox
    area: float
    triangle_count: int

    @property
    def region_id(self) -> UUID:
        """Return the identity of the source region."""

        return self.region.id
