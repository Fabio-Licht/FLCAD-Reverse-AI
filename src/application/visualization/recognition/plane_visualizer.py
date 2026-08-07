"""Read-only viewport visualization of mathematical planes."""

from __future__ import annotations

from math import sqrt

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
from domain.recognition.plane.entities.plane import Plane


class PlaneVisualizer:
    """Render mathematical planes without modifying domain geometry."""

    def __init__(
        self,
        viewport: RecognitionViewportAdapter,
        settings: VisualizationSettings,
    ) -> None:
        self._viewport = viewport
        self._settings = settings

    def visualize(
        self,
        plane: Plane,
        *,
        recognized: bool = False,
        visible: bool = True,
        selected: bool = False,
        show_border: bool = False,
    ) -> tuple[str, ...]:
        """Create or refresh plane, normal, and optional border visuals."""

        base_id = self.object_id(plane)
        normal_id = f"{base_id}:normal"
        border_id = f"{base_id}:border"
        side_length = sqrt(plane.support_area)
        color = (
            EngineeringColorPalette.RECOGNIZED_PLANE
            if recognized
            else EngineeringColorPalette.PLANE_CANDIDATE
        )
        geometry = pv.Plane(
            center=plane.origin,
            direction=plane.normal,
            i_size=side_length,
            j_size=side_length,
        )
        self._viewport.add(
            base_id,
            f"Plane {plane.id}",
            geometry,
            "recognized_plane" if recognized else "mathematical_plane",
            color=color,
            opacity=self._settings.plane_opacity,
            pickable=True,
        )
        self._viewport.set_visibility(base_id, visible)
        self._viewport.set_selected(base_id, selected)
        visual_ids = [base_id]

        if self._settings.show_normals:
            normal = pv.Arrow(
                start=plane.origin,
                direction=plane.normal,
                scale=side_length,
            )
            self._viewport.add(
                normal_id,
                f"Plane normal {plane.id}",
                normal,
                "plane_normal",
                color=color,
                pickable=False,
            )
            self._viewport.set_visibility(normal_id, visible)
            visual_ids.append(normal_id)
        elif self._viewport.contains(normal_id):
            self._viewport.remove(normal_id)

        if show_border:
            border = geometry.extract_feature_edges(
                boundary_edges=True,
                feature_edges=False,
                manifold_edges=False,
                non_manifold_edges=False,
            )
            self._viewport.add(
                border_id,
                f"Plane border {plane.id}",
                border,
                "plane_border",
                color=color,
                line_width=2.0,
                pickable=False,
            )
            self._viewport.set_visibility(border_id, visible)
            visual_ids.append(border_id)
        elif self._viewport.contains(border_id):
            self._viewport.remove(border_id)

        return tuple(visual_ids)

    @staticmethod
    def object_id(plane: Plane) -> str:
        """Return the stable scene identity for a mathematical plane."""

        return f"recognition:plane:{plane.id}"
