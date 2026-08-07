"""Selection synchronization for application-layer engineering objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from application.interaction.interaction_settings import InteractionSettings


@dataclass(frozen=True, slots=True)
class SelectionTarget:
    """Associate one scene object with domain and inspection context."""

    object_id: str
    entity: object
    context: dict[str, object]


class SelectionService:
    """Manage registered engineering selections without domain mutation."""

    def __init__(self, scene: Any, settings: InteractionSettings) -> None:
        self._scene = scene
        self._settings = settings
        self._targets: dict[str, SelectionTarget] = {}
        self._selected_ids: set[str] = set()

    def register(
        self,
        object_id: str,
        entity: object,
        **context: object,
    ) -> None:
        """Register or refresh a scene-to-domain association."""

        self._targets[object_id] = SelectionTarget(
            object_id=object_id,
            entity=entity,
            context=dict(context),
        )

    def unregister(self, object_id: str) -> None:
        """Remove one scene-to-domain association."""

        self._targets.pop(object_id, None)
        self._selected_ids.discard(object_id)

    def handles(self, object_id: str) -> bool:
        """Return whether an object belongs to the engineering layer."""

        return object_id in self._targets

    def target(self, object_id: str) -> SelectionTarget | None:
        """Return the registered selection target for a scene identity."""

        return self._targets.get(object_id)

    def select(
        self,
        object_id: str,
        *,
        additive: bool = False,
    ) -> tuple[SelectionTarget, ...]:
        """Select a registered target and synchronize its scene appearance."""

        if object_id not in self._targets:
            return self.selected()

        use_additive = additive and self._settings.enable_multi_selection

        if not use_additive:
            self._selected_ids = {object_id}
        elif object_id in self._selected_ids:
            self._selected_ids.remove(object_id)
        else:
            self._selected_ids.add(object_id)

        self._synchronize_scene()
        return self.selected()

    def synchronize(
        self,
        selected_ids: set[str],
    ) -> tuple[SelectionTarget, ...]:
        """Synchronize from an external viewport or project selection."""

        registered_ids = selected_ids.intersection(self._targets)

        if not self._settings.enable_multi_selection and registered_ids:
            registered_ids = {sorted(registered_ids)[-1]}

        self._selected_ids = registered_ids
        self._synchronize_scene()
        return self.selected()

    def clear(self) -> None:
        """Clear all registered engineering selections."""

        self._selected_ids.clear()
        self._synchronize_scene()

    def selected(self) -> tuple[SelectionTarget, ...]:
        """Return selected targets in deterministic scene-ID order."""

        return tuple(
            self._targets[object_id]
            for object_id in sorted(self._selected_ids)
        )

    def _synchronize_scene(self) -> None:
        """Apply selection state through the existing SceneManager."""

        for object_id in self._targets:
            if self._scene.get_object(object_id) is None:
                continue

            self._scene.set_selected(
                object_id,
                object_id in self._selected_ids,
                render=False,
            )

        viewer = getattr(self._scene, "viewer", None)

        if viewer is not None:
            viewer.render()
