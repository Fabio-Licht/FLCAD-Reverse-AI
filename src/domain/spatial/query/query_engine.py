"""Official backend-independent entry point for spatial queries."""

from __future__ import annotations

from time import perf_counter
from typing import Generic, TypeVar

from domain.mesh.bounding_box import BoundingBox, Point3D
from domain.spatial.interfaces.spatial_index import SpatialIndex
from domain.spatial.objects.spatial_object import SpatialObject
from domain.spatial.query.bounding_box_query import BoundingBoxQuery
from domain.spatial.query.point_query import PointQuery
from domain.spatial.query.radius_query import RadiusQuery
from domain.spatial.query.spatial_query import SpatialQuery
from domain.spatial.query.spatial_query_result import SpatialQueryResult


SpatialObjectT = TypeVar("SpatialObjectT", bound=SpatialObject)


class QueryEngine(Generic[SpatialObjectT]):
    """Delegate public spatial queries to a configured spatial index."""

    def __init__(self, spatial_index: SpatialIndex[SpatialObjectT]) -> None:
        self._spatial_index = spatial_index

    def point(
        self,
        query: PointQuery | Point3D,
        tolerance: float | None = None,
    ) -> SpatialQueryResult[SpatialObjectT]:
        """Execute a point query with an optional axis tolerance."""

        if isinstance(query, PointQuery):
            if tolerance is not None:
                raise ValueError(
                    "Tolerance must be contained in the PointQuery."
                )
            point_query = query
        else:
            point_query = PointQuery(point=query, tolerance=tolerance)

        if point_query.tolerance in (None, 0.0):
            spatial_query = SpatialQuery.for_point(point_query.point)
        else:
            assert point_query.tolerance is not None
            spatial_query = SpatialQuery.for_bounding_box(
                BoundingBox(
                    minimum=tuple(
                        coordinate - point_query.tolerance
                        for coordinate in point_query.point
                    ),
                    maximum=tuple(
                        coordinate + point_query.tolerance
                        for coordinate in point_query.point
                    ),
                )
            )

        return self._execute(spatial_query)

    def radius(
        self,
        query: RadiusQuery | Point3D,
        radius: float | None = None,
    ) -> SpatialQueryResult[SpatialObjectT]:
        """Execute a spherical-radius query."""

        if isinstance(query, RadiusQuery):
            if radius is not None:
                raise ValueError(
                    "Radius must be contained in the RadiusQuery."
                )
            radius_query = query
        else:
            if radius is None:
                raise ValueError("A direct radius query requires a radius.")

            radius_query = RadiusQuery(center=query, radius=radius)

        return self._execute(
            SpatialQuery.for_radius(
                radius_query.center,
                radius_query.radius,
            )
        )

    def bounding_box(
        self,
        query: BoundingBoxQuery | BoundingBox,
    ) -> SpatialQueryResult[SpatialObjectT]:
        """Execute an axis-aligned bounding-box query."""

        bounds = (
            query.bounding_box
            if isinstance(query, BoundingBoxQuery)
            else query
        )
        return self._execute(SpatialQuery.for_bounding_box(bounds))

    def _execute(
        self,
        query: SpatialQuery,
    ) -> SpatialQueryResult[SpatialObjectT]:
        """Delegate one query and package its backend-neutral result."""

        started_at = perf_counter()
        objects = self._spatial_index.query(query)
        execution_time = perf_counter() - started_at

        return SpatialQueryResult(
            objects=objects,
            visited_nodes=0,
            execution_time=execution_time,
            candidate_count=len(objects),
        )


SpatialQueryEngine = QueryEngine
