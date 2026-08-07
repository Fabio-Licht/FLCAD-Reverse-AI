"""Mesh entity for the FLCAD engineering domain."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.entity.engineering_entity import EngineeringEntity
from core.entity.entity_type import EntityType
from domain.mesh.bounding_box import BoundingBox
from domain.mesh.mesh_data import MeshData
from domain.mesh.mesh_statistics import MeshStatistics


@dataclass(slots=True, repr=False)
class MeshEntity(EngineeringEntity):
    """Represent a mesh as an FLCAD engineering entity."""

    entity_type: EntityType = field(
        default=EntityType.MESH,
        init=False,
    )
    mesh_data: MeshData | None = None
    statistics: MeshStatistics | None = None
    bounding_box: BoundingBox | None = None
