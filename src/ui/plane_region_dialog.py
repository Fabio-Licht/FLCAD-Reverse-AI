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


class PlaneRegionDialog(QDialog):
    """Parâmetros para reconhecer um plano em uma região local."""

    def __init__(
        self,
        default_radius: float,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(
            "Reconhecer plano por região"
        )
        self.setModal(True)
        self.resize(390, 210)

        self.radius_spin = QDoubleSpinBox()
        self.radius_spin.setRange(
            0.01,
            1_000_000.0,
        )
        self.radius_spin.setDecimals(3)
        self.radius_spin.setSingleStep(
            max(default_radius * 0.10, 0.10)
        )
        self.radius_spin.setValue(
            max(default_radius, 0.01)
        )
        self.radius_spin.setSuffix(" mm")

        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(
            1.0,
            45.0,
        )
        self.angle_spin.setDecimals(1)
        self.angle_spin.setSingleStep(1.0)
        self.angle_spin.setValue(12.0)
        self.angle_spin.setSuffix("°")

        self.minimum_points_spin = QSpinBox()
        self.minimum_points_spin.setRange(
            10,
            100_000,
        )
        self.minimum_points_spin.setValue(50)

        self.plane_scale_spin = QDoubleSpinBox()
        self.plane_scale_spin.setRange(
            1.0,
            5.0,
        )
        self.plane_scale_spin.setDecimals(2)
        self.plane_scale_spin.setSingleStep(0.10)
        self.plane_scale_spin.setValue(2.0)
        self.plane_scale_spin.setSuffix(" × raio")

        form = QFormLayout()
        form.addRow(
            "Raio da região:",
            self.radius_spin,
        )
        form.addRow(
            "Limite angular:",
            self.angle_spin,
        )
        form.addRow(
            "Mínimo de pontos:",
            self.minimum_points_spin,
        )
        form.addRow(
            "Tamanho visual do plano:",
            self.plane_scale_spin,
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
            self.radius_spin.value()
        )

    def maximum_angle(self) -> float:
        return float(
            self.angle_spin.value()
        )

    def minimum_points(self) -> int:
        return int(
            self.minimum_points_spin.value()
        )

    def plane_scale(self) -> float:
        return float(
            self.plane_scale_spin.value()
        )
