from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)


class PointDialog(QDialog):
    """Janela para criar um ponto por coordenadas."""

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Criar ponto por coordenadas")
        self.setModal(True)
        self.resize(360, 220)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(
            "Automático: Ponto 01"
        )

        self.x_spin = self._create_coordinate_spin()
        self.y_spin = self._create_coordinate_spin()
        self.z_spin = self._create_coordinate_spin()

        form_layout = QFormLayout()
        form_layout.addRow("Nome:", self.name_edit)
        form_layout.addRow("X (mm):", self.x_spin)
        form_layout.addRow("Y (mm):", self.y_spin)
        form_layout.addRow("Z (mm):", self.z_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addStretch()
        layout.addWidget(buttons)

    def _create_coordinate_spin(self) -> QDoubleSpinBox:
        """Cria um campo numérico para coordenadas."""

        spin = QDoubleSpinBox()
        spin.setRange(-1_000_000.0, 1_000_000.0)
        spin.setDecimals(4)
        spin.setSingleStep(1.0)
        spin.setSuffix(" mm")
        return spin

    def point_name(self) -> str | None:
        """Retorna o nome digitado ou None."""

        cleaned = self.name_edit.text().strip()
        return cleaned or None

    def coordinates(
        self,
    ) -> tuple[float, float, float]:
        """Retorna as coordenadas informadas."""

        return (
            float(self.x_spin.value()),
            float(self.y_spin.value()),
            float(self.z_spin.value()),
        )
