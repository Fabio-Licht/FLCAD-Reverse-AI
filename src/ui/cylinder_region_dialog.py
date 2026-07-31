from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class CylinderRegionDialog(QDialog):
    """Parâmetros para reconhecer uma região cilíndrica."""

    def __init__(
        self,
        default_radius: float,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(
            "Reconhecer cilindro por região"
        )
        self.setModal(True)
        self.resize(410, 230)

        self.region_radius_spin = QDoubleSpinBox()
        self.region_radius_spin.setRange(
            0.01,
            1_000_000.0,
        )
        self.region_radius_spin.setDecimals(3)
        self.region_radius_spin.setValue(
            max(default_radius, 0.01)
        )
        self.region_radius_spin.setSuffix(" mm")

        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(1.0, 60.0)
        self.angle_spin.setDecimals(1)
        self.angle_spin.setValue(20.0)
        self.angle_spin.setSuffix("°")

        self.minimum_points_spin = QSpinBox()
        self.minimum_points_spin.setRange(
            20,
            100_000,
        )
        self.minimum_points_spin.setValue(100)

        form = QFormLayout()
        form.addRow(
            "Raio da expansão:",
            self.region_radius_spin,
        )
        form.addRow(
            "Variação angular vizinha:",
            self.angle_spin,
        )
        form.addRow(
            "Mínimo de pontos:",
            self.minimum_points_spin,
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addStretch()
        layout.addWidget(buttons)

    def region_radius(self) -> float:
        return float(
            self.region_radius_spin.value()
        )

    def maximum_neighbor_angle(self) -> float:
        return float(
            self.angle_spin.value()
        )

    def minimum_points(self) -> int:
        return int(
            self.minimum_points_spin.value()
        )
