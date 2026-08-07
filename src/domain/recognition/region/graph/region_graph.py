"""Adjacency graph for segmented regions."""

from __future__ import annotations

from uuid import UUID

from domain.recognition.region.entities.region import Region


class RegionGraph:
    """Maintain explicit, undirected adjacency between regions."""

    def __init__(self) -> None:
        self._regions: dict[UUID, Region] = {}
        self._adjacency: dict[UUID, set[UUID]] = {}

    def add_region(self, region: Region) -> bool:
        """Add a region and report whether its identity was new."""

        if region.id in self._regions:
            return False

        self._regions[region.id] = region
        self._adjacency[region.id] = set()

        for neighbor_id in region.neighbors:
            if neighbor_id in self._regions:
                self.connect(region.id, neighbor_id)

        return True

    def connect(self, first_id: UUID, second_id: UUID) -> None:
        """Create an undirected connection between existing regions."""

        if first_id == second_id:
            raise ValueError("A region cannot be connected to itself.")

        if first_id not in self._regions or second_id not in self._regions:
            raise KeyError("Both regions must exist before they are connected.")

        self._adjacency[first_id].add(second_id)
        self._adjacency[second_id].add(first_id)

    def neighbors(self, region_id: UUID) -> tuple[Region, ...]:
        """Return regions adjacent to the requested region."""

        if region_id not in self._regions:
            raise KeyError(f"Region not found: {region_id}")

        return tuple(
            self._regions[neighbor_id]
            for neighbor_id in self._adjacency[region_id]
        )
