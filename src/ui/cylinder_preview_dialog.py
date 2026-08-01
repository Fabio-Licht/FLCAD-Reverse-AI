from __future__ import annotations

from math import acos, atan2, cos, degrees, radians, sin, sqrt

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class CylinderPreviewDialog(QDialog):
    """Editor organizado das propriedades do cilindro."""

    geometry_changed = Signal(object)

    LENGTH_REGION = "region"
    LENGTH_EXTENDED = "extended"

    ORIENTATION_RECOGNIZED = "recognized"
    ORIENTATION_CUSTOM = "custom"
    ORIENTATION_X_POSITIVE = "x+"
    ORIENTATION_X_NEGATIVE = "x-"
    ORIENTATION_Y_POSITIVE = "y+"
    ORIENTATION_Y_NEGATIVE = "y-"
    ORIENTATION_Z_POSITIVE = "z+"
    ORIENTATION_Z_NEGATIVE = "z-"

    STATE_RECOGNIZED = "Reconhecido"
    STATE_ADJUSTED = "Ajustado"
    STATE_LOCKED = "Travado"

    PATTERN_NONE = "none"
    PATTERN_LINEAR = "linear"
    PATTERN_CIRCULAR = "circular"

    PATTERN_AXIS_X = "x"
    PATTERN_AXIS_Y = "y"
    PATTERN_AXIS_Z = "z"
    PATTERN_AXIS_CUSTOM = "custom"

    STANDARD_DIAMETERS_MM = (
        1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0,
        10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0,
        25.0, 28.0, 30.0, 32.0, 35.0, 36.0, 38.0, 40.0,
        42.0, 45.0, 48.0, 50.0, 55.0, 60.0, 65.0, 70.0,
        75.0, 80.0, 90.0, 100.0,
    )

    def __init__(
        self,
        *,
        triangle_count: int,
        point_count: int,
        diameter: float,
        length: float,
        rms_error: float,
        maximum_error: float,
        coverage_angle: float,
        center: tuple[float, float, float],
        axis_direction: tuple[float, float, float],
        confidence: float,
        quality_score: float = 0.0,
        quality_grade: str = "Não avaliada",
        quality_stars: int = 0,
        circularity: float = 0.0,
        mean_absolute_error: float = 0.0,
        standard_deviation: float = 0.0,
        relative_rms_percent: float = 0.0,
        inlier_ratio: float = 0.0,
        quality_reasons: tuple[str, ...] = (),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._updating_fields = False
        self._detected_diameter = float(diameter)
        self._detected_center = tuple(
            float(value) for value in center
        )
        self._detected_direction = self._normalized(
            axis_direction
        )

        self.setWindowTitle(
            "Propriedades do cilindro"
        )
        self.setModal(False)
        self.setWindowModality(
            Qt.WindowModality.NonModal
        )
        self.resize(620, 720)
        self.setMinimumSize(560, 560)

        self.status_label = QLabel()
        status_font = QFont()
        status_font.setBold(True)
        status_font.setPointSize(11)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.status_label.setFrameShape(
            QFrame.Shape.StyledPanel
        )
        self.status_label.setMinimumHeight(34)

        explanation = QLabel(
            (
                "Amarelo: região utilizada | Verde: cilindro nominal | "
                "Azul: eixo | Laranja: centro\n"
                "Os dados reconhecidos permanecem preservados mesmo "
                "quando a geometria nominal é ajustada."
            )
        )
        explanation.setWordWrap(True)

        self.tabs = QTabWidget()
        self.tabs.addTab(
            self._create_recognition_tab(
                triangle_count=triangle_count,
                point_count=point_count,
                diameter=diameter,
                length=length,
                rms_error=rms_error,
                maximum_error=maximum_error,
                coverage_angle=coverage_angle,
                center=center,
                axis_direction=axis_direction,
                confidence=confidence,
                quality_score=quality_score,
                quality_grade=quality_grade,
                quality_stars=quality_stars,
                circularity=circularity,
                mean_absolute_error=(
                    mean_absolute_error
                ),
                standard_deviation=(
                    standard_deviation
                ),
                relative_rms_percent=(
                    relative_rms_percent
                ),
                inlier_ratio=inlier_ratio,
                quality_reasons=quality_reasons,
            ),
            "Reconhecimento",
        )
        self.tabs.addTab(
            self._create_nominal_tab(
                diameter=diameter,
                center=center,
            ),
            "Geometria nominal",
        )
        self.tabs.addTab(
            self._create_creation_tab(),
            "Criação",
        )

        self.lock_checkbox = QCheckBox(
            "Travar propriedades nominais após a criação"
        )
        self.lock_checkbox.toggled.connect(
            self._update_status
        )

        restore_all_button = QPushButton(
            "Restaurar todos os valores reconhecidos"
        )
        restore_all_button.clicked.connect(
            self._restore_all_detected
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(
            QDialogButtonBox.StandardButton.Ok
        ).setText("Criar referências")
        buttons.button(
            QDialogButtonBox.StandardButton.Cancel
        ).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.addWidget(self.status_label)
        body_layout.addWidget(explanation)
        body_layout.addWidget(self.tabs)
        body_layout.addWidget(self.lock_checkbox)
        body_layout.addWidget(restore_all_button)
        body_layout.addWidget(buttons)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )
        scroll.setWidget(body)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(scroll)

        self.standard_combo.currentIndexChanged.connect(
            self._apply_standard_diameter
        )
        self.diameter_spin.valueChanged.connect(
            self._on_geometry_field_changed
        )
        self.orientation_combo.currentIndexChanged.connect(
            self._apply_orientation_preset
        )
        self.length_mode_combo.currentIndexChanged.connect(
            self._on_creation_field_changed
        )

        for spin in self.center_spins.values():
            spin.valueChanged.connect(
                self._on_geometry_field_changed
            )

        for spin in self.direction_spins.values():
            spin.valueChanged.connect(
                self._on_direction_vector_changed
            )

        self.inclination_spin.valueChanged.connect(
            self._on_angles_changed
        )
        self.azimuth_spin.valueChanged.connect(
            self._on_angles_changed
        )

        self._set_direction_fields(
            self._detected_direction
        )
        self._update_extension_state()
        self._update_status()

    def _create_recognition_tab(
        self,
        *,
        triangle_count: int,
        point_count: int,
        diameter: float,
        length: float,
        rms_error: float,
        maximum_error: float,
        coverage_angle: float,
        center: tuple[float, float, float],
        axis_direction: tuple[float, float, float],
        confidence: float,
        quality_score: float,
        quality_grade: str,
        quality_stars: int,
        circularity: float,
        mean_absolute_error: float,
        standard_deviation: float,
        relative_rms_percent: float,
        inlier_ratio: float,
        quality_reasons: tuple[str, ...],
    ) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)

        quality_label = QLabel(
            (
                f"{'★' * quality_stars}"
                f"{'☆' * max(0, 5 - quality_stars)}  "
                f"{quality_grade} — {quality_score:.1f}%"
            )
        )
        quality_font = QFont()
        quality_font.setBold(True)
        quality_font.setPointSize(12)
        quality_label.setFont(quality_font)
        quality_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        quality_label.setMinimumHeight(38)

        if quality_score >= 92.0:
            quality_color = "#70e000"
        elif quality_score >= 80.0:
            quality_color = "#a7e65b"
        elif quality_score >= 65.0:
            quality_color = "#ffd166"
        elif quality_score >= 45.0:
            quality_color = "#ff9f43"
        else:
            quality_color = "#ff5b5b"

        quality_label.setStyleSheet(
            (
                "QLabel {"
                f"color: {quality_color};"
                "background-color: rgba(30, 34, 40, 185);"
                "border: 1px solid #56606d;"
                "border-radius: 5px;"
                "padding: 6px;"
                "}"
            )
        )
        layout.addRow(quality_label)

        layout.addRow(
            "Diâmetro reconhecido:",
            QLabel(f"{diameter:.4f} mm"),
        )
        layout.addRow(
            "Centro reconhecido:",
            QLabel(
                f"X {center[0]:.4f} | "
                f"Y {center[1]:.4f} | "
                f"Z {center[2]:.4f} mm"
            ),
        )
        layout.addRow(
            "Direção reconhecida:",
            QLabel(
                f"I {axis_direction[0]:.6f} | "
                f"J {axis_direction[1]:.6f} | "
                f"K {axis_direction[2]:.6f}"
            ),
        )
        layout.addRow(
            "Comprimento:",
            QLabel(f"{length:.4f} mm"),
        )
        layout.addRow(
            "Cobertura angular:",
            QLabel(f"{coverage_angle:.1f}°"),
        )
        layout.addRow(
            "Erro RMS:",
            QLabel(f"{rms_error:.4f} mm"),
        )
        layout.addRow(
            "Erro máximo:",
            QLabel(f"{maximum_error:.4f} mm"),
        )
        layout.addRow(
            "Confiança orientativa:",
            QLabel(f"{confidence:.1f}%"),
        )
        layout.addRow(
            "Circularidade estimada:",
            QLabel(f"{circularity:.4f} mm"),
        )
        layout.addRow(
            "Erro absoluto médio:",
            QLabel(
                f"{mean_absolute_error:.4f} mm"
            ),
        )
        layout.addRow(
            "Desvio-padrão radial:",
            QLabel(
                f"{standard_deviation:.4f} mm"
            ),
        )
        layout.addRow(
            "RMS relativo ao raio:",
            QLabel(
                f"{relative_rms_percent:.3f}%"
            ),
        )
        layout.addRow(
            "Pontos consistentes:",
            QLabel(
                f"{inlier_ratio * 100.0:.1f}%"
            ),
        )
        layout.addRow(
            "Triângulos utilizados:",
            QLabel(str(triangle_count)),
        )
        layout.addRow(
            "Pontos utilizados:",
            QLabel(str(point_count)),
        )

        reasons_text = "\n".join(
            f"• {reason}"
            for reason in quality_reasons
        )

        explanation = QLabel(
            (
                "Por que esta nota?\n"
                f"{reasons_text}"
                if reasons_text
                else "Qualidade ainda não avaliada."
            )
        )
        explanation.setWordWrap(True)
        layout.addRow(explanation)

        note = QLabel(
            (
                "Esses valores vieram da malha e não são alterados. "
                "A nota é orientativa e não substitui uma tolerância "
                "metrológica ou um desenho técnico."
            )
        )
        note.setWordWrap(True)
        layout.addRow(note)

        return tab

    def _create_nominal_tab(
        self,
        *,
        diameter: float,
        center: tuple[float, float, float],
    ) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        diameter_group = QGroupBox(
            "Geometria"
        )
        diameter_layout = QFormLayout(
            diameter_group
        )

        self.diameter_spin = QDoubleSpinBox()
        self.diameter_spin.setRange(
            0.001,
            1_000_000.0,
        )
        self.diameter_spin.setDecimals(4)
        self.diameter_spin.setSingleStep(0.1)
        self.diameter_spin.setValue(diameter)
        self.diameter_spin.setSuffix(" mm")
        self.diameter_spin.setKeyboardTracking(
            False
        )

        self.standard_combo = QComboBox()
        self.standard_combo.addItem(
            "Manter valor reconhecido",
            diameter,
        )
        self.standard_combo.addItem(
            "Arredondar para 0,1 mm",
            round(diameter, 1),
        )
        self.standard_combo.addItem(
            "Arredondar para 0,5 mm",
            round(diameter * 2.0) / 2.0,
        )
        self.standard_combo.addItem(
            "Arredondar para 1 mm",
            round(diameter),
        )

        nearest = min(
            self.STANDARD_DIAMETERS_MM,
            key=lambda value: abs(
                value - diameter
            ),
        )
        self.standard_combo.addItem(
            f"Padrão métrico mais próximo (Ø{nearest:g})",
            nearest,
        )
        self.standard_combo.insertSeparator(
            self.standard_combo.count()
        )

        for value in self.STANDARD_DIAMETERS_MM:
            self.standard_combo.addItem(
                f"Ø {value:g} mm",
                value,
            )

        self.diameter_difference_label = QLabel()
        self._update_diameter_difference(
            diameter
        )

        diameter_layout.addRow(
            "Diâmetro nominal:",
            self.diameter_spin,
        )
        diameter_layout.addRow(
            "Sugestões:",
            self.standard_combo,
        )
        diameter_layout.addRow(
            "Diferença para o scan:",
            self.diameter_difference_label,
        )

        center_group = QGroupBox(
            "Localização global"
        )
        center_layout = QGridLayout(
            center_group
        )

        self.center_spins = {
            "x": self._coordinate_spin(center[0]),
            "y": self._coordinate_spin(center[1]),
            "z": self._coordinate_spin(center[2]),
        }

        for column, key in enumerate(
            ("x", "y", "z")
        ):
            center_layout.addWidget(
                QLabel(key.upper()),
                0,
                column,
            )
            center_layout.addWidget(
                self.center_spins[key],
                1,
                column,
            )

        restore_center_button = QPushButton(
            "Restaurar centro reconhecido"
        )
        restore_center_button.clicked.connect(
            self._restore_detected_center
        )
        center_layout.addWidget(
            restore_center_button,
            2,
            0,
            1,
            3,
        )

        orientation_group = QGroupBox(
            "Orientação do eixo"
        )
        orientation_layout = QFormLayout(
            orientation_group
        )

        self.orientation_combo = QComboBox()
        self.orientation_combo.addItem(
            "Manter direção reconhecida",
            self.ORIENTATION_RECOGNIZED,
        )
        self.orientation_combo.addItem(
            "Paralelo a X+",
            self.ORIENTATION_X_POSITIVE,
        )
        self.orientation_combo.addItem(
            "Paralelo a X−",
            self.ORIENTATION_X_NEGATIVE,
        )
        self.orientation_combo.addItem(
            "Paralelo a Y+",
            self.ORIENTATION_Y_POSITIVE,
        )
        self.orientation_combo.addItem(
            "Paralelo a Y−",
            self.ORIENTATION_Y_NEGATIVE,
        )
        self.orientation_combo.addItem(
            "Paralelo a Z+",
            self.ORIENTATION_Z_POSITIVE,
        )
        self.orientation_combo.addItem(
            "Paralelo a Z−",
            self.ORIENTATION_Z_NEGATIVE,
        )
        self.orientation_combo.addItem(
            "Personalizada",
            self.ORIENTATION_CUSTOM,
        )

        vector_widget = QWidget()
        vector_layout = QHBoxLayout(
            vector_widget
        )
        vector_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.direction_spins = {
            "i": self._direction_spin(
                self._detected_direction[0]
            ),
            "j": self._direction_spin(
                self._detected_direction[1]
            ),
            "k": self._direction_spin(
                self._detected_direction[2]
            ),
        }

        for key in ("i", "j", "k"):
            vector_layout.addWidget(
                QLabel(key.upper())
            )
            vector_layout.addWidget(
                self.direction_spins[key]
            )

        angle_widget = QWidget()
        angle_layout = QHBoxLayout(
            angle_widget
        )
        angle_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.inclination_spin = self._angle_spin(
            minimum=0.0,
            maximum=180.0,
        )
        self.azimuth_spin = self._angle_spin(
            minimum=-180.0,
            maximum=180.0,
        )

        angle_layout.addWidget(
            QLabel("Inclinação Z")
        )
        angle_layout.addWidget(
            self.inclination_spin
        )
        angle_layout.addWidget(
            QLabel("Azimute XY")
        )
        angle_layout.addWidget(
            self.azimuth_spin
        )

        self.axis_angles_label = QLabel()

        orientation_layout.addRow(
            "Referência rápida:",
            self.orientation_combo,
        )
        orientation_layout.addRow(
            "Vetor I/J/K:",
            vector_widget,
        )
        orientation_layout.addRow(
            "Ângulos:",
            angle_widget,
        )
        orientation_layout.addRow(
            "Ângulos com X/Y/Z:",
            self.axis_angles_label,
        )

        restore_direction_button = QPushButton(
            "Restaurar direção reconhecida"
        )
        restore_direction_button.clicked.connect(
            self._restore_detected_direction
        )
        orientation_layout.addRow(
            restore_direction_button
        )

        layout.addWidget(diameter_group)
        layout.addWidget(center_group)
        layout.addWidget(orientation_group)
        layout.addStretch()

        return tab


    def _create_creation_tab(
        self,
    ) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        references_group = QGroupBox(
            "Referência principal"
        )
        references_layout = QFormLayout(
            references_group
        )

        self.length_mode_combo = QComboBox()
        self.length_mode_combo.addItem(
            "Limitado à região reconhecida",
            self.LENGTH_REGION,
        )
        self.length_mode_combo.addItem(
            "Estendido para alinhamento",
            self.LENGTH_EXTENDED,
        )

        self.extension_factor_spin = (
            QDoubleSpinBox()
        )
        self.extension_factor_spin.setRange(
            1.0,
            20.0,
        )
        self.extension_factor_spin.setDecimals(2)
        self.extension_factor_spin.setValue(3.0)
        self.extension_factor_spin.setSingleStep(
            0.5
        )
        self.extension_factor_spin.setSuffix(" ×")
        self.extension_factor_spin.setEnabled(
            False
        )

        self.create_axis_checkbox = QCheckBox(
            "Criar eixo central para cada cilindro"
        )
        self.create_axis_checkbox.setChecked(True)

        self.create_center_checkbox = QCheckBox(
            "Criar ponto central para cada cilindro"
        )
        self.create_center_checkbox.setChecked(
            True
        )

        references_layout.addRow(
            "Comprimento:",
            self.length_mode_combo,
        )
        references_layout.addRow(
            "Fator de extensão:",
            self.extension_factor_spin,
        )
        references_layout.addRow(
            "",
            self.create_axis_checkbox,
        )
        references_layout.addRow(
            "",
            self.create_center_checkbox,
        )

        pattern_group = QGroupBox(
            "Padrão de instâncias"
        )
        pattern_layout = QFormLayout(
            pattern_group
        )

        self.pattern_type_combo = QComboBox()
        self.pattern_type_combo.addItem(
            "Nenhum — criar somente o cilindro",
            self.PATTERN_NONE,
        )
        self.pattern_type_combo.addItem(
            "Linear — repetição por distância",
            self.PATTERN_LINEAR,
        )
        self.pattern_type_combo.addItem(
            "Circular — repetição por ângulo",
            self.PATTERN_CIRCULAR,
        )

        self.pattern_quantity_spin = QSpinBox()
        self.pattern_quantity_spin.setRange(
            1,
            360,
        )
        self.pattern_quantity_spin.setValue(1)
        self.pattern_quantity_spin.setSuffix(
            " entidades"
        )

        self.pattern_spacing_spin = (
            QDoubleSpinBox()
        )
        self.pattern_spacing_spin.setRange(
            0.0,
            1_000_000.0,
        )
        self.pattern_spacing_spin.setDecimals(4)
        self.pattern_spacing_spin.setValue(
            100.0
        )
        self.pattern_spacing_spin.setSuffix(
            " mm"
        )

        self.pattern_angle_spin = (
            QDoubleSpinBox()
        )
        self.pattern_angle_spin.setRange(
            -360.0,
            360.0,
        )
        self.pattern_angle_spin.setDecimals(4)
        self.pattern_angle_spin.setValue(
            30.0
        )
        self.pattern_angle_spin.setSuffix("°")

        self.pattern_axis_combo = QComboBox()
        self.pattern_axis_combo.addItem(
            "Eixo global X",
            self.PATTERN_AXIS_X,
        )
        self.pattern_axis_combo.addItem(
            "Eixo global Y",
            self.PATTERN_AXIS_Y,
        )
        self.pattern_axis_combo.addItem(
            "Eixo global Z",
            self.PATTERN_AXIS_Z,
        )
        self.pattern_axis_combo.addItem(
            "Vetor personalizado",
            self.PATTERN_AXIS_CUSTOM,
        )
        self.pattern_axis_combo.setCurrentIndex(
            self.pattern_axis_combo.findData(
                self.PATTERN_AXIS_Z
            )
        )

        axis_vector_widget = QWidget()
        axis_vector_layout = QHBoxLayout(
            axis_vector_widget
        )
        axis_vector_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.pattern_vector_spins = {
            "i": self._direction_spin(0.0),
            "j": self._direction_spin(0.0),
            "k": self._direction_spin(1.0),
        }

        for key in ("i", "j", "k"):
            axis_vector_layout.addWidget(
                QLabel(key.upper())
            )
            axis_vector_layout.addWidget(
                self.pattern_vector_spins[key]
            )

        origin_widget = QWidget()
        origin_layout = QHBoxLayout(
            origin_widget
        )
        origin_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.pattern_origin_spins = {
            "x": self._coordinate_spin(0.0),
            "y": self._coordinate_spin(0.0),
            "z": self._coordinate_spin(0.0),
        }

        for key in ("x", "y", "z"):
            origin_layout.addWidget(
                QLabel(key.upper())
            )
            origin_layout.addWidget(
                self.pattern_origin_spins[key]
            )

        self.rotate_pattern_orientation_checkbox = (
            QCheckBox(
                "Rotacionar a orientação dos cilindros com o padrão"
            )
        )
        self.rotate_pattern_orientation_checkbox.setChecked(
            False
        )

        pattern_layout.addRow(
            "Tipo:",
            self.pattern_type_combo,
        )
        pattern_layout.addRow(
            "Quantidade total:",
            self.pattern_quantity_spin,
        )
        pattern_layout.addRow(
            "Espaçamento linear:",
            self.pattern_spacing_spin,
        )
        pattern_layout.addRow(
            "Passo angular:",
            self.pattern_angle_spin,
        )
        pattern_layout.addRow(
            "Direção/eixo:",
            self.pattern_axis_combo,
        )
        pattern_layout.addRow(
            "Vetor personalizado:",
            axis_vector_widget,
        )
        pattern_layout.addRow(
            "Origem do eixo circular:",
            origin_widget,
        )
        pattern_layout.addRow(
            "",
            self.rotate_pattern_orientation_checkbox,
        )

        pattern_note = QLabel(
            (
                "A quantidade inclui o cilindro mestre. "
                "Exemplo: quantidade 12 e passo 30° cria o mestre "
                "em 0° e mais 11 instâncias até 330°."
            )
        )
        pattern_note.setWordWrap(True)

        layout.addWidget(references_group)
        layout.addWidget(pattern_group)
        layout.addWidget(pattern_note)
        layout.addStretch()

        self.pattern_type_combo.currentIndexChanged.connect(
            self._on_creation_field_changed
        )
        self.pattern_axis_combo.currentIndexChanged.connect(
            self._on_creation_field_changed
        )
        self.pattern_quantity_spin.valueChanged.connect(
            self._on_creation_field_changed
        )
        self.pattern_spacing_spin.valueChanged.connect(
            self._on_creation_field_changed
        )
        self.pattern_angle_spin.valueChanged.connect(
            self._on_creation_field_changed
        )
        self.extension_factor_spin.valueChanged.connect(
            self._on_creation_field_changed
        )
        self.create_axis_checkbox.toggled.connect(
            self._on_creation_field_changed
        )
        self.create_center_checkbox.toggled.connect(
            self._on_creation_field_changed
        )
        self.rotate_pattern_orientation_checkbox.toggled.connect(
            self._on_creation_field_changed
        )

        for spin in self.pattern_vector_spins.values():
            spin.valueChanged.connect(
                self._on_creation_field_changed
            )

        for spin in self.pattern_origin_spins.values():
            spin.valueChanged.connect(
                self._on_creation_field_changed
            )

        self._update_pattern_state()

        return tab

    def _on_creation_field_changed(
        self,
    ) -> None:
        """Atualiza controles e envia a prévia completa."""

        if self._updating_fields:
            return

        self._update_extension_state()
        self._update_pattern_state()
        self._emit_geometry_changed()

    def _update_pattern_state(
        self,
    ) -> None:
        pattern_type = self.pattern_type()

        active = (
            pattern_type != self.PATTERN_NONE
        )
        is_linear = (
            pattern_type == self.PATTERN_LINEAR
        )
        is_circular = (
            pattern_type == self.PATTERN_CIRCULAR
        )
        is_custom = (
            self.pattern_axis_mode()
            == self.PATTERN_AXIS_CUSTOM
        )

        self.pattern_quantity_spin.setEnabled(
            active
        )
        self.pattern_spacing_spin.setEnabled(
            is_linear
        )
        self.pattern_angle_spin.setEnabled(
            is_circular
        )
        self.pattern_axis_combo.setEnabled(
            active
        )

        for spin in self.pattern_vector_spins.values():
            spin.setEnabled(
                active and is_custom
            )

        for spin in self.pattern_origin_spins.values():
            spin.setEnabled(
                is_circular
            )

        self.rotate_pattern_orientation_checkbox.setEnabled(
            is_circular
        )

    def _coordinate_spin(
        self,
        value: float,
    ) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(
            -1_000_000.0,
            1_000_000.0,
        )
        spin.setDecimals(4)
        spin.setSingleStep(0.1)
        spin.setValue(float(value))
        spin.setSuffix(" mm")
        spin.setKeyboardTracking(False)
        return spin

    def _direction_spin(
        self,
        value: float,
    ) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(-1.0, 1.0)
        spin.setDecimals(6)
        spin.setSingleStep(0.01)
        spin.setValue(float(value))
        spin.setKeyboardTracking(False)
        return spin

    def _angle_spin(
        self,
        *,
        minimum: float,
        maximum: float,
    ) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(3)
        spin.setSingleStep(1.0)
        spin.setSuffix("°")
        spin.setKeyboardTracking(False)
        return spin

    def _normalized(
        self,
        direction: tuple[
            float,
            float,
            float,
        ],
    ) -> tuple[float, float, float]:
        length = sqrt(
            direction[0] ** 2
            + direction[1] ** 2
            + direction[2] ** 2
        )

        if length <= 1.0e-12:
            return (0.0, 0.0, 1.0)

        return (
            direction[0] / length,
            direction[1] / length,
            direction[2] / length,
        )

    def _apply_standard_diameter(
        self,
    ) -> None:
        value = self.standard_combo.currentData()

        if value is not None:
            self.diameter_spin.setValue(
                float(value)
            )

    def _apply_orientation_preset(
        self,
    ) -> None:
        if self._updating_fields:
            return

        preset = str(
            self.orientation_combo.currentData()
        )

        directions = {
            self.ORIENTATION_RECOGNIZED:
                self._detected_direction,
            self.ORIENTATION_X_POSITIVE:
                (1.0, 0.0, 0.0),
            self.ORIENTATION_X_NEGATIVE:
                (-1.0, 0.0, 0.0),
            self.ORIENTATION_Y_POSITIVE:
                (0.0, 1.0, 0.0),
            self.ORIENTATION_Y_NEGATIVE:
                (0.0, -1.0, 0.0),
            self.ORIENTATION_Z_POSITIVE:
                (0.0, 0.0, 1.0),
            self.ORIENTATION_Z_NEGATIVE:
                (0.0, 0.0, -1.0),
        }

        direction = directions.get(preset)

        if direction is not None:
            self._set_direction_fields(
                direction
            )
            self._emit_geometry_changed()

    def _on_direction_vector_changed(
        self,
    ) -> None:
        if self._updating_fields:
            return

        direction = self._normalized(
            (
                self.direction_spins["i"].value(),
                self.direction_spins["j"].value(),
                self.direction_spins["k"].value(),
            )
        )

        self.orientation_combo.blockSignals(True)
        self.orientation_combo.setCurrentIndex(
            self.orientation_combo.findData(
                self.ORIENTATION_CUSTOM
            )
        )
        self.orientation_combo.blockSignals(False)

        self._set_direction_fields(
            direction,
            update_vector=False,
        )
        self._emit_geometry_changed()

    def _on_angles_changed(self) -> None:
        if self._updating_fields:
            return

        inclination = radians(
            self.inclination_spin.value()
        )
        azimuth = radians(
            self.azimuth_spin.value()
        )

        direction = (
            sin(inclination) * cos(azimuth),
            sin(inclination) * sin(azimuth),
            cos(inclination),
        )

        self.orientation_combo.blockSignals(True)
        self.orientation_combo.setCurrentIndex(
            self.orientation_combo.findData(
                self.ORIENTATION_CUSTOM
            )
        )
        self.orientation_combo.blockSignals(False)

        self._set_direction_fields(direction)
        self._emit_geometry_changed()

    def _set_direction_fields(
        self,
        direction: tuple[
            float,
            float,
            float,
        ],
        *,
        update_vector: bool = True,
    ) -> None:
        direction = self._normalized(direction)
        self._updating_fields = True

        try:
            if update_vector:
                for key, value in zip(
                    ("i", "j", "k"),
                    direction,
                ):
                    self.direction_spins[
                        key
                    ].setValue(value)

            inclination = degrees(
                acos(
                    max(
                        -1.0,
                        min(1.0, direction[2]),
                    )
                )
            )
            azimuth = degrees(
                atan2(
                    direction[1],
                    direction[0],
                )
            )

            self.inclination_spin.setValue(
                inclination
            )
            self.azimuth_spin.setValue(
                azimuth
            )

            angles = tuple(
                degrees(
                    acos(
                        max(
                            -1.0,
                            min(1.0, component),
                        )
                    )
                )
                for component in direction
            )

            self.axis_angles_label.setText(
                (
                    f"X {angles[0]:.3f}° | "
                    f"Y {angles[1]:.3f}° | "
                    f"Z {angles[2]:.3f}°"
                )
            )
        finally:
            self._updating_fields = False

    def _restore_detected_center(self) -> None:
        self._updating_fields = True

        try:
            for key, value in zip(
                ("x", "y", "z"),
                self._detected_center,
            ):
                self.center_spins[
                    key
                ].setValue(value)
        finally:
            self._updating_fields = False

        self._emit_geometry_changed()

    def _restore_detected_direction(
        self,
    ) -> None:
        index = self.orientation_combo.findData(
            self.ORIENTATION_RECOGNIZED
        )
        self.orientation_combo.setCurrentIndex(
            index
        )
        self._set_direction_fields(
            self._detected_direction
        )
        self._emit_geometry_changed()

    def _restore_all_detected(self) -> None:
        self._updating_fields = True

        try:
            self.diameter_spin.setValue(
                self._detected_diameter
            )
            for key, value in zip(
                ("x", "y", "z"),
                self._detected_center,
            ):
                self.center_spins[
                    key
                ].setValue(value)
        finally:
            self._updating_fields = False

        self._set_direction_fields(
            self._detected_direction
        )
        self.orientation_combo.setCurrentIndex(
            self.orientation_combo.findData(
                self.ORIENTATION_RECOGNIZED
            )
        )
        self._update_diameter_difference(
            self._detected_diameter
        )
        self._emit_geometry_changed()

    def _on_geometry_field_changed(
        self,
    ) -> None:
        if self._updating_fields:
            return

        self._update_diameter_difference(
            self.diameter_spin.value()
        )
        self._emit_geometry_changed()

    def _update_diameter_difference(
        self,
        diameter: float,
    ) -> None:
        difference = (
            diameter
            - self._detected_diameter
        )
        sign = "+" if difference > 0.0 else ""

        self.diameter_difference_label.setText(
            f"{sign}{difference:.4f} mm"
        )

    def _update_extension_state(self) -> None:
        self.extension_factor_spin.setEnabled(
            self.length_mode()
            == self.LENGTH_EXTENDED
        )

    def _is_adjusted(self) -> bool:
        diameter_changed = abs(
            self.final_diameter()
            - self._detected_diameter
        ) > 1.0e-6

        center_changed = any(
            abs(current - detected) > 1.0e-6
            for current, detected in zip(
                self.final_center(),
                self._detected_center,
            )
        )

        direction_changed = any(
            abs(current - detected) > 1.0e-6
            for current, detected in zip(
                self.final_direction(),
                self._detected_direction,
            )
        )

        return (
            diameter_changed
            or center_changed
            or direction_changed
        )

    def _update_status(self) -> None:
        if self.lock_checkbox.isChecked():
            state = self.STATE_LOCKED
            color = "#7ec8ff"
        elif self._is_adjusted():
            state = self.STATE_ADJUSTED
            color = "#ffd166"
        else:
            state = self.STATE_RECOGNIZED
            color = "#70e000"

        self.status_label.setText(
            f"Estado da referência: {state}"
        )
        self.status_label.setStyleSheet(
            (
                "QLabel {"
                f"color: {color};"
                "background-color: rgba(30, 34, 40, 180);"
                "border: 1px solid #56606d;"
                "border-radius: 5px;"
                "padding: 5px;"
                "}"
            )
        )

    def _emit_geometry_changed(self) -> None:
        self._update_status()
        self.geometry_changed.emit(
            {
                "diameter": self.final_diameter(),
                "center": self.final_center(),
                "direction": self.final_direction(),
                "length_mode": self.length_mode(),
                "extension_factor": self.extension_factor(),
                "create_axis": self.create_axis(),
                "create_center": (
                    self.create_center_point()
                ),
                "pattern_settings": (
                    self.pattern_settings()
                ),
            }
        )



    def apply_creation_preset(self, preset: dict[str, object] | None) -> None:
        """Aplica as opções usadas na última criação de cilindro."""
        if not preset:
            return
        self._updating_fields = True
        try:
            length_mode = str(preset.get("length_mode", self.LENGTH_REGION))
            idx = self.length_mode_combo.findData(length_mode)
            if idx >= 0:
                self.length_mode_combo.setCurrentIndex(idx)
            self.extension_factor_spin.setValue(max(1.0, float(preset.get("extension_factor", 3.0))))
            self.create_axis_checkbox.setChecked(bool(preset.get("create_axis", True)))
            self.create_center_checkbox.setChecked(bool(preset.get("create_center", True)))
            pattern = preset.get("pattern_settings", {})
            if isinstance(pattern, dict):
                idx = self.pattern_type_combo.findData(str(pattern.get("type", self.PATTERN_NONE)))
                if idx >= 0:
                    self.pattern_type_combo.setCurrentIndex(idx)
                self.pattern_quantity_spin.setValue(int(pattern.get("quantity", 1)))
                self.pattern_spacing_spin.setValue(float(pattern.get("spacing", 100.0)))
                self.pattern_angle_spin.setValue(float(pattern.get("angle_step", 30.0)))
                idx = self.pattern_axis_combo.findData(str(pattern.get("axis_mode", self.PATTERN_AXIS_Z)))
                if idx >= 0:
                    self.pattern_axis_combo.setCurrentIndex(idx)
                for key, value in zip(("i", "j", "k"), tuple(pattern.get("axis_direction", (0.0,0.0,1.0)))):
                    self.pattern_vector_spins[key].setValue(float(value))
                for key, value in zip(("x", "y", "z"), tuple(pattern.get("axis_origin", (0.0,0.0,0.0)))):
                    self.pattern_origin_spins[key].setValue(float(value))
                self.rotate_pattern_orientation_checkbox.setChecked(bool(pattern.get("rotate_orientation", False)))
        finally:
            self._updating_fields = False
        self._update_extension_state()
        self._update_pattern_state()

    def creation_preset_values(self) -> dict[str, object]:
        return {
            "length_mode": self.length_mode(),
            "extension_factor": self.extension_factor(),
            "create_axis": self.create_axis(),
            "create_center": self.create_center_point(),
            "pattern_settings": self.pattern_settings(),
        }

    def load_existing_values(
        self,
        *,
        nominal_diameter: float,
        nominal_center: tuple[
            float,
            float,
            float,
        ],
        nominal_direction: tuple[
            float,
            float,
            float,
        ],
        length_mode: str,
        extension_factor: float,
        property_state: str,
        properties_locked: bool,
        pattern_settings: dict[
            str,
            object,
        ] | None = None,
    ) -> None:
        """Carrega uma referência já criada para edição."""

        self._updating_fields = True

        try:
            self.diameter_spin.setValue(
                nominal_diameter
            )

            for key, value in zip(
                ("x", "y", "z"),
                nominal_center,
            ):
                self.center_spins[
                    key
                ].setValue(value)

            self._set_direction_fields(
                nominal_direction
            )

            length_index = (
                self.length_mode_combo.findData(
                    length_mode
                )
            )
            if length_index >= 0:
                self.length_mode_combo.setCurrentIndex(
                    length_index
                )

            self.extension_factor_spin.setValue(
                max(1.0, extension_factor)
            )

            self.lock_checkbox.setChecked(
                properties_locked
                or property_state
                == self.STATE_LOCKED
            )

            if pattern_settings:
                pattern_type = str(
                    pattern_settings.get(
                        "type",
                        self.PATTERN_NONE,
                    )
                )
                pattern_index = (
                    self.pattern_type_combo.findData(
                        pattern_type
                    )
                )
                if pattern_index >= 0:
                    self.pattern_type_combo.setCurrentIndex(
                        pattern_index
                    )

                self.pattern_quantity_spin.setValue(
                    int(
                        pattern_settings.get(
                            "quantity",
                            1,
                        )
                    )
                )
                self.pattern_spacing_spin.setValue(
                    float(
                        pattern_settings.get(
                            "spacing",
                            100.0,
                        )
                    )
                )
                self.pattern_angle_spin.setValue(
                    float(
                        pattern_settings.get(
                            "angle_step",
                            30.0,
                        )
                    )
                )

                axis_mode = str(
                    pattern_settings.get(
                        "axis_mode",
                        self.PATTERN_AXIS_Z,
                    )
                )
                axis_index = (
                    self.pattern_axis_combo.findData(
                        axis_mode
                    )
                )
                if axis_index >= 0:
                    self.pattern_axis_combo.setCurrentIndex(
                        axis_index
                    )

                axis_direction = tuple(
                    pattern_settings.get(
                        "axis_direction",
                        (0.0, 0.0, 1.0),
                    )
                )
                for key, value in zip(
                    ("i", "j", "k"),
                    axis_direction,
                ):
                    self.pattern_vector_spins[
                        key
                    ].setValue(
                        float(value)
                    )

                axis_origin = tuple(
                    pattern_settings.get(
                        "axis_origin",
                        (0.0, 0.0, 0.0),
                    )
                )
                for key, value in zip(
                    ("x", "y", "z"),
                    axis_origin,
                ):
                    self.pattern_origin_spins[
                        key
                    ].setValue(
                        float(value)
                    )

                self.rotate_pattern_orientation_checkbox.setChecked(
                    bool(
                        pattern_settings.get(
                            "rotate_orientation",
                            False,
                        )
                    )
                )
        finally:
            self._updating_fields = False

        self._update_diameter_difference(
            nominal_diameter
        )
        self._update_extension_state()
        self._update_pattern_state()
        self._update_status()
        self._emit_geometry_changed()

    def final_diameter(self) -> float:
        return float(
            self.diameter_spin.value()
        )

    def detected_diameter(self) -> float:
        return self._detected_diameter

    def final_center(
        self,
    ) -> tuple[float, float, float]:
        return (
            float(
                self.center_spins["x"].value()
            ),
            float(
                self.center_spins["y"].value()
            ),
            float(
                self.center_spins["z"].value()
            ),
        )

    def detected_center(
        self,
    ) -> tuple[float, float, float]:
        return self._detected_center

    def final_direction(
        self,
    ) -> tuple[float, float, float]:
        return self._normalized(
            (
                self.direction_spins["i"].value(),
                self.direction_spins["j"].value(),
                self.direction_spins["k"].value(),
            )
        )

    def detected_direction(
        self,
    ) -> tuple[float, float, float]:
        return self._detected_direction

    def property_state(self) -> str:
        if self.lock_checkbox.isChecked():
            return self.STATE_LOCKED

        if self._is_adjusted():
            return self.STATE_ADJUSTED

        return self.STATE_RECOGNIZED

    def properties_locked(self) -> bool:
        return self.lock_checkbox.isChecked()

    def create_axis(self) -> bool:
        return (
            self.create_axis_checkbox.isChecked()
        )

    def create_center_point(self) -> bool:
        return (
            self.create_center_checkbox.isChecked()
        )

    def length_mode(self) -> str:
        return str(
            self.length_mode_combo.currentData()
        )

    def extension_factor(self) -> float:
        return float(
            self.extension_factor_spin.value()
        )

    def pattern_type(self) -> str:
        return str(
            self.pattern_type_combo.currentData()
        )

    def pattern_quantity(self) -> int:
        if self.pattern_type() == self.PATTERN_NONE:
            return 1

        return int(
            self.pattern_quantity_spin.value()
        )

    def pattern_spacing(self) -> float:
        return float(
            self.pattern_spacing_spin.value()
        )

    def pattern_angle_step(self) -> float:
        return float(
            self.pattern_angle_spin.value()
        )

    def pattern_axis_mode(self) -> str:
        return str(
            self.pattern_axis_combo.currentData()
        )

    def pattern_axis_direction(
        self,
    ) -> tuple[float, float, float]:
        mode = self.pattern_axis_mode()

        predefined = {
            self.PATTERN_AXIS_X: (
                1.0,
                0.0,
                0.0,
            ),
            self.PATTERN_AXIS_Y: (
                0.0,
                1.0,
                0.0,
            ),
            self.PATTERN_AXIS_Z: (
                0.0,
                0.0,
                1.0,
            ),
        }

        if mode in predefined:
            return predefined[mode]

        return self._normalized(
            (
                self.pattern_vector_spins["i"].value(),
                self.pattern_vector_spins["j"].value(),
                self.pattern_vector_spins["k"].value(),
            )
        )

    def pattern_axis_origin(
        self,
    ) -> tuple[float, float, float]:
        return (
            float(
                self.pattern_origin_spins["x"].value()
            ),
            float(
                self.pattern_origin_spins["y"].value()
            ),
            float(
                self.pattern_origin_spins["z"].value()
            ),
        )

    def pattern_rotates_orientation(self) -> bool:
        return (
            self.rotate_pattern_orientation_checkbox.isChecked()
        )

    def pattern_settings(self) -> dict[str, object]:
        return {
            "type": self.pattern_type(),
            "quantity": self.pattern_quantity(),
            "spacing": self.pattern_spacing(),
            "angle_step": self.pattern_angle_step(),
            "axis_mode": self.pattern_axis_mode(),
            "axis_direction": (
                self.pattern_axis_direction()
            ),
            "axis_origin": self.pattern_axis_origin(),
            "rotate_orientation": (
                self.pattern_rotates_orientation()
            ),
        }
