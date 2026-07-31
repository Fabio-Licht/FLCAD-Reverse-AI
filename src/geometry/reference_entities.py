from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import TypeAlias


Vector3: TypeAlias = tuple[float, float, float]
Point3: TypeAlias = tuple[float, float, float]


def vector_length(vector: Vector3) -> float:
    """Retorna o comprimento de um vetor tridimensional."""

    return sqrt(
        vector[0] ** 2
        + vector[1] ** 2
        + vector[2] ** 2
    )


def normalize_vector(vector: Vector3) -> Vector3:
    """Retorna o vetor com comprimento unitário."""

    length = vector_length(vector)

    if length <= 1.0e-12:
        raise ValueError(
            "Não é possível normalizar um vetor de comprimento zero."
        )

    return (
        vector[0] / length,
        vector[1] / length,
        vector[2] / length,
    )


@dataclass(frozen=True)
class PointReference:
    """Representa um ponto de referência tridimensional."""

    position: Point3

    @property
    def object_type(self) -> str:
        return "reference_point"


@dataclass(frozen=True)
class AxisReference:
    """
    Representa um eixo ou vetor de referência.

    A direção é sempre armazenada normalizada.
    """

    origin: Point3
    direction: Vector3
    display_length: float = 100.0

    def __post_init__(self) -> None:
        if self.display_length <= 0.0:
            raise ValueError(
                "O comprimento visual do eixo deve ser positivo."
            )

        object.__setattr__(
            self,
            "direction",
            normalize_vector(self.direction),
        )

    @property
    def object_type(self) -> str:
        return "reference_axis"


@dataclass(frozen=True)
class PlaneReference:
    """
    Representa um plano de referência.

    O plano é definido por uma origem e um vetor normal.
    """

    origin: Point3
    normal: Vector3
    size_x: float = 100.0
    size_y: float = 100.0

    def __post_init__(self) -> None:
        if self.size_x <= 0.0 or self.size_y <= 0.0:
            raise ValueError(
                "As dimensões visuais do plano devem ser positivas."
            )

        object.__setattr__(
            self,
            "normal",
            normalize_vector(self.normal),
        )

    @property
    def object_type(self) -> str:
        return "reference_plane"


@dataclass(frozen=True)
class CylinderReference:
    """
    Representa um cilindro reconhecido ou construído.

    O cilindro é definido por:
    - um ponto central no eixo;
    - direção do eixo;
    - raio;
    - comprimento;
    - informações opcionais do ajuste.
    """

    center: Point3
    axis_direction: Vector3
    radius: float
    length: float

    rms_error: float | None = None
    coverage_angle: float | None = None
    source_object_id: str | None = None

    def __post_init__(self) -> None:
        if self.radius <= 0.0:
            raise ValueError(
                "O raio do cilindro deve ser positivo."
            )

        if self.length <= 0.0:
            raise ValueError(
                "O comprimento do cilindro deve ser positivo."
            )

        if (
            self.coverage_angle is not None
            and not 0.0 <= self.coverage_angle <= 360.0
        ):
            raise ValueError(
                "A cobertura angular deve estar entre 0 e 360 graus."
            )

        object.__setattr__(
            self,
            "axis_direction",
            normalize_vector(self.axis_direction),
        )

    @property
    def diameter(self) -> float:
        """Retorna o diâmetro calculado."""

        return self.radius * 2.0

    @property
    def object_type(self) -> str:
        return "reference_cylinder"

    def create_axis(
        self,
        display_extension: float = 0.20,
    ) -> AxisReference:
        """
        Cria automaticamente o eixo central do cilindro.

        display_extension define quanto o eixo ultrapassará
        visualmente cada extremidade do cilindro.
        """

        extension = max(
            0.0,
            display_extension,
        )

        display_length = (
            self.length
            * (1.0 + extension * 2.0)
        )

        return AxisReference(
            origin=self.center,
            direction=self.axis_direction,
            display_length=display_length,
        )

    def create_center_point(self) -> PointReference:
        """Cria um ponto no centro do cilindro."""

        return PointReference(
            position=self.center
        )