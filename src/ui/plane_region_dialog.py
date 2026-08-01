from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class PlaneRegionDialog(QDialog):
    """Painel não modal para reconhecimento interativo de planos."""

    selection_requested = Signal()
    recalculate_requested = Signal()
    create_requested = Signal()
    clear_requested = Signal()
    cancel_requested = Signal()

    def __init__(
        self,
        default_radius: float,
        preset: dict[str, object] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        preset = dict(preset or {})
        self._has_seed = False
        self._calculation_in_progress = False

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(450)
        self._timer.timeout.connect(
            self._emit_automatic_recalculation
        )

        self.setWindowTitle(
            "Reconhecer plano por região"
        )
        self.setModal(False)
        self.resize(430, 360)
        self.setMinimumWidth(410)

        explanation = QLabel(
            (
                "A janela permanece aberta enquanto você "
                "seleciona a malha. Depois altere os parâmetros "
                "e recalcule sem clicar novamente."
            )
        )
        explanation.setWordWrap(True)

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
            max(
                float(
                    preset.get(
                        "region_radius",
                        default_radius,
                    )
                ),
                0.01,
            )
        )
        self.radius_spin.setSuffix(" mm")
        self.radius_spin.setKeyboardTracking(False)

        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(1.0, 45.0)
        self.angle_spin.setDecimals(1)
        self.angle_spin.setSingleStep(1.0)
        self.angle_spin.setValue(
            float(
                preset.get(
                    "maximum_angle",
                    12.0,
                )
            )
        )
        self.angle_spin.setSuffix("°")
        self.angle_spin.setKeyboardTracking(False)

        self.minimum_points_spin = QSpinBox()
        self.minimum_points_spin.setRange(
            10,
            100_000,
        )
        self.minimum_points_spin.setValue(
            int(
                preset.get(
                    "minimum_points",
                    50,
                )
            )
        )

        self.plane_scale_spin = QDoubleSpinBox()
        self.plane_scale_spin.setRange(1.0, 5.0)
        self.plane_scale_spin.setDecimals(2)
        self.plane_scale_spin.setSingleStep(0.10)
        self.plane_scale_spin.setValue(
            float(
                preset.get(
                    "plane_scale",
                    2.0,
                )
            )
        )
        self.plane_scale_spin.setSuffix(" × raio")
        self.plane_scale_spin.setKeyboardTracking(False)

        self.auto_checkbox = QCheckBox(
            "Recalcular automaticamente ao alterar parâmetros"
        )
        self.auto_checkbox.setChecked(
            bool(
                preset.get(
                    "auto_recalculate",
                    True,
                )
            )
        )

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
            "Tamanho visual:",
            self.plane_scale_spin,
        )
        form.addRow("", self.auto_checkbox)

        self.status_label = QLabel(
            "Aguardando seleção."
        )
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            (
                "QLabel {"
                "background-color: rgba(35, 40, 48, 180);"
                "border: 1px solid #56606d;"
                "border-radius: 5px;"
                "padding: 8px;"
                "}"
            )
        )

        self.result_label = QLabel(
            "Resultado ainda não calculado."
        )
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet(
            (
                "QLabel {"
                "background-color: rgba(25, 30, 36, 180);"
                "border: 1px solid #56606d;"
                "border-radius: 5px;"
                "padding: 8px;"
                "}"
            )
        )

        self.select_button = QPushButton(
            "Selecionar região"
        )
        self.select_button.clicked.connect(
            self.selection_requested.emit
        )

        self.recalculate_button = QPushButton(
            "Recalcular"
        )
        self.recalculate_button.setEnabled(False)
        self.recalculate_button.clicked.connect(
            self.recalculate_requested.emit
        )

        self.create_button = QPushButton(
            "Criar plano"
        )
        self.create_button.setEnabled(False)
        self.create_button.clicked.connect(
            self.create_requested.emit
        )

        self.clear_button = QPushButton(
            "Limpar"
        )
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(
            self.clear_requested.emit
        )

        self.cancel_button = QPushButton(
            "Cancelar"
        )
        self.cancel_button.clicked.connect(
            self._request_cancel
        )

        first_row = QHBoxLayout()
        first_row.addWidget(self.select_button)
        first_row.addWidget(self.recalculate_button)
        first_row.addWidget(self.clear_button)

        second_row = QHBoxLayout()
        second_row.addWidget(self.create_button)
        second_row.addWidget(self.cancel_button)

        layout = QVBoxLayout(self)
        layout.addWidget(explanation)
        layout.addLayout(form)
        layout.addWidget(self.status_label)
        layout.addWidget(self.result_label)
        layout.addStretch()
        layout.addLayout(first_row)
        layout.addLayout(second_row)

        for widget in (
            self.radius_spin,
            self.angle_spin,
            self.minimum_points_spin,
            self.plane_scale_spin,
        ):
            widget.valueChanged.connect(
                self._schedule_automatic_recalculation
            )

    def _request_cancel(self) -> None:
        self._timer.stop()
        self.cancel_requested.emit()

    def closeEvent(self, event) -> None:
        self.cancel_requested.emit()
        event.ignore()

    def _schedule_automatic_recalculation(
        self,
    ) -> None:
        if (
            not self.auto_checkbox.isChecked()
            or not self._has_seed
            or self._calculation_in_progress
        ):
            return

        self.status_label.setText(
            "Parâmetros alterados. Recalculando..."
        )
        self._timer.start()

    def _emit_automatic_recalculation(
        self,
    ) -> None:
        if (
            self.auto_checkbox.isChecked()
            and self._has_seed
            and not self._calculation_in_progress
        ):
            self.recalculate_requested.emit()

    def set_selection_active(
        self,
        active: bool,
    ) -> None:
        self.select_button.setEnabled(
            not active
        )
        self.select_button.setText(
            "Seleção ativa"
            if active
            else "Selecionar região"
        )

    def set_seed_selected(self) -> None:
        self._has_seed = True
        self.clear_button.setEnabled(True)
        self.recalculate_button.setEnabled(True)
        self.status_label.setText(
            "Região selecionada. Calculando..."
        )

    def set_calculation_in_progress(
        self,
        active: bool,
    ) -> None:
        self._calculation_in_progress = active
        self.recalculate_button.setEnabled(
            self._has_seed and not active
        )
        self.create_button.setEnabled(
            self.create_button.isEnabled()
            and not active
        )


    def set_result(
        self,
        *,
        rms_error: float,
        maximum_error: float,
        point_count: int,
        triangle_count: int,
        normal: tuple[float, float, float],
        quality_score: float,
        quality_grade: str,
        quality_stars: int,
        mean_absolute_error: float,
        standard_deviation: float,
        inlier_ratio: float,
        quality_reasons: tuple[str, ...],
    ) -> None:
        self._calculation_in_progress = False

        reasons_text = "\n".join(
            f"• {reason}"
            for reason in quality_reasons
        )
        stars_text = (
            "★" * quality_stars
            + "☆" * max(0, 5 - quality_stars)
        )

        self.result_label.setText(
            (
                f"{stars_text}  {quality_grade} "
                f"— {quality_score:.1f}%\n"
                f"RMS: {rms_error:.4f} mm\n"
                f"Erro máximo: {maximum_error:.4f} mm\n"
                f"Erro absoluto médio: "
                f"{mean_absolute_error:.4f} mm\n"
                f"Desvio-padrão: "
                f"{standard_deviation:.4f} mm\n"
                f"Pontos consistentes: "
                f"{inlier_ratio * 100.0:.1f}%\n"
                f"Pontos: {point_count}\n"
                f"Triângulos: {triangle_count}\n"
                f"Normal: "
                f"{normal[0]:.4f}, "
                f"{normal[1]:.4f}, "
                f"{normal[2]:.4f}\n\n"
                f"{reasons_text}"
            )
        )
        self.status_label.setText(
            "Plano reconhecido. Ajuste ou confirme."
        )
        self.create_button.setEnabled(True)
        self.recalculate_button.setEnabled(True)
        self.select_button.setEnabled(True)
        self.select_button.setText(
            "Selecionar novamente"
        )
    def set_error(
        self,
        message: str,
    ) -> None:
        self._calculation_in_progress = False
        self.result_label.setText(
            "Resultado inválido."
        )
        self.status_label.setText(
            f"Não foi possível reconhecer:\n{message}"
        )
        self.create_button.setEnabled(False)
        self.select_button.setEnabled(True)
        self.select_button.setText(
            "Selecionar novamente"
        )

    def clear_state(self) -> None:
        self._timer.stop()
        self._has_seed = False
        self._calculation_in_progress = False
        self.status_label.setText(
            "Aguardando seleção."
        )
        self.result_label.setText(
            "Resultado ainda não calculado."
        )
        self.select_button.setEnabled(True)
        self.select_button.setText(
            "Selecionar região"
        )
        self.recalculate_button.setEnabled(False)
        self.create_button.setEnabled(False)
        self.clear_button.setEnabled(False)

    def region_radius(self) -> float:
        return float(self.radius_spin.value())

    def maximum_angle(self) -> float:
        return float(self.angle_spin.value())

    def minimum_points(self) -> int:
        return int(
            self.minimum_points_spin.value()
        )

    def plane_scale(self) -> float:
        return float(
            self.plane_scale_spin.value()
        )

    def preset_values(self) -> dict[str, object]:
        return {
            "region_radius": self.region_radius(),
            "maximum_angle": self.maximum_angle(),
            "minimum_points": self.minimum_points(),
            "plane_scale": self.plane_scale(),
            "auto_recalculate": (
                self.auto_checkbox.isChecked()
            ),
        }
