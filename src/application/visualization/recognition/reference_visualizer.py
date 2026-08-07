"""Read-only viewport visualization of engineering references."""

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
from domain.reference.entities.reference_plane import ReferencePlane
from domain.reference.managers.reference_manager import ReferenceManager


class ReferenceVisualizer:
    """Synchronize ReferencePlane state with viewport-only geometry."""

    def __init__(
        self,
        viewport: RecognitionViewportAdapter,
        settings: VisualizationSettings,
    ) -> None:
        self._viewport = viewport
        self._settings = settings
        self._managed_ids: set[str] = set()

    def visualize(self, reference: ReferencePlane) -> str:
        """Create or refresh one reference-plane visual."""

        object_id = self.object_id(reference)
        side_length = sqrt(reference.support_area)
        color = (
            EngineeringColorPalette.LOCKED
            if reference.locked
            else reference.color
        )
        geometry = pv.Plane(
            center=reference.origin,
            direction=reference.normal,
            i_size=side_length,
            j_size=side_length,
        )
        self._viewport.add(
            object_id,
            reference.display_name,
            geometry,
            "reference_plane",
            color=color,
            opacity=min(reference.opacity, self._settings.reference_opacity),
            show_edges=True,
            edge_color=EngineeringColorPalette.REFERENCE_PLANE,
            line_width=3.0 if reference.locked else 2.0,
            pickable=not reference.locked,
        )
        self._viewport.set_visibility(object_id, reference.visible)
        self._viewport.set_selected(object_id, reference.selected)
        self._managed_ids.add(object_id)
        return object_id

    def synchronize(self, manager: ReferenceManager) -> tuple[str, ...]:
        """Refresh all plane references and remove stale viewport objects."""

        active_ids: set[str] = set()

        for reference in manager.all():
            if not isinstance(reference, ReferencePlane):
                continue

            active_ids.add(self.visualize(reference))

        for stale_id in self._managed_ids - active_ids:
            if self._viewport.contains(stale_id):
                self._viewport.remove(stale_id)

        self._managed_ids = active_ids
        return tuple(sorted(active_ids))

    @staticmethod
    def object_id(reference: ReferencePlane) -> str:
        """Return the stable scene identity for a reference plane."""

        return f"recognition:reference-plane:{reference.id}"
