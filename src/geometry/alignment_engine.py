from __future__ import annotations

from math import pi
from typing import Iterable

import numpy as np


def normalized(
    vector: Iterable[float],
) -> np.ndarray:
    result = np.asarray(
        tuple(vector),
        dtype=float,
    )

    if result.shape != (3,):
        raise ValueError(
            "O vetor deve possuir três componentes."
        )

    length = float(
        np.linalg.norm(result)
    )

    if length <= 1.0e-12:
        raise ValueError(
            "Não é possível alinhar um vetor nulo."
        )

    return result / length


def rotation_matrix_from_vectors(
    source: Iterable[float],
    target: Iterable[float],
) -> np.ndarray:
    """
    Calcula uma rotação 3 × 3 que leva source até target.

    Trata também os casos paralelo e antiparalelo.
    """

    source_vector = normalized(source)
    target_vector = normalized(target)

    cross_product = np.cross(
        source_vector,
        target_vector,
    )
    sine = float(
        np.linalg.norm(cross_product)
    )
    cosine = float(
        np.dot(
            source_vector,
            target_vector,
        )
    )

    if sine <= 1.0e-12:
        if cosine > 0.0:
            return np.eye(3)

        helper = (
            np.array([1.0, 0.0, 0.0])
            if abs(source_vector[0]) < 0.9
            else np.array([0.0, 1.0, 0.0])
        )
        axis = np.cross(
            source_vector,
            helper,
        )
        axis = axis / np.linalg.norm(axis)

        # Rotação de 180°: R = 2 aaᵀ - I.
        return (
            2.0
            * np.outer(axis, axis)
            - np.eye(3)
        )

    skew = np.array(
        [
            [
                0.0,
                -cross_product[2],
                cross_product[1],
            ],
            [
                cross_product[2],
                0.0,
                -cross_product[0],
            ],
            [
                -cross_product[1],
                cross_product[0],
                0.0,
            ],
        ],
        dtype=float,
    )

    return (
        np.eye(3)
        + skew
        + skew @ skew
        * ((1.0 - cosine) / (sine * sine))
    )


def pivot_rotation_transform(
    *,
    source_direction: Iterable[float],
    target_direction: Iterable[float],
    pivot: Iterable[float],
) -> np.ndarray:
    """
    Cria matriz homogênea 4 × 4 para girar em torno do pivot.
    """

    rotation = rotation_matrix_from_vectors(
        source_direction,
        target_direction,
    )
    pivot_array = np.asarray(
        tuple(pivot),
        dtype=float,
    )

    if pivot_array.shape != (3,):
        raise ValueError(
            "O ponto de giro deve possuir três coordenadas."
        )

    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = (
        pivot_array
        - rotation @ pivot_array
    )

    return transform


def target_axis(
    axis_name: str,
) -> tuple[float, float, float]:
    definitions = {
        "x": (1.0, 0.0, 0.0),
        "y": (0.0, 1.0, 0.0),
        "z": (0.0, 0.0, 1.0),
        "x-": (-1.0, 0.0, 0.0),
        "y-": (0.0, -1.0, 0.0),
        "z-": (0.0, 0.0, -1.0),
    }

    if axis_name not in definitions:
        raise ValueError(
            f"Eixo global desconhecido: {axis_name}"
        )

    return definitions[axis_name]



def plane_to_global_transform(
    *,
    plane_origin: Iterable[float],
    plane_normal: Iterable[float],
    target_normal: Iterable[float],
    seat_on_global_plane: bool = True,
) -> np.ndarray:
    """
    Orienta um plano para uma normal global e, opcionalmente,
    assenta sua origem no plano global correspondente.

    Exemplo:
    target_normal Z+ → plano global XY em Z = 0.
    """

    origin = np.asarray(
        tuple(plane_origin),
        dtype=float,
    )

    if origin.shape != (3,):
        raise ValueError(
            "A origem do plano deve possuir três coordenadas."
        )

    target = normalized(target_normal)

    rotation_transform = pivot_rotation_transform(
        source_direction=plane_normal,
        target_direction=target,
        pivot=origin,
    )

    if not seat_on_global_plane:
        return rotation_transform

    # Como a rotação acontece em torno da origem do plano, ela
    # permanece no mesmo ponto. Removemos apenas sua componente
    # ao longo da normal global escolhida.
    signed_distance = float(
        np.dot(origin, target)
    )
    translation = -signed_distance * target

    translation_transform = np.eye(4)
    translation_transform[:3, 3] = translation

    return translation_transform @ rotation_transform
