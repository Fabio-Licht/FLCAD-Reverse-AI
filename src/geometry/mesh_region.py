from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import cos, radians, sin
from typing import Any

import numpy as np


@dataclass(frozen=True)
class MeshRegionResult:
    """Região conectada extraída de uma malha."""

    cell_ids: tuple[int, ...]
    points: np.ndarray
    seed_cell_id: int

    @property
    def triangle_count(self) -> int:
        return len(self.cell_ids)

    @property
    def point_count(self) -> int:
        return int(self.points.shape[0])


def grow_planar_region(
    mesh: Any,
    seed_point: tuple[float, float, float],
    radius: float,
    maximum_angle_degrees: float,
    maximum_cells: int = 75_000,
) -> MeshRegionResult:
    """
    Expande uma região a partir do triângulo mais próximo.

    A expansão respeita:
    - conectividade por arestas;
    - raio máximo em torno do clique;
    - diferença angular entre normais;
    - limite de segurança de células.
    """

    if radius <= 0.0:
        raise ValueError(
            "O raio da região deve ser positivo."
        )

    if not 0.0 < maximum_angle_degrees < 90.0:
        raise ValueError(
            "O limite angular deve estar entre 0 e 90 graus."
        )

    working_mesh = mesh.compute_normals(
        point_normals=False,
        cell_normals=True,
        consistent_normals=True,
        auto_orient_normals=True,
        inplace=False,
    )

    seed = np.asarray(
        seed_point,
        dtype=float,
    )

    seed_cell_id = int(
        working_mesh.find_closest_cell(seed)
    )

    normals = np.asarray(
        working_mesh.cell_data["Normals"],
        dtype=float,
    )

    seed_normal = normals[seed_cell_id]
    seed_normal_length = float(
        np.linalg.norm(seed_normal)
    )

    if seed_normal_length <= 1.0e-12:
        raise ValueError(
            "A célula inicial não possui normal válida."
        )

    seed_normal = seed_normal / seed_normal_length
    minimum_dot = cos(
        radians(maximum_angle_degrees)
    )

    queue: deque[int] = deque(
        [seed_cell_id]
    )
    visited: set[int] = set()
    accepted: list[int] = []

    radius_squared = radius * radius

    while queue:
        cell_id = queue.popleft()

        if cell_id in visited:
            continue

        visited.add(cell_id)

        cell = working_mesh.get_cell(cell_id)
        cell_points = np.asarray(
            cell.points,
            dtype=float,
        )

        if cell_points.size == 0:
            continue

        center = cell_points.mean(axis=0)
        offset = center - seed

        if (
            float(np.dot(offset, offset))
            > radius_squared
        ):
            continue

        normal = normals[cell_id]
        normal_length = float(
            np.linalg.norm(normal)
        )

        if normal_length <= 1.0e-12:
            continue

        normal = normal / normal_length

        if float(
            np.dot(normal, seed_normal)
        ) < minimum_dot:
            continue

        accepted.append(cell_id)

        if len(accepted) >= maximum_cells:
            break

        for neighbor_id in (
            working_mesh.cell_neighbors(
                cell_id,
                connections="edges",
            )
        ):
            neighbor_id = int(neighbor_id)

            if neighbor_id not in visited:
                queue.append(neighbor_id)

    if not accepted:
        raise ValueError(
            "Nenhum triângulo compatível foi encontrado."
        )

    region_mesh = working_mesh.extract_cells(
        accepted
    )

    points = np.asarray(
        region_mesh.points,
        dtype=float,
    )

    if points.shape[0] < 3:
        raise ValueError(
            "A região encontrada possui poucos pontos."
        )

    # Remove coordenadas duplicadas para evitar peso artificial
    # no ajuste de mínimos quadrados.
    rounded_points = np.round(
        points,
        decimals=9,
    )

    _, unique_indices = np.unique(
        rounded_points,
        axis=0,
        return_index=True,
    )

    unique_points = points[
        np.sort(unique_indices)
    ]

    return MeshRegionResult(
        cell_ids=tuple(accepted),
        points=unique_points,
        seed_cell_id=seed_cell_id,
    )



