"""Read-only viewport visualization of backend-neutral mesh entities."""

from __future__ import annotations

import numpy as np
import pyvista as pv

from application.visualization.recognition.engineering_color_palette import (
    EngineeringColorPalette,
)
from application.visualization.recognition.viewport_adapter import (
    RecognitionViewportAdapter,
)
from domain.mesh.mesh_entity import MeshEntity


class MeshVisualizer:
    """Render a MeshEntity without modifying its domain data."""

    def __init__(self, viewport: RecognitionViewportAdapter) -> None:
        self._viewport = viewport

    def visualize(self, mesh: MeshEntity) -> str:
        """Create or refresh the gray source-mesh visual."""

        if mesh.mesh_data is None:
            raise ValueError("Mesh visualization requires mesh data.")

        vertices = np.asarray(mesh.mesh_data.vertices, dtype=float)
        connectivity: list[list[int]] = []

        for face in mesh.mesh_data.faces:
            indices = tuple(int(value) for value in face)

            if len(indices) != 3:
                raise ValueError("Mesh visualization requires triangles.")

            connectivity.append([3, indices[0], indices[1], indices[2]])

        faces = np.asarray(connectivity, dtype=np.int64).reshape(-1)
        geometry = pv.PolyData(vertices, faces)
        object_id = self.object_id(mesh)
        self._viewport.add(
            object_id,
            mesh.display_name,
            geometry,
            "mesh",
            color=EngineeringColorPalette.MESH,
            opacity=1.0,
            pickable=True,
        )
        return object_id

    @staticmethod
    def object_id(mesh: MeshEntity) -> str:
        """Return the stable scene identity for a source mesh."""

        return f"recognition:mesh:{mesh.uuid}"
