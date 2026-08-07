"""Abstract strategy contract for mathematical plane fitting."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TypeAlias

from domain.mesh.bounding_box import Point3D
from domain.recognition.plane.value_objects.plane_fitting_settings import (
    PlaneFittingSettings,
)


PlaneStrategyResult: TypeAlias = tuple[
    Point3D,
    Point3D,
    tuple[float, ...],
    tuple[bool, ...],
]


class PlaneFittingStrategy(ABC):
    """Define a replaceable mathematical plane-fitting algorithm."""

    @abstractmethod
    def fit(
        self,
        points: Sequence[Point3D],
        settings: PlaneFittingSettings,
    ) -> PlaneStrategyResult:
        """Return origin, normal, residuals, and inlier classifications."""

        raise NotImplementedError