def grow_cylindrical_region(
    mesh: Any,
    seed_point: tuple[float, float, float],
    radius: float,
    maximum_neighbor_angle_degrees: float,
    maximum_cells: int = 75_000,
) -> tuple[MeshRegionResult, np.ndarray]:
    """
    Expande uma região curva conectada.

    A normal é comparada entre triângulos vizinhos,
    permitindo a rotação gradual típica de cilindros.
    """

    if radius <= 0.0:
        raise ValueError(
            "O raio da região deve ser positivo."
        )

    if not 0.0 < maximum_neighbor_angle_degrees < 90.0:
        raise ValueError(
            "O limite angular deve estar entre 0 e 90 graus."
        )

    working_mesh = mesh.compute_normals(
        point_normals=True,
        cell_normals=True,
        consistent_normals=True,
        auto_orient_normals=True,
        inplace=False,
    )

    seed = np.asarray(
        seed_point,
        dtype=float,
    )

    seed_cell_id = int(
        working_mesh.find_closest_cell(seed)
    )

    cell_normals = np.asarray(
        working_mesh.cell_data["Normals"],
        dtype=float,
    )

    minimum_dot = cos(
        radians(maximum_neighbor_angle_degrees)
    )
    radius_squared = radius * radius

    queue: deque[int] = deque(
        [seed_cell_id]
    )
    visited: set[int] = set()
    accepted: list[int] = []

    while queue:
        cell_id = queue.popleft()

        if cell_id in visited:
            continue

        visited.add(cell_id)

        cell = working_mesh.get_cell(cell_id)
        cell_points = np.asarray(
            cell.points,
            dtype=float,
        )

        if cell_points.size == 0:
            continue

        center = cell_points.mean(axis=0)
        offset = center - seed

        if (
            float(np.dot(offset, offset))
            > radius_squared
        ):
            continue

        accepted.append(cell_id)

        if len(accepted) >= maximum_cells:
            break

        current_normal = cell_normals[cell_id]
        current_length = float(
            np.linalg.norm(current_normal)
        )

        if current_length <= 1.0e-12:
            continue

        current_normal = (
            current_normal / current_length
        )

        for neighbor_id in (
            working_mesh.cell_neighbors(
                cell_id,
                connections="edges",
            )
        ):
            neighbor_id = int(neighbor_id)

            if neighbor_id in visited:
                continue

            neighbor_normal = cell_normals[
                neighbor_id
            ]
            neighbor_length = float(
                np.linalg.norm(neighbor_normal)
            )

            if neighbor_length <= 1.0e-12:
                continue

            neighbor_normal = (
                neighbor_normal / neighbor_length
            )

            if float(
                np.dot(
                    current_normal,
                    neighbor_normal,
                )
            ) >= minimum_dot:
                queue.append(neighbor_id)

    if not accepted:
        raise ValueError(
            "Nenhuma região cilíndrica conectada foi encontrada."
        )

    region_mesh = working_mesh.extract_cells(
        accepted
    )

    points = np.asarray(
        region_mesh.points,
        dtype=float,
    )
    point_normals = np.asarray(
        region_mesh.point_data["Normals"],
        dtype=float,
    )

    if points.shape[0] < 20:
        raise ValueError(
            "A região encontrada possui poucos pontos."
        )

    rounded_points = np.round(
        points,
        decimals=9,
    )
    _, unique_indices = np.unique(
        rounded_points,
        axis=0,
        return_index=True,
    )
    unique_indices = np.sort(unique_indices)

    result = MeshRegionResult(
        cell_ids=tuple(accepted),
        points=points[unique_indices],
        seed_cell_id=seed_cell_id,
    )

    return (
        result,
        point_normals[unique_indices],
    )



