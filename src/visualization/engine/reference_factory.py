from __future__ import annotations

from math import sqrt
from typing import Any

import pyvista as pv

from geometry.reference_entities import (
    AxisReference,
    CylinderReference,
    PlaneReference,
    PointReference,
    Vector3,
    normalize_vector,
)


class ReferenceGeometryFactory:
    """
    Converte entidades matemáticas em geometrias PyVista.

    As entidades originais permanecem precisas e independentes
    da representação usada na viewport.
    """

    @staticmethod
    def create_point(
        reference: PointReference,
        radius: float = 1.5,
    ) -> Any:
        """Cria a representação gráfica de um ponto."""

        if radius <= 0.0:
            raise ValueError(
                "O raio visual do ponto deve ser positivo."
            )

        return pv.Sphere(
            center=reference.position,
            radius=radius,
            theta_resolution=20,
            phi_resolution=20,
        )

    @staticmethod
    def create_axis(
        reference: AxisReference,
        shaft_radius: float | None = None,
    ) -> Any:
        """
        Cria a representação gráfica de um eixo.

        A origem fornecida fica no centro visual do eixo.
        """

        direction = reference.direction
        length = reference.display_length

        start = (
            reference.origin[0]
            - direction[0] * length / 2.0,
            reference.origin[1]
            - direction[1] * length / 2.0,
            reference.origin[2]
            - direction[2] * length / 2.0,
        )

        radius = (
            shaft_radius
            if shaft_radius is not None
            else max(length * 0.006, 0.15)
        )

        tip_length = min(
            length * 0.12,
            radius * 12.0,
        )

        shaft_length = max(
            length - tip_length,
            length * 0.50,
        )

        return pv.Arrow(
            start=start,
            direction=direction,
            scale=length,
            shaft_radius=max(
                radius / max(length, 1.0),
                0.002,
            ),
            tip_radius=max(
                radius * 2.5 / max(length, 1.0),
                0.006,
            ),
            tip_length=min(
                tip_length / max(length, 1.0),
                0.30,
            ),
        )

    @staticmethod
    def create_plane(
        reference: PlaneReference,
    ) -> Any:
        """Cria a representação retangular de um plano."""

        direction_1, direction_2 = (
            ReferenceGeometryFactory._plane_directions(
                reference.normal
            )
        )

        return pv.Plane(
            center=reference.origin,
            direction=reference.normal,
            i_size=reference.size_x,
            j_size=reference.size_y,
            i_resolution=1,
            j_resolution=1,
        )

    @staticmethod
    def create_cylinder(
        reference: CylinderReference,
        resolution: int = 96,
    ) -> Any:
        """Cria a representação visual de um cilindro."""

        return pv.Cylinder(
            center=reference.center,
            direction=reference.axis_direction,
            radius=reference.radius,
            height=reference.length,
            resolution=max(
                24,
                int(resolution),
            ),
            capping=False,
        )

    @staticmethod
    def _plane_directions(
        normal: Vector3,
    ) -> tuple[Vector3, Vector3]:
        """
        Calcula duas direções ortogonais pertencentes ao plano.

        Essa função também será reutilizada futuramente para
        esboços e sistemas de coordenadas locais.
        """

        normal = normalize_vector(normal)

        if abs(normal[2]) < 0.90:
            helper = (0.0, 0.0, 1.0)
        else:
            helper = (0.0, 1.0, 0.0)

        direction_1 = (
            normal[1] * helper[2]
            - normal[2] * helper[1],
            normal[2] * helper[0]
            - normal[0] * helper[2],
            normal[0] * helper[1]
            - normal[1] * helper[0],
        )

        direction_1 = normalize_vector(
            direction_1
        )

        direction_2 = (
            normal[1] * direction_1[2]
            - normal[2] * direction_1[1],
            normal[2] * direction_1[0]
            - normal[0] * direction_1[2],
            normal[0] * direction_1[1]
            - normal[1] * direction_1[0],
        )

        direction_2 = normalize_vector(
            direction_2
        )

        return direction_1, direction_2

    @staticmethod
    def scene_diagonal(
        bounds: tuple[
            float,
            float,
            float,
            float,
            float,
            float,
        ],
    ) -> float:
        """Calcula a diagonal dos limites de uma cena."""

        size_x = bounds[1] - bounds[0]
        size_y = bounds[3] - bounds[2]
        size_z = bounds[5] - bounds[4]

        return sqrt(
            size_x * size_x
            + size_y * size_y
            + size_z * size_z
        )