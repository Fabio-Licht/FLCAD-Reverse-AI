"""Engineering reference plane with complete recognition traceability."""

from __future__ import annotations

from dataclasses import dataclass

from core.entity.entity_type import EntityType
from domain.mesh.bounding_box import BoundingBox, Point3D
from domain.recognition.plane.entities.plane import Plane
from domain.recognition.plane.entities.recognized_plane import RecognizedPlane
from domain.reference.entities.reference_entity import ReferenceEntity


@dataclass(slots=True, repr=False, kw_only=True)
class ReferencePlane(ReferenceEntity):
    """Represent an engineering reference backed by a recognized plane."""

    recognized_plane: RecognizedPlane

    @property
    def plane(self) -> Plane:
        """Return the immutable mathematical plane."""

        return self.recognized_plane.plane

    @property
    def origin(self) -> Point3D:
        """Return the mathematical plane origin."""

        return self.plane.origin

    @property
    def normal(self) -> Point3D:
        """Return the mathematical plane normal."""

        return self.plane.normal

    @property
    def support_area(self) -> float:
        """Return the plane's supporting region area."""

        return self.plane.support_area

    @property
    def bounding_box(self) -> BoundingBox:
        """Return the plane's source bounds."""

        return self.plane.bounding_box

    @property
    def reference_type(self) -> EntityType:
        """Return the plane reference domain type."""

        return EntityType.PLANE
