from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class CylinderRegionDialog(QDialog):
    """Painel persistente do reconhecimento cilíndrico."""

    selection_requested = Signal()
    clear_requested = Signal()
    recalculate_requested = Signal()
    automatic_recalculate_requested = Signal()
    history_result_requested = Signal(int)
    add_to_batch_requested = Signal()
    create_batch_requested = Signal()
    continue_requested = Signal()
    cancel_requested = Signal()

    def __init__(
        self,
        default_radius: float,
        preset: dict[str, object] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        preset = dict(preset or {})

        self._collected_seed_count = 0
        self._calculation_in_progress = False

        self._recalculate_timer = QTimer(self)
        self._recalculate_timer.setSingleShot(True)
        self._recalculate_timer.setInterval(450)
        self._recalculate_timer.timeout.connect(
            self._emit_automatic_recalculation
        )

        self.setWindowTitle(
            "Reconhecer cilindro por região"
        )
        self.setModal(False)
        self.resize(450, 420)
        self.setMinimumWidth(420)

        explanation = QLabel(
            (
                "Configure os parâmetros, selecione as sementes "
                "e avalie o resultado sem fechar este painel. "
                "Depois altere os valores e use Recalcular."
            )
        )
        explanation.setWordWrap(True)

        self.region_radius_spin = QDoubleSpinBox()
        self.region_radius_spin.setRange(
            0.01,
            1_000_000.0,
        )
        self.region_radius_spin.setDecimals(3)
        self.region_radius_spin.setValue(
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
        self.region_radius_spin.setSuffix(" mm")
        self.region_radius_spin.setKeyboardTracking(
            False
        )

        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(1.0, 60.0)
        self.angle_spin.setDecimals(1)
        self.angle_spin.setValue(
            float(
                preset.get(
                    "maximum_neighbor_angle",
                    20.0,
                )
            )
        )
        self.angle_spin.setSuffix("°")
        self.angle_spin.setKeyboardTracking(False)

        self.seed_count_spin = QSpinBox()
        self.seed_count_spin.setRange(1, 2)
        self.seed_count_spin.setValue(
            int(
                preset.get(
                    "seed_count",
                    2,
                )
            )
        )
        self.seed_count_spin.setSuffix(" pontos")

        self.minimum_points_spin = QSpinBox()
        self.minimum_points_spin.setRange(
            20,
            100_000,
        )
        self.minimum_points_spin.setValue(
            int(
                preset.get(
                    "minimum_points",
                    100,
                )
            )
        )

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
            "Sementes de seleção:",
            self.seed_count_spin,
        )
        form.addRow(
            "Mínimo de pontos:",
            self.minimum_points_spin,
        )

        self.auto_recalculate_checkbox = QCheckBox(
            "Recalcular automaticamente ao alterar parâmetros"
        )
        self.auto_recalculate_checkbox.setChecked(
            bool(
                preset.get(
                    "auto_recalculate",
                    True,
                )
            )
        )
        form.addRow(
            "",
            self.auto_recalculate_checkbox,
        )

        self.multi_recognition_checkbox = QCheckBox(
            "Multi-reconhecimento: acumular vários cilindros"
        )
        self.multi_recognition_checkbox.setChecked(
            bool(
                preset.get(
                    "multi_recognition",
                    False,
                )
            )
        )
        self.multi_recognition_checkbox.setToolTip(
            (
                "Adiciona cada resultado válido a um lote e permite "
                "criar todos de uma vez."
            )
        )
        form.addRow(
            "",
            self.multi_recognition_checkbox,
        )

        self.production_mode_checkbox = QCheckBox(
            "Modo produção: manter o comando ativo após criar"
        )
        self.production_mode_checkbox.setChecked(
            bool(
                preset.get(
                    "production_mode",
                    False,
                )
            )
        )
        self.production_mode_checkbox.setToolTip(
            (
                "Depois de criar um cilindro, o painel de "
                "reconhecimento será aberto novamente para a "
                "próxima seleção."
            )
        )
        form.addRow(
            "",
            self.production_mode_checkbox,
        )

        self.progress_label = QLabel(
            "Aguardando início da seleção."
        )
        self.progress_label.setWordWrap(True)
        self.progress_label.setStyleSheet(
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

        self.history_label = QLabel(
            "Histórico da sessão"
        )
        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(105)
        self.history_list.setToolTip(
            (
                "Cada recálculo válido fica registrado. "
                "Dê duplo clique para recuperar um resultado."
            )
        )
        self.history_list.itemDoubleClicked.connect(
            self._request_selected_history_result
        )

        self.use_history_button = QPushButton(
            "Usar resultado selecionado"
        )
        self.use_history_button.setEnabled(False)
        self.use_history_button.clicked.connect(
            self._request_selected_history_result
        )
        self.history_list.currentRowChanged.connect(
            lambda row: self.use_history_button.setEnabled(
                row >= 0
            )
        )

        self.select_button = QPushButton(
            "Selecionar sementes"
        )
        self.select_button.clicked.connect(
            self.selection_requested.emit
        )

        self.clear_button = QPushButton(
            "Limpar sementes"
        )
        self.clear_button.clicked.connect(
            self.clear_requested.emit
        )
        self.clear_button.setEnabled(False)

        self.recalculate_button = QPushButton(
            "Recalcular"
        )
        self.recalculate_button.clicked.connect(
            self.recalculate_requested.emit
        )
        self.recalculate_button.setEnabled(False)

        self.continue_button = QPushButton(
            "Abrir propriedades"
        )
        self.continue_button.clicked.connect(
            self.continue_requested.emit
        )
        self.continue_button.setEnabled(False)

        self.cancel_button = QPushButton(
            "Cancelar"
        )
        self.cancel_button.clicked.connect(
            self._request_cancel
        )

        first_row = QHBoxLayout()
        first_row.addWidget(self.select_button)
        first_row.addWidget(self.clear_button)
        first_row.addWidget(self.recalculate_button)

        second_row = QHBoxLayout()
        second_row.addWidget(self.continue_button)
        second_row.addWidget(self.cancel_button)

        layout = QVBoxLayout(self)
        layout.addWidget(explanation)
        layout.addLayout(form)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.result_label)
        layout.addWidget(self.history_label)
        layout.addWidget(self.history_list)
        self.batch_label = QLabel(
            "Lote de cilindros: 0"
        )
        self.batch_list = QListWidget()
        self.batch_list.setMinimumHeight(85)

        self.add_batch_button = QPushButton(
            "Adicionar resultado ao lote"
        )
        self.add_batch_button.setEnabled(False)
        self.add_batch_button.clicked.connect(
            self.add_to_batch_requested.emit
        )

        self.create_batch_button = QPushButton(
            "Criar lote"
        )
        self.create_batch_button.setEnabled(False)
        self.create_batch_button.clicked.connect(
            self.create_batch_requested.emit
        )

        batch_row = QHBoxLayout()
        batch_row.addWidget(self.add_batch_button)
        batch_row.addWidget(self.create_batch_button)

        layout.addWidget(self.use_history_button)
        layout.addWidget(self.batch_label)
        layout.addWidget(self.batch_list)
        layout.addLayout(batch_row)
        layout.addStretch()
        layout.addLayout(first_row)
        layout.addLayout(second_row)

        for widget in (
            self.region_radius_spin,
            self.angle_spin,
            self.minimum_points_spin,
        ):
            widget.valueChanged.connect(
                self._schedule_automatic_recalculation
            )

        self.seed_count_spin.valueChanged.connect(
            self._on_seed_count_changed
        )
        self.auto_recalculate_checkbox.toggled.connect(
            self._on_auto_recalculate_toggled
        )

    def _request_selected_history_result(
        self,
        item=None,
    ) -> None:
        row = self.history_list.currentRow()

        if row >= 0:
            self.history_result_requested.emit(row)

    def add_history_result(
        self,
        *,
        attempt_number: int,
        diameter: float,
        rms_error: float,
        coverage_angle: float,
        quality_grade: str,
        quality_score: float,
        region_radius: float,
        neighbor_angle: float,
        is_best: bool,
    ) -> None:
        prefix = "★ " if is_best else ""
        text = (
            f"{prefix}{attempt_number:02d} | "
            f"Ø {diameter:.4f} | "
            f"RMS {rms_error:.4f} | "
            f"{coverage_angle:.1f}° | "
            f"{quality_grade} {quality_score:.1f}% | "
            f"R {region_radius:.2f} / A {neighbor_angle:.1f}°"
        )
        self.history_list.addItem(text)
        self.history_list.setCurrentRow(
            self.history_list.count() - 1
        )

    def mark_best_history_result(
        self,
        best_index: int,
    ) -> None:
        for index in range(
            self.history_list.count()
        ):
            item = self.history_list.item(index)
            text = item.text()

            if text.startswith("★ "):
                text = text[2:]

            if index == best_index:
                text = "★ " + text

            item.setText(text)

    def clear_history_results(self) -> None:
        self.history_list.clear()
        self.use_history_button.setEnabled(False)

    def select_history_result(
        self,
        index: int,
    ) -> None:
        if (
            index >= 0
            and index < self.history_list.count()
        ):
            self.history_list.setCurrentRow(index)

    def _request_cancel(self) -> None:
        self._recalculate_timer.stop()
        self.cancel_requested.emit()

    def _on_seed_count_changed(self) -> None:
        self.clear_result()
        self._collected_seed_count = 0
        self.set_seed_progress(
            0,
            self.seed_count(),
            "Quantidade de sementes alterada. Selecione novamente.",
        )

    def _on_auto_recalculate_toggled(
        self,
        enabled: bool,
    ) -> None:
        if not enabled:
            self._recalculate_timer.stop()
            return

        self._schedule_automatic_recalculation()

    def _schedule_automatic_recalculation(
        self,
    ) -> None:
        if (
            not self.auto_recalculate_checkbox.isChecked()
            or self._calculation_in_progress
            or self._collected_seed_count
            < self.seed_count()
        ):
            return

        self.progress_label.setText(
            (
                f"Sementes: "
                f"{self._collected_seed_count}/"
                f"{self.seed_count()}\n"
                "Parâmetros alterados. "
                "Recalculando automaticamente..."
            )
        )
        self._recalculate_timer.start()

    def _emit_automatic_recalculation(
        self,
    ) -> None:
        if (
            self.auto_recalculate_checkbox.isChecked()
            and not self._calculation_in_progress
            and self._collected_seed_count
            >= self.seed_count()
        ):
            self.automatic_recalculate_requested.emit()

    def set_calculation_in_progress(
        self,
        active: bool,
    ) -> None:
        self._calculation_in_progress = active
        self.recalculate_button.setEnabled(
            not active
            and self._collected_seed_count
            >= self.seed_count()
        )
        self.continue_button.setEnabled(
            not active
            and self.continue_button.isEnabled()
        )

        if active:
            self.progress_label.setText(
                (
                    f"Sementes: "
                    f"{self._collected_seed_count}/"
                    f"{self.seed_count()}\n"
                    "Calculando reconhecimento..."
                )
            )

    def closeEvent(self, event) -> None:
        self.cancel_requested.emit()
        event.ignore()

    def set_selection_active(
        self,
        active: bool,
    ) -> None:
        self.select_button.setText(
            (
                "Seleção ativa"
                if active
                else "Selecionar sementes"
            )
        )
        self.select_button.setEnabled(
            not active
        )

    def set_seed_progress(
        self,
        collected: int,
        required: int,
        message: str | None = None,
    ) -> None:
        if message is None:
            if collected <= 0:
                message = (
                    "Clique na primeira região da "
                    "parede cilíndrica."
                )
            elif collected < required:
                message = (
                    f"Semente {collected} registrada. "
                    "Clique em outra região da mesma parede."
                )
            else:
                message = (
                    "Sementes completas. "
                    "Calculando reconhecimento..."
                )

        self._collected_seed_count = int(
            collected
        )

        self.progress_label.setText(
            (
                f"Sementes: {collected}/{required}\n"
                f"{message}"
            )
        )
        self.clear_button.setEnabled(
            collected > 0
        )
        self.recalculate_button.setEnabled(
            collected >= required
        )

    def set_result(
        self,
        *,
        diameter: float,
        rms_error: float,
        coverage_angle: float,
        quality_grade: str,
        quality_score: float,
        point_count: int,
    ) -> None:
        self.result_label.setText(
            (
                f"Resultado atual\n"
                f"Diâmetro: {diameter:.4f} mm\n"
                f"RMS: {rms_error:.4f} mm\n"
                f"Cobertura: {coverage_angle:.1f}°\n"
                f"Pontos: {point_count}\n"
                f"Qualidade: {quality_grade} "
                f"({quality_score:.1f}%)"
            )
        )
        self._calculation_in_progress = False
        self.continue_button.setEnabled(True)
        self.recalculate_button.setEnabled(True)
        self.add_batch_button.setEnabled(
            self.multi_recognition_checkbox.isChecked()
        )
        self.select_button.setEnabled(True)
        self.select_button.setText(
            "Selecionar novamente"
        )

    def clear_result(self) -> None:
        self.result_label.setText(
            "Resultado ainda não calculado."
        )
        self.continue_button.setEnabled(False)
        self.recalculate_button.setEnabled(False)
        self.add_batch_button.setEnabled(False)

    def set_error(
        self,
        message: str,
    ) -> None:
        self.progress_label.setText(
            f"Não foi possível reconhecer:\n{message}"
        )
        self._calculation_in_progress = False
        self.result_label.setText(
            "Resultado inválido."
        )
        self.continue_button.setEnabled(False)
        self.select_button.setEnabled(True)
        self.select_button.setText(
            "Selecionar novamente"
        )

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

    def seed_count(self) -> int:
        return int(
            self.seed_count_spin.value()
        )

    def preset_values(self) -> dict[str, object]:
        return {
            "region_radius": self.region_radius(),
            "maximum_neighbor_angle": (
                self.maximum_neighbor_angle()
            ),
            "minimum_points": self.minimum_points(),
            "seed_count": self.seed_count(),
            "auto_recalculate": (
                self.auto_recalculate_checkbox.isChecked()
            ),
            "production_mode": (
                self.production_mode_checkbox.isChecked()
            ),
            "multi_recognition": (
                self.multi_recognition_checkbox.isChecked()
            ),
        }

    def multi_recognition_enabled(self) -> bool:
        return (
            self.multi_recognition_checkbox.isChecked()
        )

    def add_batch_result(
        self,
        *,
        index: int,
        diameter: float,
        quality_grade: str,
        quality_score: float,
    ) -> None:
        self.batch_list.addItem(
            (
                f"{index:02d} | Ø {diameter:.4f} mm | "
                f"{quality_grade} {quality_score:.1f}%"
            )
        )
        self.batch_label.setText(
            f"Lote de cilindros: {self.batch_list.count()}"
        )
        self.create_batch_button.setEnabled(
            self.batch_list.count() > 0
        )
        self.add_batch_button.setEnabled(False)
        self.clear_result()

    def clear_batch_results(self) -> None:
        self.batch_list.clear()
        self.batch_label.setText(
            "Lote de cilindros: 0"
        )
        self.create_batch_button.setEnabled(False)

    def production_mode_enabled(self) -> bool:
        return (
            self.production_mode_checkbox.isChecked()
        )
