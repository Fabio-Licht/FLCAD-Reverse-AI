"""Orchestration capability for mesh region growing."""

from __future__ import annotations

from time import perf_counter

from domain.mesh.mesh_entity import MeshEntity
from domain.recognition.region.calculators.region_growing_calculator import (
    RegionGrowingCalculator,
)
from domain.recognition.region.reports.region_growing_report import (
    RegionGrowingReport,
)
from domain.recognition.region.value_objects.region_seed import RegionSeed
from domain.recognition.region.value_objects.region_settings import (
    RegionSettings,
)


class RegionGrowingCapability:
    """Validate and orchestrate topology-based region segmentation."""

    def __init__(
        self,
        calculator: RegionGrowingCalculator | None = None,
    ) -> None:
        self._calculator = calculator or RegionGrowingCalculator()

    def execute(
        self,
        mesh: MeshEntity,
        seed: RegionSeed,
        settings: RegionSettings,
    ) -> RegionGrowingReport:
        """Execute region growing and return its immutable report."""

        self._validate(mesh, seed)
        started_at = perf_counter()
        region = self._calculator.calculate(mesh, seed, settings)
        execution_time = perf_counter() - started_at
        warnings = self._warnings(region, settings)

        return RegionGrowingReport(
            region=region,
            execution_time=execution_time,
            warnings=warnings,
        )

    @staticmethod
    def _validate(mesh: MeshEntity, seed: RegionSeed) -> None:
        """Validate inputs without performing segmentation calculations."""

        if mesh.mesh_data is None:
            raise ValueError("Region growing requires mesh data.")

        try:
            face_count = len(mesh.mesh_data.faces)
        except TypeError as error:
            raise TypeError("Mesh faces must be a sized collection.") from error

        if seed.triangle_index >= face_count:
            raise IndexError("Region seed triangle index is outside the mesh.")

    @staticmethod
    def _warnings(
        region: Region,
        settings: RegionSettings,
    ) -> tuple[str, ...]:
        """Return validation warnings for the calculated region."""

        warnings: list[str] = []

        if len(region.triangle_indices) < settings.minimum_region_size:
            warnings.append(
                "Region contains fewer triangles than the configured minimum."
            )

        if region.area == 0.0:
            warnings.append("Region contains only degenerate triangles.")

        return tuple(warnings)
