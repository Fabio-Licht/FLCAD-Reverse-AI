from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class PatternInstance:
    """Transformação calculada para uma instância de padrão."""

    index: int
    center: tuple[float, float, float]
    direction: tuple[float, float, float]
    parameter: float
    is_master: bool


def normalized(
    vector: Iterable[float],
) -> np.ndarray:
    result = np.asarray(
        tuple(vector),
        dtype=float,
    )

    if result.shape != (3,):
        raise ValueError(
            "O vetor deve possuir exatamente três componentes."
        )

    length = float(
        np.linalg.norm(result)
    )

    if length <= 1.0e-12:
        raise ValueError(
            "O vetor do padrão não pode ser nulo."
        )

    return result / length


def rotate_vector_about_axis(
    vector: Iterable[float],
    axis: Iterable[float],
    angle_degrees: float,
) -> np.ndarray:
    """Rotaciona um vetor pela fórmula de Rodrigues."""

    vector_array = np.asarray(
        tuple(vector),
        dtype=float,
    )
    axis_array = normalized(axis)
    angle = radians(
        float(angle_degrees)
    )

    return (
        vector_array * cos(angle)
        + np.cross(
            axis_array,
            vector_array,
        ) * sin(angle)
        + axis_array
        * float(
            np.dot(
                axis_array,
                vector_array,
            )
        )
        * (1.0 - cos(angle))
    )


def create_linear_pattern(
    *,
    master_center: Iterable[float],
    master_direction: Iterable[float],
    translation_direction: Iterable[float],
    spacing: float,
    quantity: int,
) -> list[PatternInstance]:
    """
    Cria instâncias igualmente espaçadas em uma direção.

    A quantidade inclui a entidade mestre.
    """

    if quantity < 1:
        raise ValueError(
            "A quantidade deve ser pelo menos 1."
        )

    if spacing < 0.0:
        raise ValueError(
            "O espaçamento não pode ser negativo."
        )

    center = np.asarray(
        tuple(master_center),
        dtype=float,
    )
    direction = normalized(
        master_direction
    )
    translation = normalized(
        translation_direction
    )

    instances: list[PatternInstance] = []

    for index in range(quantity):
        distance = float(index) * float(
            spacing
        )
        instance_center = (
            center
            + translation * distance
        )

        instances.append(
            PatternInstance(
                index=index,
                center=tuple(
                    float(value)
                    for value in instance_center
                ),
                direction=tuple(
                    float(value)
                    for value in direction
                ),
                parameter=distance,
                is_master=index == 0,
            )
        )

    return instances


def create_circular_pattern(
    *,
    master_center: Iterable[float],
    master_direction: Iterable[float],
    axis_origin: Iterable[float],
    axis_direction: Iterable[float],
    angle_step_degrees: float,
    quantity: int,
    rotate_orientation: bool,
) -> list[PatternInstance]:
    """
    Cria instâncias rotacionadas em torno de um eixo central.

    A quantidade inclui a entidade mestre. Quando
    ``rotate_orientation`` for verdadeiro, o eixo próprio do
    cilindro também acompanha a rotação do padrão.
    """

    if quantity < 1:
        raise ValueError(
            "A quantidade deve ser pelo menos 1."
        )

    center = np.asarray(
        tuple(master_center),
        dtype=float,
    )
    direction = normalized(
        master_direction
    )
    origin = np.asarray(
        tuple(axis_origin),
        dtype=float,
    )
    axis = normalized(
        axis_direction
    )

    relative_center = (
        center - origin
    )

    instances: list[PatternInstance] = []

    for index in range(quantity):
        angle = (
            float(index)
            * float(angle_step_degrees)
        )

        rotated_center = (
            origin
            + rotate_vector_about_axis(
                relative_center,
                axis,
                angle,
            )
        )

        if rotate_orientation:
            rotated_direction = normalized(
                rotate_vector_about_axis(
                    direction,
                    axis,
                    angle,
                )
            )
        else:
            rotated_direction = direction

        instances.append(
            PatternInstance(
                index=index,
                center=tuple(
                    float(value)
                    for value in rotated_center
                ),
                direction=tuple(
                    float(value)
                    for value in rotated_direction
                ),
                parameter=angle,
                is_master=index == 0,
            )
        )

    return instances
