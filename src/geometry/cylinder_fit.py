from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin, sqrt
from typing import Any

import numpy as np


@dataclass(frozen=True)
class CylinderFitResult:
    """Resultado de um ajuste cilíndrico refinado."""

    center: tuple[float, float, float]
    axis_direction: tuple[float, float, float]
    radius: float
    length: float
    rms_error: float
    maximum_error: float
    point_count: int
    coverage_angle: float
    radial_tolerance: float
    axis_score: float


@dataclass(frozen=True)
class _AxisEvaluation:
    axis: np.ndarray
    center: np.ndarray
    radius: float
    length: float
    residuals: np.ndarray
    axial: np.ndarray
    x: np.ndarray
    y: np.ndarray
    score: float


def _normalize(
    vector: np.ndarray,
) -> np.ndarray:
    length = float(np.linalg.norm(vector))

    if length <= 1.0e-12:
        raise ValueError(
            "Foi encontrado um vetor de comprimento zero."
        )

    return vector / length


def _stable_direction(
    vector: np.ndarray,
) -> np.ndarray:
    """Mantém o sinal do eixo estável entre execuções."""

    vector = _normalize(vector)
    dominant = int(
        np.argmax(np.abs(vector))
    )

    if vector[dominant] < 0.0:
        vector = -vector

    return vector


