from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QGroupBox, QLabel,
    QVBoxLayout, QWidget,
)


class CylinderPreviewDialog(QDialog):
    """Confirma e permite ajustar a referência cilíndrica."""

    diameter_changed = Signal(float)

    LENGTH_REGION = "region"
    LENGTH_EXTENDED = "extended"

    STANDARD_DIAMETERS_MM = (
        1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0,
        10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0,
        25.0, 28.0, 30.0, 32.0, 35.0, 36.0, 38.0, 40.0,
        42.0, 45.0, 48.0, 50.0, 55.0, 60.0, 65.0, 70.0,
        75.0, 80.0, 90.0, 100.0,
    )

    def __init__(self, *, triangle_count: int, point_count: int,
                 diameter: float, length: float, rms_error: float,
                 maximum_error: float, coverage_angle: float,
                 axis_direction: tuple[float, float, float],
                 confidence: float, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._detected_diameter = float(diameter)
        self.setWindowTitle("Pré-visualização do cilindro")
        self.setModal(False)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.resize(520, 620)

        explanation = QLabel(
            """Região usada: amarelo translúcido
Cilindro calculado: verde translúcido
Eixo central: azul
Ponto central: laranja

O diâmetro pode ser mantido como reconhecido ou ajustado para uma medida nominal padrão. A prévia é atualizada imediatamente."""
        )
        explanation.setWordWrap(True)

        metrics_group = QGroupBox("Resultado do reconhecimento")
        metrics = QFormLayout(metrics_group)
        metrics.addRow("Diâmetro reconhecido:", QLabel(f"{diameter:.4f} mm"))
        metrics.addRow("Comprimento reconhecido:", QLabel(f"{length:.4f} mm"))
        metrics.addRow("Cobertura angular:", QLabel(f"{coverage_angle:.1f}°"))
        metrics.addRow("Erro RMS:", QLabel(f"{rms_error:.4f} mm"))
        metrics.addRow("Erro máximo:", QLabel(f"{maximum_error:.4f} mm"))
        metrics.addRow("Confiança:", QLabel(f"{confidence:.1f}%"))
        metrics.addRow("Triângulos:", QLabel(str(triangle_count)))
        metrics.addRow("Pontos usados:", QLabel(str(point_count)))
        metrics.addRow("Direção do eixo:", QLabel(
            f"({axis_direction[0]:.4f}, {axis_direction[1]:.4f}, {axis_direction[2]:.4f})"
        ))

        nominal_group = QGroupBox("Diâmetro nominal")
        nominal = QFormLayout(nominal_group)
        self.diameter_spin = QDoubleSpinBox()
        self.diameter_spin.setRange(0.001, 1_000_000.0)
        self.diameter_spin.setDecimals(4)
        self.diameter_spin.setSingleStep(0.1)
        self.diameter_spin.setValue(diameter)
        self.diameter_spin.setSuffix(" mm")
        self.diameter_spin.setKeyboardTracking(False)

        self.standard_combo = QComboBox()
        self.standard_combo.addItem("Manter valor reconhecido", diameter)
        self.standard_combo.addItem("Arredondar para 0,1 mm", round(diameter,1))
        self.standard_combo.addItem("Arredondar para 0,5 mm", round(diameter*2.0)/2.0)
        self.standard_combo.addItem("Arredondar para 1 mm", round(diameter))
        nearest=min(self.STANDARD_DIAMETERS_MM, key=lambda v: abs(v-diameter))
        self.standard_combo.addItem(f"Padrão métrico mais próximo (Ø{nearest:g})", nearest)
        self.standard_combo.insertSeparator(self.standard_combo.count())
        for value in self.STANDARD_DIAMETERS_MM:
            self.standard_combo.addItem(f"Ø {value:g} mm", value)

        self.nominal_difference_label = QLabel()
        self._update_difference_label(diameter)
        self.standard_combo.currentIndexChanged.connect(self._apply_standard_diameter)
        self.diameter_spin.valueChanged.connect(self._on_diameter_changed)
        nominal.addRow("Diâmetro final:", self.diameter_spin)
        nominal.addRow("Sugestões:", self.standard_combo)
        nominal.addRow("Diferença para o scan:", self.nominal_difference_label)

        options_group = QGroupBox("Opções de criação")
        options = QFormLayout(options_group)
        self.length_mode_combo = QComboBox()
        self.length_mode_combo.addItem("Limitado à região reconhecida", self.LENGTH_REGION)
        self.length_mode_combo.addItem("Estendido para alinhamento", self.LENGTH_EXTENDED)
        self.extension_factor_spin = QDoubleSpinBox()
        self.extension_factor_spin.setRange(1.0,20.0)
        self.extension_factor_spin.setDecimals(2)
        self.extension_factor_spin.setValue(3.0)
        self.extension_factor_spin.setSingleStep(0.5)
        self.extension_factor_spin.setSuffix(" ×")
        self.extension_factor_spin.setEnabled(False)
        self.length_mode_combo.currentIndexChanged.connect(self._update_extension_state)
        self.create_axis_checkbox = QCheckBox("Criar eixo central")
        self.create_axis_checkbox.setChecked(True)
        self.create_center_checkbox = QCheckBox("Criar ponto central")
        self.create_center_checkbox.setChecked(True)
        options.addRow("Comprimento:", self.length_mode_combo)
        options.addRow("Fator de extensão:", self.extension_factor_spin)
        options.addRow("", self.create_axis_checkbox)
        options.addRow("", self.create_center_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Criar referências")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout=QVBoxLayout(self)
        layout.addWidget(explanation)
        layout.addSpacing(8)
        layout.addWidget(metrics_group)
        layout.addWidget(nominal_group)
        layout.addWidget(options_group)
        layout.addStretch()
        layout.addWidget(buttons)

    def _apply_standard_diameter(self) -> None:
        value=self.standard_combo.currentData()
        if value is not None:
            self.diameter_spin.setValue(float(value))

    def _on_diameter_changed(self, value: float) -> None:
        self._update_difference_label(value)
        self.diameter_changed.emit(float(value))

    def _update_difference_label(self, diameter: float) -> None:
        difference=diameter-self._detected_diameter
        sign="+" if difference>0 else ""
        self.nominal_difference_label.setText(f"{sign}{difference:.4f} mm")

    def _update_extension_state(self) -> None:
        self.extension_factor_spin.setEnabled(self.length_mode()==self.LENGTH_EXTENDED)

    def final_diameter(self) -> float:
        return float(self.diameter_spin.value())

    def detected_diameter(self) -> float:
        return self._detected_diameter

    def create_axis(self) -> bool:
        return self.create_axis_checkbox.isChecked()

    def create_center_point(self) -> bool:
        return self.create_center_checkbox.isChecked()

    def length_mode(self) -> str:
        return str(self.length_mode_combo.currentData())

    def extension_factor(self) -> float:
        return float(self.extension_factor_spin.value())
