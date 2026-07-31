from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DeleteDialog(QDialog):
    """Janela de seleção e exclusão de objetos."""

    delete_requested = Signal()
    cancel_requested = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._completed = False

        self.setWindowTitle("Excluir objetos")
        self.resize(420, 330)
        self.setModal(False)

        self.setWindowFlag(
            Qt.WindowType.Tool,
            True,
        )

        self._create_interface()

    def _create_interface(self) -> None:
        """Cria os controles da janela."""

        title_label = QLabel(
            "Selecione os objetos que deseja excluir"
        )

        title_label.setStyleSheet(
            "font-size: 15px; font-weight: bold;"
        )

        instructions_label = QLabel(
            "Você pode selecionar clicando diretamente "
            "no objeto da viewport ou no layer da árvore.\n\n"
            "Na árvore, use Ctrl + clique para selecionar "
            "vários objetos."
        )

        instructions_label.setWordWrap(True)

        selection_label = QLabel(
            "Objetos selecionados:"
        )

        self.selected_list = QListWidget()

        self.empty_label = QLabel(
            "Nenhum objeto selecionado"
        )

        self.empty_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.delete_button = QPushButton(
            "Excluir selecionados"
        )

        self.delete_button.setEnabled(False)

        cancel_button = QPushButton("Cancelar")

        self.delete_button.clicked.connect(
            self.delete_requested.emit
        )

        cancel_button.clicked.connect(
            self.close
        )

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(
            self.delete_button
        )

        layout = QVBoxLayout(self)
        layout.addWidget(title_label)
        layout.addWidget(instructions_label)
        layout.addSpacing(10)
        layout.addWidget(selection_label)
        layout.addWidget(self.selected_list)
        layout.addWidget(self.empty_label)
        layout.addLayout(buttons_layout)

        self._update_empty_state()

    def set_selected_objects(
        self,
        object_names: list[str],
    ) -> None:
        """Atualiza a lista de objetos selecionados."""

        self.selected_list.clear()

        for object_name in object_names:
            self.selected_list.addItem(
                object_name
            )

        has_selection = bool(object_names)

        self.delete_button.setEnabled(
            has_selection
        )

        self._update_empty_state()

    def _update_empty_state(self) -> None:
        """Atualiza a mensagem de lista vazia."""

        has_items = (
            self.selected_list.count() > 0
        )

        self.selected_list.setVisible(has_items)
        self.empty_label.setVisible(
            not has_items
        )

    def complete_and_close(self) -> None:
        """Fecha a janela sem emitir cancelamento."""

        self._completed = True
        self.close()

    def closeEvent(
        self,
        event: QCloseEvent,
    ) -> None:
        """Trata o cancelamento da janela."""

        if not self._completed:
            self._completed = True
            self.cancel_requested.emit()

        event.accept()