def _orthonormal_basis(
    axis: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    axis = _normalize(axis)

    helper = (
        np.array([0.0, 0.0, 1.0])
        if abs(axis[2]) < 0.90
        else np.array([0.0, 1.0, 0.0])
    )

    basis_u = _normalize(
        np.cross(axis, helper)
    )
    basis_v = _normalize(
        np.cross(axis, basis_u)
    )

    return basis_u, basis_v


def _fit_circle_2d(
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[float, float, float]:
    """Ajusta um círculo 2D por mínimos quadrados."""

    matrix = np.column_stack(
        (
            2.0 * x,
            2.0 * y,
            np.ones_like(x),
        )
    )
    rhs = x * x + y * y

    solution, *_ = np.linalg.lstsq(
        matrix,
        rhs,
        rcond=None,
    )

    center_x = float(solution[0])
    center_y = float(solution[1])
    constant = float(solution[2])

    radius_squared = (
        center_x * center_x
        + center_y * center_y
        + constant
    )

    if radius_squared <= 1.0e-12:
        raise ValueError(
            "Não foi possível determinar um raio válido."
        )

    return (
        center_x,
        center_y,
        sqrt(radius_squared),
    )


def _robust_scale(
    values: np.ndarray,
) -> float:
    median = float(
        np.median(values)
    )
    mad = float(
        np.median(
            np.abs(values - median)
        )
    )

    return max(
        1.4826 * mad,
        1.0e-9,
    )


def _evaluate_axis(
    points: np.ndarray,
    normals: np.ndarray,
    axis: np.ndarray,
) -> _AxisEvaluation:
    """
    Avalia uma direção candidata.

    A pontuação combina:
    - erro radial do cilindro;
    - perpendicularidade entre eixo e normais;
    - estabilidade do raio.
    """

    axis = _stable_direction(axis)
    centroid = points.mean(axis=0)
    basis_u, basis_v = (
        _orthonormal_basis(axis)
    )

    centered = points - centroid
    x = centered @ basis_u
    y = centered @ basis_v
    axial = centered @ axis

    center_x, center_y, radius = (
        _fit_circle_2d(x, y)
    )

    radial = np.sqrt(
        (x - center_x) ** 2
        + (y - center_y) ** 2
    )
    residuals = radial - radius

    radial_sigma = _robust_scale(
        residuals
    )
    radial_clip = max(
        radial_sigma * 3.5,
        radius * 0.015,
        0.01,
    )

    clipped_residuals = np.clip(
        residuals,
        -radial_clip,
        radial_clip,
    )

    radial_score = sqrt(
        float(
            np.mean(
                clipped_residuals
                * clipped_residuals
            )
        )
    )

    normal_dot = np.abs(
        normals @ axis
    )
    normal_score = sqrt(
        float(
            np.mean(
                normal_dot * normal_dot
            )
        )
    )

    # Evita eixos degenerados que transformam uma faixa
    # quase plana em um cilindro de raio enorme.
    radial_spread = float(
        np.std(radial)
    )
    radius_penalty = (
        radial_spread
        / max(radius, 1.0e-9)
    )

    score = (
        radial_score
        + radius * normal_score * 0.30
        + radius * radius_penalty * 0.05
    )

    axis_center = (
        centroid
        + center_x * basis_u
        + center_y * basis_v
    )

    minimum_axial = float(
        np.min(axial)
    )
    maximum_axial = float(
        np.max(axial)
    )
    length = (
        maximum_axial
        - minimum_axial
    )

    axial_midpoint = (
        minimum_axial
        + maximum_axial
    ) / 2.0

    cylinder_center = (
        axis_center
        + axial_midpoint * axis
    )

    return _AxisEvaluation(
        axis=axis,
        center=cylinder_center,
        radius=float(radius),
        length=float(length),
        residuals=residuals,
        axial=axial,
        x=x - center_x,
        y=y - center_y,
        score=float(score),
    )


def _initial_axis_candidates(
    points: np.ndarray,
    normals: np.ndarray,
) -> list[np.ndarray]:
    """Cria candidatos a partir de pontos e normais."""

    candidates: list[np.ndarray] = []

    point_centered = (
        points - points.mean(axis=0)
    )
    point_covariance = (
        point_centered.T
        @ point_centered
    )
    _, point_vectors = np.linalg.eigh(
        point_covariance
    )

    # Para furos curtos, o eixo costuma ser a direção de
    # menor variação dos pontos. Mantemos as três direções
    # como candidatas para não assumir a proporção da peça.
    for index in range(3):
        candidates.append(
            _stable_direction(
                point_vectors[:, index]
            )
        )

    normal_covariance = (
        normals.T @ normals
    )
    _, normal_vectors = np.linalg.eigh(
        normal_covariance
    )

    # Em um cilindro, o eixo é a direção de menor energia
    # das normais radiais.
    for index in range(3):
        candidates.append(
            _stable_direction(
                normal_vectors[:, index]
            )
        )

    # Produtos vetoriais entre normais distantes também
    # sugerem diretamente a direção do eixo.
    sample_count = min(
        normals.shape[0],
        600,
    )
    indices = np.linspace(
        0,
        normals.shape[0] - 1,
        sample_count,
        dtype=int,
    )
    sampled = normals[indices]

    step = max(
        1,
        sample_count // 24,
    )

    for first in range(
        0,
        sample_count,
        step,
    ):
        for second in range(
            first + step,
            sample_count,
            step,
        ):
            cross_product = np.cross(
                sampled[first],
                sampled[second],
            )
            cross_length = float(
                np.linalg.norm(
                    cross_product
                )
            )

            if cross_length < 0.25:
                continue

            candidates.append(
                _stable_direction(
                    cross_product
                )
            )

            if len(candidates) >= 90:
                break

        if len(candidates) >= 90:
            break

    # Remove candidatos praticamente repetidos.
    unique: list[np.ndarray] = []

    for candidate in candidates:
        if any(
            abs(
                float(
                    np.dot(
                        candidate,
                        existing,
                    )
                )
            )
            > 0.998
            for existing in unique
        ):
            continue

        unique.append(candidate)

    return unique


def _refine_axis(
    points: np.ndarray,
    normals: np.ndarray,
    initial_axis: np.ndarray,
) -> _AxisEvaluation:
    """
    Refina localmente o eixo em ângulos decrescentes.

    É uma otimização geométrica sem dependência externa.
    """

    best = _evaluate_axis(
        points,
        normals,
        initial_axis,
    )

    for angle_degrees in (
        12.0,
        6.0,
        3.0,
        1.5,
        0.75,
        0.35,
    ):
        basis_u, basis_v = (
            _orthonormal_basis(
                best.axis
            )
        )

        angle = radians(
            angle_degrees
        )
        tangent_scale = sin(angle)
        axis_scale = cos(angle)

        candidates = [
            _stable_direction(
                best.axis * axis_scale
                + basis_u * tangent_scale
            ),
            _stable_direction(
                best.axis * axis_scale
                - basis_u * tangent_scale
            ),
            _stable_direction(
                best.axis * axis_scale
                + basis_v * tangent_scale
            ),
            _stable_direction(
                best.axis * axis_scale
                - basis_v * tangent_scale
            ),
            _stable_direction(
                best.axis * axis_scale
                + (
                    basis_u + basis_v
                )
                / sqrt(2.0)
                * tangent_scale
            ),
            _stable_direction(
                best.axis * axis_scale
                + (
                    basis_u - basis_v
                )
                / sqrt(2.0)
                * tangent_scale
            ),
            _stable_direction(
                best.axis * axis_scale
                - (
                    basis_u + basis_v
                )
                / sqrt(2.0)
                * tangent_scale
            ),
            _stable_direction(
                best.axis * axis_scale
                - (
                    basis_u - basis_v
                )
                / sqrt(2.0)
                * tangent_scale
            ),
        ]

        improved = best

        for candidate in candidates:
            evaluation = _evaluate_axis(
                points,
                normals,
                candidate,
            )

            if (
                evaluation.score
                < improved.score
            ):
                improved = evaluation

        best = improved

    return best


def fit_cylinder_to_points(
    points: Any,
    normals: Any,
) -> CylinderFitResult:
    """
    Ajusta simultaneamente direção, raio e posição.

    O método seleciona o melhor candidato global e depois
    refina a direção em passos angulares decrescentes.
    """

    point_array = np.asarray(
        points,
        dtype=float,
    )
    normal_array = np.asarray(
        normals,
        dtype=float,
    )

    if (
        point_array.ndim != 2
        or point_array.shape[1] != 3
        or normal_array.shape
        != point_array.shape
    ):
        raise ValueError(
            "Pontos e normais devem formar matrizes N × 3."
        )

    valid_mask = (
        np.isfinite(
            point_array
        ).all(axis=1)
        & np.isfinite(
            normal_array
        ).all(axis=1)
    )

    point_array = point_array[
        valid_mask
    ]
    normal_array = normal_array[
        valid_mask
    ]

    normal_lengths = np.linalg.norm(
        normal_array,
        axis=1,
    )
    valid_normals = (
        normal_lengths > 1.0e-12
    )

    point_array = point_array[
        valid_normals
    ]
    normal_array = normal_array[
        valid_normals
    ]
    normal_lengths = normal_lengths[
        valid_normals
    ]

    if point_array.shape[0] < 20:
        raise ValueError(
            "A região possui poucos pontos válidos."
        )

    normal_array = (
        normal_array
        / normal_lengths[:, None]
    )

    candidates = (
        _initial_axis_candidates(
            point_array,
            normal_array,
        )
    )

    if not candidates:
        raise ValueError(
            "Não foi possível gerar direções candidatas."
        )

    evaluations: list[
        _AxisEvaluation
    ] = []

    for candidate in candidates:
        try:
            evaluations.append(
                _evaluate_axis(
                    point_array,
                    normal_array,
                    candidate,
                )
            )
        except (
            ValueError,
            np.linalg.LinAlgError,
        ):
            continue

    if not evaluations:
        raise ValueError(
            "Nenhum eixo candidato produziu um cilindro válido."
        )

    preliminary = min(
        evaluations,
        key=lambda item: item.score,
    )

    refined = _refine_axis(
        point_array,
        normal_array,
        preliminary.axis,
    )

    radial_sigma = _robust_scale(
        refined.residuals
    )
    radial_tolerance = max(
        radial_sigma * 3.5,
        refined.radius * 0.025,
        0.03,
    )

    inlier_mask = (
        np.abs(
            refined.residuals
        )
        <= radial_tolerance
    )

    if (
        np.count_nonzero(
            inlier_mask
        )
        >= 20
        and not np.all(inlier_mask)
    ):
        point_array = point_array[
            inlier_mask
        ]
        normal_array = normal_array[
            inlier_mask
        ]

        refined = _refine_axis(
            point_array,
            normal_array,
            refined.axis,
        )

        radial_sigma = _robust_scale(
            refined.residuals
        )
        radial_tolerance = max(
            radial_sigma * 3.5,
            refined.radius * 0.025,
            0.03,
        )

    if refined.length <= 1.0e-9:
        raise ValueError(
            "O comprimento estimado é muito pequeno."
        )

    rms_error = sqrt(
        float(
            np.mean(
                refined.residuals
                * refined.residuals
            )
        )
    )
    maximum_error = float(
        np.max(
            np.abs(
                refined.residuals
            )
        )
    )

    angles = np.mod(
        np.arctan2(
            refined.y,
            refined.x,
        ),
        2.0 * np.pi,
    )
    angles.sort()

    if angles.shape[0] > 1:
        gaps = np.diff(
            np.concatenate(
                [
                    angles,
                    angles[:1]
                    + 2.0 * np.pi,
                ]
            )
        )

        coverage_angle = (
            360.0
            - float(
                np.degrees(
                    np.max(gaps)
                )
            )
        )
    else:
        coverage_angle = 0.0

    return CylinderFitResult(
        center=(
            float(refined.center[0]),
            float(refined.center[1]),
            float(refined.center[2]),
        ),
        axis_direction=(
            float(refined.axis[0]),
            float(refined.axis[1]),
            float(refined.axis[2]),
        ),
        radius=float(
            refined.radius
        ),
        length=float(
            refined.length
        ),
        rms_error=rms_error,
        maximum_error=maximum_error,
        point_count=int(
            point_array.shape[0]
        ),
        coverage_angle=float(
            max(
                0.0,
                min(
                    360.0,
                    coverage_angle,
                ),
            )
        ),
        radial_tolerance=float(
            radial_tolerance
        ),
        axis_score=float(
            refined.score
        ),
    )
