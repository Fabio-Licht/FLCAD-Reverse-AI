"""Read-only viewport visualization of segmented mesh regions."""

from __future__ import annotations

from typing import Any

import numpy as np
import pyvista as pv

from application.visualization.recognition.engineering_color_palette import (
    EngineeringColorPalette,
)
from application.visualization.recognition.viewport_adapter import (
    RecognitionViewportAdapter,
)
from application.visualization.recognition.visualization_settings import (
    VisualizationSettings,
)
from domain.mesh.mesh_entity import MeshEntity
from domain.recognition.region.entities.region import Region


class RegionVisualizer:
    """Render immutable Region objects using source-mesh triangles."""

    def __init__(
        self,
        viewport: RecognitionViewportAdapter,
        settings: VisualizationSettings,
    ) -> None:
        self._viewport = viewport
        self._settings = settings

    def visualize(
        self,
        mesh: MeshEntity,
        region: Region,
        *,
        visible: bool = True,
        selected: bool = False,
    ) -> str:
        """Create or refresh a colored region scene object."""

        geometry = self._geometry(mesh, region)
        object_id = self.object_id(region)
        color = EngineeringColorPalette.region(region.id)
        self._viewport.add(
            object_id,
            f"Region {region.id}",
            geometry,
            "recognition_region",
            color=color,
            opacity=self._settings.region_opacity,
            show_edges=True,
            edge_color=color,
            pickable=True,
        )
        self._viewport.set_visibility(object_id, visible)
        self._viewport.set_selected(object_id, selected)
        return object_id

    @staticmethod
    def object_id(region: Region) -> str:
        """Return the stable scene identity for a region."""

        return f"recognition:region:{region.id}"

    @staticmethod
    def _geometry(mesh: MeshEntity, region: Region) -> Any:
        """Convert selected source triangles to viewport-only geometry."""

        if mesh.mesh_data is None:
            raise ValueError("Region visualization requires mesh data.")

        vertices = np.asarray(mesh.mesh_data.vertices, dtype=float)
        faces = mesh.mesh_data.faces
        selected_faces: list[list[int]] = []

        for triangle_index in region.triangle_indices:
            if triangle_index < 0 or triangle_index >= len(faces):
                raise IndexError(
                    "Region references a triangle outside the source mesh."
                )

            face = tuple(int(value) for value in faces[triangle_index])

            if len(face) != 3:
                raise ValueError("Region visualization requires triangles.")

            selected_faces.append([3, face[0], face[1], face[2]])

        connectivity = np.asarray(selected_faces, dtype=np.int64).reshape(-1)
        return pv.PolyData(vertices, connectivity)
