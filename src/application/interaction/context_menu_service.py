"""Engineering context menus for registered reference objects."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QInputDialog, QMenu

from application.visualization.recognition.recognition_visualization_service import (
    RecognitionVisualizationService,
)
from domain.reference.entities.reference_plane import ReferencePlane
from domain.reference.managers.reference_manager import ReferenceManager


class ContextMenuService:
    """Create and execute initial ReferencePlane interaction actions."""

    def __init__(
        self,
        manager: ReferenceManager,
        visualization: RecognitionVisualizationService,
    ) -> None:
        self._manager = manager
        self._visualization = visualization

    def create(self, entity: object, parent: Any = None) -> QMenu | None:
        """Create a context menu for a supported engineering object."""

        if not isinstance(entity, ReferencePlane):
            return None

        menu = QMenu(parent)
        self._add_action(menu, "Rename", lambda: self._rename(entity, parent))
        self._add_action(menu, "Hide", lambda: self.hide(entity), entity.visible)
        self._add_action(menu, "Show", lambda: self.show(entity), not entity.visible)
        self._add_action(menu, "Lock", lambda: self.lock(entity), not entity.locked)
        self._add_action(menu, "Unlock", lambda: self.unlock(entity), entity.locked)
        menu.addSeparator()
        self._add_action(menu, "Delete", lambda: self.delete(entity))
        return menu

    def rename(self, reference: ReferencePlane, name: str) -> None:
        """Rename a reference and refresh its visual representation."""

        resolved_name = name.strip()

        if not resolved_name:
            raise ValueError("Reference name must not be empty.")

        existing = self._manager.find_by_name(resolved_name)

        if existing is not None and existing is not reference:
            raise ValueError(f"Reference name already exists: {resolved_name}")

        reference.name = resolved_name
        reference.display_name = resolved_name
        self._visualization.visualize_reference(reference)

    def hide(self, reference: ReferencePlane) -> None:
        """Hide a reference and synchronize the viewport."""

        reference.visible = False
        self._visualization.visualize_reference(reference)

    def show(self, reference: ReferencePlane) -> None:
        """Show a reference and synchronize the viewport."""

        reference.visible = True
        self._visualization.visualize_reference(reference)

    def lock(self, reference: ReferencePlane) -> None:
        """Lock a reference and synchronize its appearance."""

        reference.locked = True
        self._visualization.visualize_reference(reference)

    def unlock(self, reference: ReferencePlane) -> None:
        """Unlock a reference and synchronize its appearance."""

        reference.locked = False
        self._visualization.visualize_reference(reference)

    def delete(self, reference: ReferencePlane) -> None:
        """Remove a reference from its manager and viewport."""

        self._manager.remove(reference.id)
        self._visualization.remove(
            f"recognition:reference-plane:{reference.id}"
        )

    def _rename(self, reference: ReferencePlane, parent: Any) -> None:
        """Request a new name through the Qt application shell."""

        name, accepted = QInputDialog.getText(
            parent,
            "Rename Reference Plane",
            "Name:",
            text=reference.name,
        )

        if accepted:
            self.rename(reference, name)

    @staticmethod
    def _add_action(
        menu: QMenu,
        label: str,
        callback: Any,
        enabled: bool = True,
    ) -> None:
        """Add a configured action to a Qt context menu."""

        action = QAction(label, menu)
        action.setEnabled(enabled)
        action.triggered.connect(callback)
        menu.addAction(action)
