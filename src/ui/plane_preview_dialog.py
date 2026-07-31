from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class PlanePreviewDialog(QDialog):
    """Confirma a região e o plano reconhecido."""

    def __init__(
        self,
        *,
        triangle_count: int,
        point_count: int,
        rms_error: float,
        maximum_error: float,
        normal: tuple[float, float, float],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(
            "Pré-visualização do plano"
        )
        self.setModal(True)
        self.resize(430, 280)

        explanation = QLabel(
            (
                "A região amarela representa exatamente os "
                "triângulos usados no cálculo.\n"
                "O retângulo azul é a prévia do plano."
            )
        )
        explanation.setWordWrap(True)

        statistics = QLabel(
            (
                f"Triângulos selecionados: {triangle_count}\n"
                f"Pontos únicos: {point_count}\n"
                f"Erro RMS: {rms_error:.4f} mm\n"
                f"Erro máximo: {maximum_error:.4f} mm\n"
                f"Normal: "
                f"({normal[0]:.4f}, "
                f"{normal[1]:.4f}, "
                f"{normal[2]:.4f})"
            )
        )
        statistics.setTextInteractionFlags(
            statistics.textInteractionFlags()
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        ok_button = buttons.button(
            QDialogButtonBox.StandardButton.Ok
        )
        ok_button.setText("Criar plano")

        cancel_button = buttons.button(
            QDialogButtonBox.StandardButton.Cancel
        )
        cancel_button.setText("Cancelar")

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(explanation)
        layout.addSpacing(10)
        layout.addWidget(statistics)
        layout.addStretch()
        layout.addWidget(buttons)
