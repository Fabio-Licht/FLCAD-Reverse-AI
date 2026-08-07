"""Abstract contract for backend-independent spatial indexes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from domain.spatial.objects.spatial_object import SpatialObject
from domain.spatial.query.spatial_query import SpatialQuery


SpatialObjectT = TypeVar("SpatialObjectT", bound=SpatialObject)


class SpatialIndex(ABC, Generic[SpatialObjectT]):
    """Define mutation and query operations for a spatial index."""

    @abstractmethod
    def insert(self, spatial_object: SpatialObjectT) -> bool:
        """Insert an object and report whether it was newly indexed."""

        raise NotImplementedError

    @abstractmethod
    def remove(self, spatial_object: SpatialObjectT) -> bool:
        """Remove an object and report whether it was indexed."""

        raise NotImplementedError

    @abstractmethod
    def update(self, spatial_object: SpatialObjectT) -> bool:
        """Refresh the location of an indexed object."""

        raise NotImplementedError

    @abstractmethod
    def query(self, query: SpatialQuery) -> tuple[SpatialObjectT, ...]:
        """Return indexed objects matching a spatial query."""

        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Remove every object from the index."""

        raise NotImplementedError
