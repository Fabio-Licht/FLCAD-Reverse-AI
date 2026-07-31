from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


TOP_LEVEL_GROUPS = {
    "mesh": "Malhas",
    "references": "Geometria de referência",
    "sketch": "Esboços",
    "curve": "Curvas",
    "surface": "Superfícies",
    "solid": "Sólidos",
    "analysis": "Análises",
}

REFERENCE_GROUPS = {
    "reference_point": "Pontos",
    "reference_axis": "Eixos e vetores",
    "reference_plane": "Planos",
    "reference_cylinder": "Cilindros",
}


class ProjectPanel(QWidget):
    """Árvore organizada das entidades do projeto."""

    visibility_changed = Signal(str, bool)
    object_selection_toggled = Signal(str)

    VISIBLE_SYMBOL = "●"
    HIDDEN_SYMBOL = "○"

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.selection_mode_active = False

        self._group_items: dict[
            str,
            QTreeWidgetItem,
        ] = {}

        self._reference_group_items: dict[
            str,
            QTreeWidgetItem,
        ] = {}

        self._object_items: dict[
            str,
            QTreeWidgetItem,
        ] = {}

        self._object_visibility: dict[
            str,
            bool,
        ] = {}

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.setColumnWidth(0, 42)
        self.tree.setIndentation(18)

        self.tree.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )

        self.tree.itemClicked.connect(
            self._on_item_clicked
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tree)

        self._create_groups()

    def _create_groups(self) -> None:
        """Cria grupos principais e subgrupos de referência."""

        self.tree.blockSignals(True)
        self.tree.clear()

        self._group_items.clear()
        self._reference_group_items.clear()
        self._object_items.clear()
        self._object_visibility.clear()

        for group_key, group_name in (
            TOP_LEVEL_GROUPS.items()
        ):
            group_item = QTreeWidgetItem(
                ["", group_name]
            )

            group_item.setFlags(
                group_item.flags()
                & ~Qt.ItemFlag.ItemIsSelectable
            )

            group_font = QFont()
            group_font.setBold(True)
            group_item.setFont(1, group_font)

            self.tree.addTopLevelItem(group_item)
            self._group_items[group_key] = group_item

            group_item.setExpanded(
                group_key in {"mesh", "references"}
            )

        references_root = self._group_items[
            "references"
        ]

        for object_type, group_name in (
            REFERENCE_GROUPS.items()
        ):
            subgroup = QTreeWidgetItem(
                ["", group_name]
            )

            subgroup.setFlags(
                subgroup.flags()
                & ~Qt.ItemFlag.ItemIsSelectable
            )

            subgroup_font = QFont()
            subgroup_font.setItalic(True)
            subgroup.setFont(1, subgroup_font)

            references_root.addChild(subgroup)

            self._reference_group_items[
                object_type
            ] = subgroup

            subgroup.setExpanded(True)

        self.tree.blockSignals(False)

    def set_selection_mode_active(
        self,
        active: bool,
    ) -> None:
        """Ativa ou desativa seleção de objetos."""

        self.selection_mode_active = active

        if not active:
            self.clear_selection()

    def add_mesh(
        self,
        file_path: str,
        mesh: Any,
        object_id: str,
    ) -> None:
        """Compatibilidade com versões anteriores."""

        from pathlib import Path

        self.add_object(
            object_id=object_id,
            name=Path(file_path).name,
            object_type="mesh",
            data=mesh,
            visible=True,
        )

    def add_object(
        self,
        object_id: str,
        name: str,
        object_type: str,
        data: Any,
        visible: bool = True,
    ) -> None:
        """Adiciona uma entidade no grupo adequado."""

        if object_id in self._object_items:
            self.remove_object(object_id)

        parent_item = self._parent_for_type(
            object_type
        )

        symbol = (
            self.VISIBLE_SYMBOL
            if visible
            else self.HIDDEN_SYMBOL
        )

        object_item = QTreeWidgetItem(
            [symbol, name]
        )

        object_item.setData(
            1,
            Qt.ItemDataRole.UserRole,
            object_id,
        )

        object_item.setData(
            1,
            Qt.ItemDataRole.UserRole + 1,
            "object",
        )

        object_item.setData(
            1,
            Qt.ItemDataRole.UserRole + 2,
            object_type,
        )

        object_item.setTextAlignment(
            0,
            Qt.AlignmentFlag.AlignCenter,
        )

        visibility_font = QFont()
        visibility_font.setBold(True)
        visibility_font.setPointSize(13)
        object_item.setFont(0, visibility_font)

        self._object_items[object_id] = object_item
        self._object_visibility[object_id] = visible

        self._update_visibility_appearance(
            object_item,
            visible,
        )

        if object_type == "mesh":
            self._add_mesh_information(
                object_item,
                data,
            )
        else:
            self._add_reference_information(
                object_item,
                object_type,
                data,
            )

        parent_item.addChild(object_item)
        parent_item.setExpanded(True)

        if object_type.startswith("reference_"):
            self._group_items[
                "references"
            ].setExpanded(True)

        object_item.setExpanded(False)
        object_item.setSelected(False)

    def _parent_for_type(
        self,
        object_type: str,
    ) -> QTreeWidgetItem:
        """Resolve o grupo da entidade."""

        if object_type in self._reference_group_items:
            return self._reference_group_items[
                object_type
            ]

        group_key = {
            "mesh": "mesh",
            "sketch": "sketch",
            "curve": "curve",
            "surface": "surface",
            "solid": "solid",
            "analysis": "analysis",
        }.get(object_type)

        if group_key is None:
            raise ValueError(
                f"Tipo sem grupo na árvore: {object_type}"
            )

        return self._group_items[group_key]

    def _add_mesh_information(
        self,
        object_item: QTreeWidgetItem,
        mesh: Any,
    ) -> None:
        """Adiciona dados técnicos da malha."""

        information_item = (
            self._create_information_item(
                "Informações da malha"
            )
        )

        points_text = (
            f"Pontos: {mesh.n_points:,}".replace(
                ",",
                ".",
            )
        )

        triangles_text = (
            f"Triângulos: {mesh.n_cells:,}".replace(
                ",",
                ".",
            )
        )

        information_item.addChild(
            self._create_information_item(
                points_text
            )
        )

        information_item.addChild(
            self._create_information_item(
                triangles_text
            )
        )

        bounds = mesh.bounds

        dimensions_item = (
            self._create_information_item(
                "Dimensões"
            )
        )

        dimensions_item.addChild(
            self._create_information_item(
                f"X: {bounds[1] - bounds[0]:.2f} mm"
            )
        )

        dimensions_item.addChild(
            self._create_information_item(
                f"Y: {bounds[3] - bounds[2]:.2f} mm"
            )
        )

        dimensions_item.addChild(
            self._create_information_item(
                f"Z: {bounds[5] - bounds[4]:.2f} mm"
            )
        )

        information_item.addChild(
            dimensions_item
        )

        object_item.addChild(
            information_item
        )

    def _add_reference_information(
        self,
        object_item: QTreeWidgetItem,
        object_type: str,
        data: Any,
    ) -> None:
        """Adiciona informações resumidas da referência."""

        information_item = (
            self._create_information_item(
                "Propriedades"
            )
        )

        if object_type == "reference_point":
            x, y, z = data.position

            information_item.addChild(
                self._create_information_item(
                    f"X: {x:.4f} mm"
                )
            )
            information_item.addChild(
                self._create_information_item(
                    f"Y: {y:.4f} mm"
                )
            )
            information_item.addChild(
                self._create_information_item(
                    f"Z: {z:.4f} mm"
                )
            )

        elif object_type == "reference_axis":
            dx, dy, dz = data.direction

            information_item.addChild(
                self._create_information_item(
                    f"Direção: ({dx:.4f}, {dy:.4f}, {dz:.4f})"
                )
            )
            information_item.addChild(
                self._create_information_item(
                    f"Comprimento visual: {data.display_length:.2f} mm"
                )
            )

        elif object_type == "reference_plane":
            nx, ny, nz = data.normal

            information_item.addChild(
                self._create_information_item(
                    f"Normal: ({nx:.4f}, {ny:.4f}, {nz:.4f})"
                )
            )
            information_item.addChild(
                self._create_information_item(
                    f"Tamanho: {data.size_x:.2f} × {data.size_y:.2f} mm"
                )
            )

        elif object_type == "reference_cylinder":
            information_item.addChild(
                self._create_information_item(
                    f"Diâmetro: {data.diameter:.4f} mm"
                )
            )
            information_item.addChild(
                self._create_information_item(
                    f"Comprimento: {data.length:.4f} mm"
                )
            )

        object_item.addChild(
            information_item
        )

    def _create_information_item(
        self,
        text: str,
    ) -> QTreeWidgetItem:
        """Cria uma linha informativa."""

        item = QTreeWidgetItem(["", text])

        item.setFlags(
            item.flags()
            & ~Qt.ItemFlag.ItemIsSelectable
        )

        return item

    def set_selected_objects(
        self,
        object_ids: set[str],
    ) -> None:
        """Sincroniza seleção visual."""

        self.tree.blockSignals(True)
        self.tree.clearSelection()

        for object_id, item in (
            self._object_items.items()
        ):
            item.setSelected(
                object_id in object_ids
            )

        self.tree.setCurrentItem(None)
        self.tree.blockSignals(False)

    def clear_selection(self) -> None:
        """Limpa a seleção visual."""

        self.tree.blockSignals(True)
        self.tree.clearSelection()
        self.tree.setCurrentItem(None)
        self.tree.blockSignals(False)

    def set_object_visibility(
        self,
        object_id: str,
        visible: bool,
    ) -> bool:
        """Atualiza indicador de visibilidade."""

        item = self._object_items.get(object_id)

        if item is None:
            return False

        self._object_visibility[object_id] = visible

        item.setText(
            0,
            (
                self.VISIBLE_SYMBOL
                if visible
                else self.HIDDEN_SYMBOL
            ),
        )

        self._update_visibility_appearance(
            item,
            visible,
        )

        return True

    def _update_visibility_appearance(
        self,
        item: QTreeWidgetItem,
        visible: bool,
    ) -> None:
        """Atualiza a cor do indicador."""

        item.setForeground(
            0,
            QBrush(
                QColor(
                    "#63d5ff"
                    if visible
                    else "#6f7782"
                )
            ),
        )

    def remove_object(
        self,
        object_id: str,
    ) -> None:
        """Remove um layer da árvore."""

        object_item = self._object_items.get(
            object_id
        )

        if object_item is None:
            return

        parent_item = object_item.parent()

        if parent_item is not None:
            index = parent_item.indexOfChild(
                object_item
            )

            if index >= 0:
                parent_item.takeChild(index)

        self._object_items.pop(
            object_id,
            None,
        )

        self._object_visibility.pop(
            object_id,
            None,
        )

    def _on_item_clicked(
        self,
        item: QTreeWidgetItem,
        column: int,
    ) -> None:
        """Trata visibilidade e seleção."""

        item_role = item.data(
            1,
            Qt.ItemDataRole.UserRole + 1,
        )

        if item_role != "object":
            return

        object_id_data = item.data(
            1,
            Qt.ItemDataRole.UserRole,
        )

        if not object_id_data:
            return

        object_id = str(object_id_data)

        if column == 0:
            current_visibility = (
                self._object_visibility.get(
                    object_id,
                    True,
                )
            )

            self.visibility_changed.emit(
                object_id,
                not current_visibility,
            )
            return

        if (
            column == 1
            and self.selection_mode_active
        ):
            self.object_selection_toggled.emit(
                object_id
            )
