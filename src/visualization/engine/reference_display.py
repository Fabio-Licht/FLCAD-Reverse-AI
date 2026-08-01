from __future__ import annotations

from math import cos, pi, sin
from typing import Any

import numpy as np
import pyvista as pv


def _normalized(
    direction: tuple[float, float, float],
) -> np.ndarray:
    vector = np.asarray(
        direction,
        dtype=float,
    )
    length = float(
        np.linalg.norm(vector)
    )

    if length <= 1.0e-12:
        raise ValueError(
            "A direção do cilindro não pode ser nula."
        )

    return vector / length


def _basis_from_axis(
    axis: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    helper = (
        np.array([0.0, 0.0, 1.0])
        if abs(float(axis[2])) < 0.90
        else np.array([0.0, 1.0, 0.0])
    )

    first = np.cross(
        axis,
        helper,
    )
    first = first / np.linalg.norm(first)

    second = np.cross(
        axis,
        first,
    )
    second = second / np.linalg.norm(second)

    return first, second


def create_cylinder_reference_lines(
    cylinder: Any,
    *,
    circle_resolution: int = 96,
    generator_count: int = 8,
) -> pv.PolyData:
    """
    Cria a representação técnica de um cilindro.

    A entidade é mostrada por:
    - duas circunferências;
    - geratrizes longitudinais;
    - sem preenchimento de superfície.

    Essa representação deixa a malha visível e torna a
    referência mais leve para alinhamento e inspeção.
    """

    center = np.asarray(
        cylinder.center,
        dtype=float,
    )
    axis = _normalized(
        cylinder.axis_direction
    )
    radius = float(cylinder.radius)
    length = float(cylinder.length)

    if radius <= 0.0 or length <= 0.0:
        raise ValueError(
            "Raio e comprimento devem ser positivos."
        )

    basis_u, basis_v = _basis_from_axis(
        axis
    )

    half_length = length / 2.0
    first_center = (
        center - axis * half_length
    )
    second_center = (
        center + axis * half_length
    )

    points: list[
        tuple[float, float, float]
    ] = []
    lines: list[int] = []

    def add_polyline(
        polyline_points: list[np.ndarray],
        *,
        closed: bool = False,
    ) -> None:
        start_index = len(points)

        for point in polyline_points:
            points.append(
                (
                    float(point[0]),
                    float(point[1]),
                    float(point[2]),
                )
            )

        point_ids = list(
            range(
                start_index,
                start_index
                + len(polyline_points),
            )
        )

        if closed:
            point_ids.append(
                point_ids[0]
            )

        lines.extend(
            [len(point_ids), *point_ids]
        )

    angles = [
        2.0 * pi * index
        / circle_resolution
        for index in range(
            circle_resolution
        )
    ]

    first_circle = [
        first_center
        + radius
        * (
            cos(angle) * basis_u
            + sin(angle) * basis_v
        )
        for angle in angles
    ]
    second_circle = [
        second_center
        + radius
        * (
            cos(angle) * basis_u
            + sin(angle) * basis_v
        )
        for angle in angles
    ]

    add_polyline(
        first_circle,
        closed=True,
    )
    add_polyline(
        second_circle,
        closed=True,
    )

    for index in range(
        max(4, generator_count)
    ):
        angle = (
            2.0
            * pi
            * index
            / max(4, generator_count)
        )
        radial = radius * (
            cos(angle) * basis_u
            + sin(angle) * basis_v
        )

        add_polyline(
            [
                first_center + radial,
                second_center + radial,
            ]
        )

    geometry = pv.PolyData(
        np.asarray(
            points,
            dtype=float,
        )
    )
    geometry.lines = np.asarray(
        lines,
        dtype=np.int64,
    )

    return geometry
