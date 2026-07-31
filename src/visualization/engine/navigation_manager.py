from __future__ import annotations

from math import sqrt
from typing import Any

import pyvista as pv


class NavigationManager:
    """Gerencia câmera, projeções, vistas e centro de rotação."""

    PIVOT_ACTOR_NAME = "__genesis_rotation_pivot__"
    PIVOT_COLOR = "#ff9f1c"

    def __init__(
        self,
        viewer: Any,
    ) -> None:
        self.viewer = viewer

        self.pivot_point: tuple[
            float,
            float,
            float,
        ] | None = None

        self.axes_visible = True

    def set_rotation_center(
        self,
        point: tuple[float, float, float],
        show_marker: bool = True,
    ) -> None:
        """Define um ponto tridimensional como centro de órbita."""

        self.pivot_point = (
            float(point[0]),
            float(point[1]),
            float(point[2]),
        )

        self.viewer.camera.focal_point = self.pivot_point

        if show_marker:
            self._show_pivot_marker(self.pivot_point)

        self._reset_clipping_range()
        self.viewer.render()

    def restore_global_center(self) -> bool:
        """Restaura o centro de rotação para o centro da cena."""

        bounds = self._scene_bounds()

        if bounds is None:
            self.pivot_point = None
            self.remove_pivot_marker()
            return False

        center = self._bounds_center(bounds)

        self.pivot_point = center
        self.viewer.camera.focal_point = center

        self.remove_pivot_marker(render=False)
        self._reset_clipping_range()
        self.viewer.render()

        return True

    def set_standard_view(
        self,
        view_name: str,
    ) -> bool:
        """Posiciona a câmera em uma vista técnica padronizada."""

        bounds = self._scene_bounds()

        if bounds is None:
            return False

        center = self._bounds_center(bounds)
        distance = self._camera_distance(bounds)

        view_definitions = {
            # Olha de Y- para Y+.
            "front": (
                (0.0, -1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),

            # Olha de Y+ para Y-.
            "back": (
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),

            # Olha de Z+ para Z-.
            "top": (
                (0.0, 0.0, 1.0),
                (0.0, 1.0, 0.0),
            ),

            # Olha de Z- para Z+.
            "bottom": (
                (0.0, 0.0, -1.0),
                (0.0, 1.0, 0.0),
            ),

            # Olha de X- para X+.
            "left": (
                (-1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0),
            ),

            # Olha de X+ para X-.
            "right": (
                (1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0),
            ),

            # Vista isométrica superior frontal direita.
            "isometric": (
                (1.0, -1.0, 1.0),
                (0.0, 0.0, 1.0),
            ),
        }

        definition = view_definitions.get(view_name)

        if definition is None:
            return False

        direction, view_up = definition

        direction_length = sqrt(
            direction[0] ** 2
            + direction[1] ** 2
            + direction[2] ** 2
        )

        normalized_direction = (
            direction[0] / direction_length,
            direction[1] / direction_length,
            direction[2] / direction_length,
        )

        camera_position = (
            center[0] + normalized_direction[0] * distance,
            center[1] + normalized_direction[1] * distance,
            center[2] + normalized_direction[2] * distance,
        )

        camera = self.viewer.camera

        camera.position = camera_position
        camera.focal_point = center
        camera.up = view_up

        self.pivot_point = center

        self.remove_pivot_marker(render=False)
        self._reset_clipping_range()
        self.viewer.render()

        return True

    def rotate_view_90(
        self,
        clockwise: bool,
    ) -> None:
        """
        Gira a orientação da vista em 90 graus.

        Apenas a câmera é girada. A geometria não é alterada.
        """

        angle = -90.0 if clockwise else 90.0

        camera = self.viewer.camera

        try:
            camera.Roll(angle)
        except AttributeError:
            current_roll = float(
                getattr(camera, "roll", 0.0)
            )
            camera.roll = current_roll + angle

        self._reset_clipping_range()
        self.viewer.render()

    def set_axes_visible(
        self,
        visible: bool,
    ) -> None:
        """Mostra ou oculta o indicador de eixos."""

        self.axes_visible = visible

        if visible:
            self.viewer.show_axes()
        else:
            self.viewer.hide_axes()

        self.viewer.render()

    def set_parallel_projection(
        self,
        enabled: bool,
    ) -> None:
        """Alterna entre projeção ortográfica e perspectiva."""

        if enabled:
            self.viewer.enable_parallel_projection()
        else:
            self.viewer.disable_parallel_projection()

        self.viewer.render()

    def remove_pivot_marker(
        self,
        render: bool = True,
    ) -> None:
        """Remove o marcador visual do centro de rotação."""

        try:
            self.viewer.remove_actor(
                self.PIVOT_ACTOR_NAME,
                render=False,
            )
        except Exception:
            pass

        if render:
            self.viewer.render()

    def _show_pivot_marker(
        self,
        point: tuple[float, float, float],
    ) -> None:
        """Mostra uma esfera no centro de rotação."""

        self.remove_pivot_marker(render=False)

        marker = pv.Sphere(
            radius=self._marker_radius(),
            center=point,
            theta_resolution=24,
            phi_resolution=24,
        )

        self.viewer.add_mesh(
            marker,
            name=self.PIVOT_ACTOR_NAME,
            color=self.PIVOT_COLOR,
            lighting=False,
            ambient=1.0,
            pickable=False,
        )

    def _marker_radius(self) -> float:
        """Calcula um tamanho proporcional para o marcador."""

        bounds = self._scene_bounds()

        if bounds is None:
            return 1.0

        size_x = bounds[1] - bounds[0]
        size_y = bounds[3] - bounds[2]
        size_z = bounds[5] - bounds[4]

        diagonal = sqrt(
            size_x * size_x
            + size_y * size_y
            + size_z * size_z
        )

        if diagonal <= 0.0:
            return 1.0

        return max(
            diagonal * 0.008,
            0.25,
        )

    def _camera_distance(
        self,
        bounds: tuple[
            float,
            float,
            float,
            float,
            float,
            float,
        ],
    ) -> float:
        """Calcula uma distância segura entre câmera e cena."""

        size_x = bounds[1] - bounds[0]
        size_y = bounds[3] - bounds[2]
        size_z = bounds[5] - bounds[4]

        diagonal = sqrt(
            size_x * size_x
            + size_y * size_y
            + size_z * size_z
        )

        return max(
            diagonal * 1.8,
            10.0,
        )

    def _reset_clipping_range(self) -> None:
        """Atualiza os planos próximo e distante da câmera."""

        try:
            self.viewer.renderer.ResetCameraClippingRange()
        except Exception:
            try:
                self.viewer.camera.reset_clipping_range()
            except Exception:
                pass

    def _scene_bounds(
        self,
    ) -> tuple[
        float,
        float,
        float,
        float,
        float,
        float,
    ] | None:
        """Obtém limites válidos da cena."""

        try:
            values = tuple(
                float(value)
                for value in self.viewer.bounds
            )
        except Exception:
            return None

        if len(values) != 6:
            return None

        if not all(value == value for value in values):
            return None

        return (
            values[0],
            values[1],
            values[2],
            values[3],
            values[4],
            values[5],
        )

    def _bounds_center(
        self,
        bounds: tuple[
            float,
            float,
            float,
            float,
            float,
            float,
        ],
    ) -> tuple[float, float, float]:
        """Retorna o centro geométrico dos limites."""

        return (
            (bounds[0] + bounds[1]) / 2.0,
            (bounds[2] + bounds[3]) / 2.0,
            (bounds[4] + bounds[5]) / 2.0,
        )