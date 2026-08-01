from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

import numpy as np


@dataclass(frozen=True)
class CylinderQualityResult:
    """Indicadores explicáveis da qualidade do ajuste."""

    score: float
    grade: str
    stars: int
    circularity: float
    mean_absolute_error: float
    standard_deviation: float
    relative_rms_percent: float
    inlier_ratio: float
    evaluated_point_count: int
    reasons: tuple[str, ...]


def _normalized(
    vector: Any,
) -> np.ndarray:
    result = np.asarray(
        vector,
        dtype=float,
    )
    length = float(
        np.linalg.norm(result)
    )

    if length <= 1.0e-12:
        raise ValueError(
            "A direção do cilindro não pode ser nula."
        )

    return result / length


def cylinder_radial_residuals(
    *,
    points: Any,
    center: Any,
    axis_direction: Any,
    radius: float,
) -> np.ndarray:
    """Calcula o erro radial assinado de cada ponto."""

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

    axis = _normalized(
        axis_direction
    )
    center_array = np.asarray(
        center,
        dtype=float,
    )
    relative = (
        point_array - center_array
    )
    axial = (
        relative @ axis
    )[:, None] * axis[None, :]
    radial_vectors = relative - axial
    radial_distances = np.linalg.norm(
        radial_vectors,
        axis=1,
    )

    return radial_distances - float(
        radius
    )


def evaluate_cylinder_quality(
    *,
    points: Any,
    center: Any,
    axis_direction: Any,
    radius: float,
    rms_error: float,
    maximum_error: float,
    coverage_angle: float,
    radial_tolerance: float,
) -> CylinderQualityResult:
    """
    Combina precisão, cobertura e consistência dos pontos.

    A pontuação é orientativa e explicável. Não substitui
    certificação metrológica nem tolerâncias do desenho.
    """

    residuals = cylinder_radial_residuals(
        points=points,
        center=center,
        axis_direction=axis_direction,
        radius=radius,
    )

    if residuals.size == 0:
        raise ValueError(
            "Não há pontos para avaliar a qualidade."
        )

    absolute = np.abs(
        residuals
    )
    mean_absolute_error = float(
        np.mean(absolute)
    )
    standard_deviation = float(
        np.std(residuals)
    )
    circularity = float(
        np.max(residuals)
        - np.min(residuals)
    )

    safe_radius = max(
        float(radius),
        1.0e-9,
    )
    relative_rms = (
        float(rms_error)
        / safe_radius
    )
    relative_rms_percent = (
        relative_rms * 100.0
    )

    tolerance = max(
        float(radial_tolerance),
        1.0e-9,
    )
    inlier_ratio = float(
        np.count_nonzero(
            absolute <= tolerance
        )
        / residuals.size
    )

    # Erro relativo: nota máxima até cerca de 0,25% do raio,
    # caindo progressivamente até 5%.
    error_score = max(
        0.0,
        min(
            1.0,
            1.0
            - max(
                0.0,
                relative_rms - 0.0025,
            )
            / 0.0475,
        ),
    )

    coverage_score = max(
        0.0,
        min(
            1.0,
            float(coverage_angle)
            / 300.0,
        ),
    )

    inlier_score = max(
        0.0,
        min(
            1.0,
            (
                inlier_ratio - 0.70
            )
            / 0.30,
        ),
    )

    point_score = max(
        0.0,
        min(
            1.0,
            residuals.size / 800.0,
        ),
    )

    maximum_score = max(
        0.0,
        min(
            1.0,
            1.0
            - float(maximum_error)
            / max(
                safe_radius * 0.08,
                tolerance * 3.0,
                1.0e-9,
            ),
        ),
    )

    score = 100.0 * (
        0.38 * error_score
        + 0.24 * coverage_score
        + 0.18 * inlier_score
        + 0.10 * point_score
        + 0.10 * maximum_score
    )
    score = max(
        0.0,
        min(100.0, score),
    )

    if score >= 92.0:
        grade = "Excelente"
        stars = 5
    elif score >= 80.0:
        grade = "Muito boa"
        stars = 4
    elif score >= 65.0:
        grade = "Boa"
        stars = 3
    elif score >= 45.0:
        grade = "Baixa"
        stars = 2
    else:
        grade = "Crítica"
        stars = 1

    reasons: list[str] = []

    if coverage_angle >= 300.0:
        reasons.append(
            "Cobertura angular ampla."
        )
    elif coverage_angle >= 180.0:
        reasons.append(
            "Cobertura angular parcial, porém utilizável."
        )
    else:
        reasons.append(
            "Cobertura angular limitada; confirme o eixo visualmente."
        )

    if relative_rms_percent <= 0.5:
        reasons.append(
            "Erro RMS muito pequeno em relação ao raio."
        )
    elif relative_rms_percent <= 2.0:
        reasons.append(
            "Erro RMS compatível com uma malha moderadamente ruidosa."
        )
    else:
        reasons.append(
            "Erro RMS elevado em relação ao tamanho do cilindro."
        )

    if inlier_ratio >= 0.95:
        reasons.append(
            "Quase todos os pontos são consistentes com o cilindro."
        )
    elif inlier_ratio >= 0.85:
        reasons.append(
            "A maioria dos pontos é consistente com o ajuste."
        )
    else:
        reasons.append(
            "Há uma quantidade relevante de pontos divergentes."
        )

    if residuals.size < 100:
        reasons.append(
            "Poucos pontos avaliados; considere ampliar a região."
        )

    return CylinderQualityResult(
        score=float(score),
        grade=grade,
        stars=stars,
        circularity=circularity,
        mean_absolute_error=(
            mean_absolute_error
        ),
        standard_deviation=(
            standard_deviation
        ),
        relative_rms_percent=(
            relative_rms_percent
        ),
        inlier_ratio=inlier_ratio,
        evaluated_point_count=int(
            residuals.size
        ),
        reasons=tuple(reasons),
    )
