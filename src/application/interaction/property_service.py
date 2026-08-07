"""Read-only property conversion for engineering interaction."""

from __future__ import annotations

from typing import TypeAlias

from domain.mesh.mesh_entity import MeshEntity
from domain.recognition.plane.entities.plane import Plane
from domain.recognition.plane.entities.recognized_plane import RecognizedPlane
from domain.recognition.region.entities.region import Region
from domain.recognition.region.value_objects.region_analysis import (
    RegionAnalysis,
)
from domain.recognition.region.value_objects.region_features import (
    RegionFeatures,
)
from domain.reference.entities.reference_plane import ReferencePlane


PropertyCollection: TypeAlias = tuple[tuple[str, object], ...]


class PropertyService:
    """Convert supported domain objects into immutable property collections."""

    def properties(
        self,
        entity: object,
        context: dict[str, object] | None = None,
    ) -> PropertyCollection:
        """Return read-only properties for a supported engineering object."""

        resolved_context = context or {}

        if isinstance(entity, Region):
            return self._region(entity, resolved_context)

        if isinstance(entity, RecognizedPlane):
            return self._recognized_plane(entity)

        if isinstance(entity, ReferencePlane):
            return self._reference_plane(entity)

        if isinstance(entity, Plane):
            return (
                ("Plane ID", str(entity.id)),
                ("Origin", entity.origin),
                ("Normal", entity.normal),
                ("Support Area", entity.support_area),
                ("Bounding Box", entity.bounding_box),
            )

        if isinstance(entity, MeshEntity):
            return (
                ("Mesh ID", str(entity.uuid)),
                ("Name", entity.display_name),
                ("Entity State", entity.state.value),
            )

        raise TypeError(f"Unsupported property entity: {type(entity).__name__}")

    @staticmethod
    def _region(
        region: Region,
        context: dict[str, object],
    ) -> PropertyCollection:
        """Return Region properties with supplied analysis evidence."""

        analysis = context.get("analysis")
        features = context.get("features")

        triangle_count = (
            analysis.triangle_count
            if isinstance(analysis, RegionAnalysis)
            else len(region.triangle_indices)
        )
        planarity = (
            features.planarity_score
            if isinstance(features, RegionFeatures)
            else "Unavailable"
        )
        normal_variance: float | str = (
            analysis.normal_variance
            if isinstance(analysis, RegionAnalysis)
            else "Unavailable"
        )

        return (
            ("Region ID", str(region.id)),
            ("Area", region.area),
            ("Triangle Count", triangle_count),
            ("Planarity", planarity),
            ("Normal Variance", normal_variance),
            ("Bounding Box", region.bounding_box),
        )

    @staticmethod
    def _recognized_plane(
        recognized_plane: RecognizedPlane,
    ) -> PropertyCollection:
        """Return recognized-plane geometry and quality evidence."""

        plane = recognized_plane.plane
        statistics = recognized_plane.provenance.statistics
        return (
            ("Origin", plane.origin),
            ("Normal", plane.normal),
            ("RMS Error", statistics.rms_error),
            ("Average Error", statistics.average_error),
            ("Maximum Error", statistics.maximum_error),
            ("Confidence", recognized_plane.recognition_confidence),
            (
                "Engineering Quality",
                recognized_plane.engineering_quality.value,
            ),
        )

    @staticmethod
    def _reference_plane(
        reference: ReferencePlane,
    ) -> PropertyCollection:
        """Return logical presentation state for a reference plane."""

        return (
            ("Name", reference.display_name),
            ("Visible", reference.visible),
            ("Locked", reference.locked),
            ("Layer", reference.layer),
            ("Color", reference.color),
            ("Opacity", reference.opacity),
        )
