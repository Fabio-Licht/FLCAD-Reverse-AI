from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class PlaneQualityResult:
    score: float
    grade: str
    stars: int
    mean_absolute_error: float
    standard_deviation: float
    inlier_ratio: float
    evaluated_point_count: int
    reasons: tuple[str, ...]


def plane_residuals(
    *,
    points: Any,
    origin: Any,
    normal: Any,
) -> np.ndarray:
    point_array = np.asarray(points, dtype=float)
    origin_array = np.asarray(origin, dtype=float)
    normal_array = np.asarray(normal, dtype=float)

    if point_array.ndim != 2 or point_array.shape[1] != 3:
        raise ValueError("Os pontos do plano devem formar uma matriz N × 3.")

    normal_length = float(np.linalg.norm(normal_array))
    if normal_length <= 1.0e-12:
        raise ValueError("A normal do plano não pode ser nula.")

    unit_normal = normal_array / normal_length
    return (point_array - origin_array) @ unit_normal


def evaluate_plane_quality(
    *,
    points: Any,
    origin: Any,
    normal: Any,
    rms_error: float,
    maximum_error: float,
    region_radius: float,
) -> PlaneQualityResult:
    residuals = plane_residuals(
        points=points,
        origin=origin,
        normal=normal,
    )
    if residuals.size == 0:
        raise ValueError("Não existem pontos para avaliar o plano.")

    absolute = np.abs(residuals)
    mean_absolute_error = float(np.mean(absolute))
    standard_deviation = float(np.std(residuals))

    scale = max(float(region_radius), 1.0e-9)
    relative_rms = float(rms_error) / scale
    relative_maximum = float(maximum_error) / scale

    tolerance = max(
        float(rms_error) * 2.5,
        scale * 0.002,
        1.0e-6,
    )
    inlier_ratio = float(
        np.count_nonzero(absolute <= tolerance) / residuals.size
    )

    rms_score = max(
        0.0,
        min(1.0, 1.0 - max(0.0, relative_rms - 0.0005) / 0.0295),
    )
    maximum_score = max(
        0.0,
        min(1.0, 1.0 - relative_maximum / 0.08),
    )
    inlier_score = max(
        0.0,
        min(1.0, (inlier_ratio - 0.70) / 0.30),
    )
    point_score = max(
        0.0,
        min(1.0, residuals.size / 1200.0),
    )

    score = 100.0 * (
        0.45 * rms_score
        + 0.20 * maximum_score
        + 0.25 * inlier_score
        + 0.10 * point_score
    )
    score = max(0.0, min(100.0, score))

    if score >= 92.0:
        grade, stars = "Excelente", 5
    elif score >= 80.0:
        grade, stars = "Muito boa", 4
    elif score >= 65.0:
        grade, stars = "Boa", 3
    elif score >= 45.0:
        grade, stars = "Baixa", 2
    else:
        grade, stars = "Crítica", 1

    reasons: list[str] = []
    if relative_rms <= 0.002:
        reasons.append("RMS pequeno em relação ao tamanho da região.")
    elif relative_rms <= 0.01:
        reasons.append("RMS compatível com uma região moderadamente ruidosa.")
    else:
        reasons.append(
            "RMS elevado; reduza a região ou evite superfícies curvas."
        )

    if inlier_ratio >= 0.95:
        reasons.append(
            "Quase todos os pontos são consistentes com o plano."
        )
    elif inlier_ratio >= 0.85:
        reasons.append("A maioria dos pontos é consistente com o ajuste.")
    else:
        reasons.append("Há muitos pontos divergentes do plano calculado.")

    if residuals.size < 100:
        reasons.append(
            "Poucos pontos avaliados; amplie a região com cuidado."
        )

    return PlaneQualityResult(
        score=float(score),
        grade=grade,
        stars=stars,
        mean_absolute_error=mean_absolute_error,
        standard_deviation=standard_deviation,
        inlier_ratio=inlier_ratio,
        evaluated_point_count=int(residuals.size),
        reasons=tuple(reasons),
    )