def refine_cylindrical_cells(
    mesh: Any,
    candidate_cell_ids: tuple[int, ...],
    seed_cell_id: int,
    cylinder_center: tuple[float, float, float],
    axis_direction: tuple[float, float, float],
    radius: float,
    radial_tolerance: float,
    normal_tolerance_degrees: float = 24.0,
) -> tuple[MeshRegionResult, np.ndarray]:
    """
    Remove planos, chanfros e superfícies vizinhas do ajuste.

    São preservados apenas os triângulos:
    - aproximadamente paralelos ao eixo;
    - próximos do raio calculado;
    - conectados ao triângulo inicial.
    """

    working_mesh = mesh.compute_normals(
        point_normals=True,
        cell_normals=True,
        consistent_normals=True,
        auto_orient_normals=True,
        inplace=False,
    )

    axis = np.asarray(
        axis_direction,
        dtype=float,
    )
    axis = axis / np.linalg.norm(axis)

    center = np.asarray(
        cylinder_center,
        dtype=float,
    )

    cell_normals = np.asarray(
        working_mesh.cell_data["Normals"],
        dtype=float,
    )

    maximum_axis_dot = sin(
        radians(normal_tolerance_degrees)
    )

    accepted_set: set[int] = set()

    for cell_id in candidate_cell_ids:
        cell_id = int(cell_id)
        cell = working_mesh.get_cell(
            cell_id
        )

        points = np.asarray(
            cell.points,
            dtype=float,
        )

        if points.size == 0:
            continue

        cell_center = points.mean(axis=0)
        relative = cell_center - center
        axial_component = (
            float(np.dot(relative, axis))
            * axis
        )
        radial_vector = (
            relative - axial_component
        )
        radial_distance = float(
            np.linalg.norm(radial_vector)
        )

        normal = cell_normals[cell_id]
        normal_length = float(
            np.linalg.norm(normal)
        )

        if normal_length <= 1.0e-12:
            continue

        normal = normal / normal_length

        if abs(
            float(np.dot(normal, axis))
        ) > maximum_axis_dot:
            continue

        if abs(
            radial_distance - radius
        ) > radial_tolerance:
            continue

        accepted_set.add(cell_id)

    if not accepted_set:
        raise ValueError(
            "Nenhum triângulo permaneceu após o refinamento cilíndrico."
        )

    # Mantém somente o componente conectado ao clique.
    if seed_cell_id not in accepted_set:
        seed_cell_id = min(
            accepted_set,
            key=lambda cell_id: abs(
                cell_id - seed_cell_id
            ),
        )

    queue: deque[int] = deque(
        [seed_cell_id]
    )
    connected: list[int] = []
    visited: set[int] = set()

    while queue:
        cell_id = queue.popleft()

        if (
            cell_id in visited
            or cell_id not in accepted_set
        ):
            continue

        visited.add(cell_id)
        connected.append(cell_id)

        for neighbor_id in (
            working_mesh.cell_neighbors(
                cell_id,
                connections="edges",
            )
        ):
            neighbor_id = int(
                neighbor_id
            )

            if (
                neighbor_id in accepted_set
                and neighbor_id not in visited
            ):
                queue.append(
                    neighbor_id
                )

    if len(connected) < 5:
        raise ValueError(
            "A região cilíndrica refinada ficou pequena demais."
        )

    region_mesh = (
        working_mesh.extract_cells(
            connected
        )
    )

    points = np.asarray(
        region_mesh.points,
        dtype=float,
    )
    point_normals = np.asarray(
        region_mesh.point_data["Normals"],
        dtype=float,
    )

    rounded_points = np.round(
        points,
        decimals=9,
    )

    _, unique_indices = np.unique(
        rounded_points,
        axis=0,
        return_index=True,
    )
    unique_indices = np.sort(
        unique_indices
    )

    result = MeshRegionResult(
        cell_ids=tuple(connected),
        points=points[unique_indices],
        seed_cell_id=seed_cell_id,
    )

    return (
        result,
        point_normals[unique_indices],
    )
