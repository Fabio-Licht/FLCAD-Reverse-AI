from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import (
    QVTKRenderWindowInteractor,
)
from vtkmodules.vtkRenderingCore import vtkRenderer

# Importa os módulos necessários para o funcionamento
# correto do pipeline gráfico do VTK.
import vtkmodules.vtkInteractionStyle  # noqa: F401
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401


class VTKViewport(QWidget):
    """Widget responsável pela área de visualização 3D do Genesis."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._vtk_widget = QVTKRenderWindowInteractor(self)
        self._renderer = vtkRenderer()

        self._configure_layout()
        self._configure_renderer()

    def _configure_layout(self) -> None:
        """Configura o layout que contém a janela VTK."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._vtk_widget)

    def _configure_renderer(self) -> None:
        """Configura o renderizador inicial do Genesis."""

        render_window = self._vtk_widget.GetRenderWindow()
        render_window.AddRenderer(self._renderer)

        # Fundo em degradê escuro.
        self._renderer.SetBackground(0.10, 0.12, 0.16)
        self._renderer.SetBackground2(0.24, 0.28, 0.34)
        self._renderer.GradientBackgroundOn()

    @property
    def renderer(self) -> vtkRenderer:
        """Retorna o renderer para inclusão de objetos na cena."""

        return self._renderer

    def initialize(self) -> None:
        """Inicializa a janela e a interação do VTK."""

        self._vtk_widget.Initialize()
        self._vtk_widget.Start()
        self._vtk_widget.GetRenderWindow().Render()

    def closeEvent(self, event) -> None:
        """Finaliza corretamente os recursos gráficos."""

        self._vtk_widget.Finalize()
        super().closeEvent(event)