"""Application service coordinating recognition viewport visuals."""

from __future__ import annotations

from typing import Any

from application.visualization.recognition.mesh_visualizer import (
    MeshVisualizer,
)
from application.visualization.recognition.plane_visualizer import (
    PlaneVisualizer,
)
from application.visualization.recognition.reference_visualizer import (
    ReferenceVisualizer,
)
from application.visualization.recognition.region_visualizer import (
    RegionVisualizer,
)
from application.visualization.recognition.viewport_adapter import (
    RecognitionViewportAdapter,
)
from application.visualization.recognition.visualization_settings import (
    VisualizationSettings,
)
from domain.mesh.mesh_entity import MeshEntity
from domain.recognition.plane.entities.plane import Plane
from domain.recognition.plane.entities.recognized_plane import RecognizedPlane
from domain.recognition.region.entities.region import Region
from domain.reference.entities.reference_plane import ReferencePlane
from domain.reference.managers.reference_manager import ReferenceManager


class RecognitionVisualizationService:
    """Dispatch domain objects to read-only specialized visualizers."""

    def __init__(
        self,
        scene: Any,
        settings: VisualizationSettings | None = None,
    ) -> None:
        self.settings = settings or VisualizationSettings(
            region_opacity=0.72,
            plane_opacity=0.38,
            reference_opacity=0.62,
            show_normals=True,
            show_labels=False,
            show_region_ids=False,
        )
        self._viewport = RecognitionViewportAdapter(scene)
        self._meshes = MeshVisualizer(self._viewport)
        self._regions = RegionVisualizer(self._viewport, self.settings)
        self._planes = PlaneVisualizer(self._viewport, self.settings)
        self._references = ReferenceVisualizer(
            self._viewport,
            self.settings,
        )
        self._interaction: Any = None
        self._reference_interaction_ids: set[str] = set()

    def attach_interaction_controller(self, controller: Any) -> None:
        """Attach the application interaction registry after composition."""

        self._interaction = controller

    def visualize_mesh(self, mesh: MeshEntity) -> str:
        """Create or refresh the gray source-mesh visual."""

        object_id = self._meshes.visualize(mesh)
        self._register((object_id,), mesh)
        return object_id

    def visualize_region(
        self,
        mesh: MeshEntity,
        region: Region,
        *,
        visible: bool = True,
        selected: bool = False,
        analysis: object | None = None,
        features: object | None = None,
    ) -> str:
        """Dispatch a Region to the region visualizer."""

        object_id = self._regions.visualize(
            mesh,
            region,
            visible=visible,
            selected=selected,
        )
        self._register(
            (object_id,),
            region,
            analysis=analysis,
            features=features,
        )
        return object_id

    def visualize_plane(
        self,
        plane: Plane,
        *,
        recognized: bool = False,
        visible: bool = True,
        selected: bool = False,
        show_border: bool = False,
    ) -> tuple[str, ...]:
        """Dispatch a mathematical Plane to the plane visualizer."""

        object_ids = self._planes.visualize(
            plane,
            recognized=recognized,
            visible=visible,
            selected=selected,
            show_border=show_border,
        )
        self._register(object_ids, plane)
        return object_ids

    def visualize_recognized_plane(
        self,
        recognized_plane: RecognizedPlane,
        *,
        show_border: bool = True,
    ) -> tuple[str, ...]:
        """Render an accepted or rejected recognized-plane result."""

        object_ids = self._planes.visualize(
            recognized_plane.plane,
            recognized=recognized_plane.accepted,
            show_border=show_border,
        )
        self._register(object_ids, recognized_plane)
        return object_ids

    def visualize_reference(self, reference: ReferencePlane) -> str:
        """Dispatch a ReferencePlane to the reference visualizer."""

        object_id = self._references.visualize(reference)
        self._register((object_id,), reference)
        self._reference_interaction_ids.add(object_id)
        return object_id

    def synchronize_references(
        self,
        manager: ReferenceManager,
    ) -> tuple[str, ...]:
        """Synchronize all managed reference planes with the viewport."""

        active_ids = set(self._references.synchronize(manager))

        for stale_id in self._reference_interaction_ids - active_ids:
            self._unregister(stale_id)

        for reference in manager.all():
            if isinstance(reference, ReferencePlane):
                self._register(
                    (
                        f"recognition:reference-plane:{reference.id}",
                    ),
                    reference,
                )

        self._reference_interaction_ids = active_ids
        return tuple(sorted(active_ids))

    def set_visibility(self, object_id: str, visible: bool) -> bool:
        """Update visibility for a visualization object."""

        return self._viewport.set_visibility(object_id, visible)

    def set_selected(self, object_id: str, selected: bool) -> bool:
        """Update selection for a visualization object."""

        return self._viewport.set_selected(object_id, selected)

    def remove(self, object_id: str) -> bool:
        """Remove a visualization object from the viewport."""

        removed = self._viewport.remove(object_id)
        self._unregister(object_id)
        self._reference_interaction_ids.discard(object_id)
        return removed

    def refresh(
        self,
        entity: object,
        *,
        mesh: MeshEntity | None = None,
        analysis: object | None = None,
        features: object | None = None,
    ) -> Any:
        """Refresh a supported entity through its specialized visualizer."""

        if isinstance(entity, Region):
            if mesh is None:
                raise ValueError("Refreshing a Region requires its MeshEntity.")
            return self.visualize_region(
                mesh,
                entity,
                analysis=analysis,
                features=features,
            )

        if isinstance(entity, RecognizedPlane):
            return self.visualize_recognized_plane(entity)

        if isinstance(entity, Plane):
            return self.visualize_plane(entity)

        if isinstance(entity, ReferencePlane):
            return self.visualize_reference(entity)

        if isinstance(entity, MeshEntity):
            return self.visualize_mesh(entity)

        raise TypeError(f"Unsupported visualization entity: {type(entity).__name__}")

    def _register(
        self,
        object_ids: tuple[str, ...],
        entity: object,
        **context: object,
    ) -> None:
        """Register visualization identities with the interaction layer."""

        if self._interaction is None:
            return

        for object_id in object_ids:
            self._interaction.register(object_id, entity, **context)

    def _unregister(self, object_id: str) -> None:
        """Unregister a visualization identity from interaction."""

        if self._interaction is not None:
            self._interaction.unregister(object_id)
