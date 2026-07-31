from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

import numpy as np


@dataclass(frozen=True)
class PlaneFitResult:
    """Resultado de um ajuste de plano por mínimos quadrados."""

    origin: tuple[float, float, float]
    normal: tuple[float, float, float]
    rms_error: float
    maximum_error: float
    point_count: int


def fit_plane_to_points(
    points: Any,
) -> PlaneFitResult:
    """Ajusta um plano a um conjunto de pontos tridimensionais."""

    point_array = np.asarray(
        points,
        dtype=float,
    )

    if (
        point_array.ndim != 2
        or point_array.shape[1] != 3
    ):
        raise ValueError(
            "Os pontos devem formar uma matriz N × 3."
        )

    if point_array.shape[0] < 3:
        raise ValueError(
            "São necessários pelo menos três pontos."
        )

    if not np.isfinite(point_array).all():
        raise ValueError(
            "A região contém coordenadas inválidas."
        )

    centroid = point_array.mean(axis=0)
    centered = point_array - centroid

    _, singular_values, vh = np.linalg.svd(
        centered,
        full_matrices=False,
    )

    if singular_values.shape[0] < 3:
        raise ValueError(
            "Não foi possível determinar um plano."
        )

    normal = vh[-1]
    normal_length = float(
        np.linalg.norm(normal)
    )

    if normal_length <= 1.0e-12:
        raise ValueError(
            "A região selecionada não define uma normal válida."
        )

    normal = normal / normal_length

    signed_distances = centered @ normal
    absolute_distances = np.abs(
        signed_distances
    )

    rms_error = sqrt(
        float(
            np.mean(
                signed_distances
                * signed_distances
            )
        )
    )

    maximum_error = float(
        absolute_distances.max()
    )

    return PlaneFitResult(
        origin=(
            float(centroid[0]),
            float(centroid[1]),
            float(centroid[2]),
        ),
        normal=(
            float(normal[0]),
            float(normal[1]),
            float(normal[2]),
        ),
        rms_error=rms_error,
        maximum_error=maximum_error,
        point_count=int(
            point_array.shape[0]
        ),
    )
