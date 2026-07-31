from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Any

from PySide6.QtCore import QPoint
from vtkmodules.vtkRenderingCore import vtkCellPicker


@dataclass(frozen=True)
class ContextPickResult:
    """Resultado de um picking na viewport."""

    object_id: str
    actor: Any
    point: tuple[float, float, float]
    display_distance: float


class ContextPicker:
    """
    Executa picking preciso e rápido sobre objetos da cena.

    Estratégia:
    1. Testa exatamente o ponto clicado.
    2. Se não encontrar nada, testa somente oito pixels próximos.
    3. Interrompe assim que encontra um resultado válido.
    """

    def __init__(
        self,
        viewer: Any,
        scene: Any,
    ) -> None:
        self.viewer = viewer
        self.scene = scene

        self._picker = vtkCellPicker()

        # Uma tolerância um pouco maior reduz a necessidade
        # de executar muitas tentativas ao redor do cursor.
        self._picker.SetTolerance(0.003)
        self._picker.PickFromListOn()

        # Centro + oito posições próximas.
        # O centro sempre é testado primeiro.
        self._search_offsets = (
            (0, 0),
            (-2, 0),
            (2, 0),
            (0, -2),
            (0, 2),
            (-2, -2),
            (-2, 2),
            (2, -2),
            (2, 2),
        )

    def pick(
        self,
        qt_position: QPoint,
    ) -> ContextPickResult | None:
        """Identifica o objeto e o ponto 3D sob o cursor."""

        display_position = self._qt_to_vtk_display(
            qt_position
        )

        if display_position is None:
            return None

        center_x, center_y = display_position

        self._prepare_pick_list()

        if self._picker.GetPickList().GetNumberOfItems() == 0:
            return None

        for offset_x, offset_y in self._search_offsets:
            pick_x = center_x + offset_x
            pick_y = center_y + offset_y

            result = self._pick_display_position(
                pick_x=pick_x,
                pick_y=pick_y,
                center_x=center_x,
                center_y=center_y,
            )

            if result is not None:
                return result

        return None

    def _prepare_pick_list(self) -> None:
        """Atualiza a lista dos atores que podem ser escolhidos."""

        self._picker.InitializePickList()

        for object_id in self.scene.object_ids():
            scene_object = self.scene.get_object(
                object_id
            )

            if scene_object is None:
                continue

            if not scene_object.visible:
                continue

            try:
                self._picker.AddPickList(
                    scene_object.actor
                )
            except (TypeError, AttributeError):
                continue

    def _pick_display_position(
        self,
        pick_x: int,
        pick_y: int,
        center_x: int,
        center_y: int,
    ) -> ContextPickResult | None:
        """Executa uma tentativa em coordenadas VTK."""

        renderer = self.viewer.renderer

        was_picked = self._picker.Pick(
            float(pick_x),
            float(pick_y),
            0.0,
            renderer,
        )

        if not was_picked:
            return None

        actor = self._picker.GetActor()

        if actor is None:
            return None

        scene_object = self.scene.get_object_by_actor(
            actor
        )

        if scene_object is None:
            return None

        picked_position = self._picker.GetPickPosition()

        point = (
            float(picked_position[0]),
            float(picked_position[1]),
            float(picked_position[2]),
        )

        if not self._point_is_valid(point):
            return None

        display_distance = sqrt(
            float((pick_x - center_x) ** 2)
            + float((pick_y - center_y) ** 2)
        )

        return ContextPickResult(
            object_id=scene_object.object_id,
            actor=actor,
            point=point,
            display_distance=display_distance,
        )

    def _qt_to_vtk_display(
        self,
        qt_position: QPoint,
    ) -> tuple[int, int] | None:
        """
        Converte coordenadas Qt para coordenadas VTK.

        Considera diferenças de DPI e escala do Windows.
        """

        context_widget = self.viewer.interactor

        widget_width = context_widget.width()
        widget_height = context_widget.height()

        if widget_width <= 0 or widget_height <= 0:
            return None

        render_window = self.viewer.GetRenderWindow()
        render_size = render_window.GetSize()

        if render_size is None or len(render_size) != 2:
            return None

        render_width = int(render_size[0])
        render_height = int(render_size[1])

        if render_width <= 0 or render_height <= 0:
            return None

        scale_x = render_width / float(widget_width)
        scale_y = render_height / float(widget_height)

        vtk_x = round(
            float(qt_position.x()) * scale_x
        )

        qt_scaled_y = round(
            float(qt_position.y()) * scale_y
        )

        # Qt: origem no canto superior esquerdo.
        # VTK: origem no canto inferior esquerdo.
        vtk_y = render_height - qt_scaled_y - 1

        vtk_x = max(
            0,
            min(vtk_x, render_width - 1),
        )

        vtk_y = max(
            0,
            min(vtk_y, render_height - 1),
        )

        return vtk_x, vtk_y

    def _point_is_valid(
        self,
        point: tuple[float, float, float],
    ) -> bool:
        """Confirma que as coordenadas são numéricas e finitas."""

        return all(
            isfinite(coordinate)
            for coordinate in point
        )