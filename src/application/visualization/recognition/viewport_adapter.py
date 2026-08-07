"""Adapter between recognition visualizers and the existing scene."""

from __future__ import annotations

from typing import Any


class RecognitionViewportAdapter:
    """Expose the viewport operations required by recognition visuals."""

    def __init__(self, scene: Any) -> None:
        self._scene = scene

    def add(
        self,
        object_id: str,
        name: str,
        geometry: Any,
        object_type: str,
        **render_options: Any,
    ) -> None:
        """Add or replace a scene object."""

        self._scene.add_mesh(
            object_id=object_id,
            name=name,
            mesh=geometry,
            object_type=object_type,
            **render_options,
        )

    def remove(self, object_id: str) -> bool:
        """Remove a scene object when it exists."""

        return self._scene.remove_object(object_id)

    def contains(self, object_id: str) -> bool:
        """Return whether a scene object is currently registered."""

        return self._scene.get_object(object_id) is not None

    def set_visibility(self, object_id: str, visible: bool) -> bool:
        """Synchronize logical visibility with the scene actor."""

        return self._scene.set_visibility(object_id, visible)

    def set_selected(self, object_id: str, selected: bool) -> bool:
        """Synchronize selection with the scene actor."""

        return self._scene.set_selected(object_id, selected)
