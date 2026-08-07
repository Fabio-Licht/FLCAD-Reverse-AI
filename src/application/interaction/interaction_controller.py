"""Controller coordinating engineering viewport interaction."""

from __future__ import annotations

from typing import Any

from application.interaction.context_menu_service import ContextMenuService
from application.interaction.inspection_service import (
    InspectionService,
    InspectionSnapshot,
)
from application.interaction.interaction_settings import InteractionSettings
from application.interaction.selection_service import SelectionService


class InteractionController:
    """Dispatch viewport selection, inspection, and context-menu commands."""

    def __init__(
        self,
        selection: SelectionService,
        inspection: InspectionService,
        context_menus: ContextMenuService,
        settings: InteractionSettings,
    ) -> None:
        self._selection = selection
        self._inspection = inspection
        self._context_menus = context_menus
        self._settings = settings

    def register(
        self,
        object_id: str,
        entity: object,
        **context: object,
    ) -> None:
        """Register a visual engineering object for interaction."""

        self._selection.register(object_id, entity, **context)

    def unregister(self, object_id: str) -> None:
        """Remove an engineering object from interaction."""

        self._selection.unregister(object_id)

    def handles(self, object_id: str) -> bool:
        """Return whether an object belongs to this interaction layer."""

        return self._selection.handles(object_id)

    def on_viewport_selection(
        self,
        object_id: str,
        *,
        additive: bool = False,
    ) -> InspectionSnapshot | None:
        """Receive a viewport selection and synchronize inspection."""

        selected = self._selection.select(
            object_id,
            additive=additive,
        )
        return self._inspect_selected(selected)

    def synchronize_selection(
        self,
        selected_ids: set[str],
    ) -> InspectionSnapshot | None:
        """Synchronize external selection and current inspection."""

        selected = self._selection.synchronize(selected_ids)
        return self._inspect_selected(selected)

    def clear_selection(self) -> None:
        """Clear selection and inspection state."""

        self._selection.clear()
        self._inspection.clear()

    def context_menu(self, object_id: str, parent: Any = None) -> Any:
        """Create the context menu for a registered object when enabled."""

        if not self._settings.enable_context_menu:
            return None

        target = self._selection.target(object_id)

        if target is None:
            return None

        return self._context_menus.create(target.entity, parent)

    def _inspect_selected(
        self,
        selected: tuple[Any, ...],
    ) -> InspectionSnapshot | None:
        """Inspect the active selected target when inspection is enabled."""

        if not self._settings.enable_inspector or not selected:
            self._inspection.clear()
            return None

        return self._inspection.inspect(selected[-1])
