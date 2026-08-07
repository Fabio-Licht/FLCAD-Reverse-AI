"""Generic, backend-independent octree spatial index."""

from __future__ import annotations

from typing import Generic, TypeVar

from domain.mesh.bounding_box import BoundingBox
from domain.spatial.interfaces.spatial_index import SpatialIndex
from domain.spatial.objects.spatial_object import SpatialObject
from domain.spatial.octree.octree_config import OctreeConfig
from domain.spatial.octree.octree_node import OctreeNode
from domain.spatial.query.spatial_query import SpatialQuery


SpatialObjectT = TypeVar("SpatialObjectT", bound=SpatialObject)


class Octree(SpatialIndex[SpatialObjectT], Generic[SpatialObjectT]):
    """Index generic spatial objects using lazy octree subdivision."""

    def __init__(self, config: OctreeConfig) -> None:
        self._config = config
        self._root: OctreeNode[SpatialObjectT] | None = None
        self._objects: dict[int, SpatialObjectT] = {}

    def insert(self, spatial_object: SpatialObjectT) -> bool:
        """Insert an object if the same instance is not already indexed."""

        object_key = id(spatial_object)

        if object_key in self._objects:
            return False

        object_bounds = spatial_object.bounding_box()
        self._objects[object_key] = spatial_object

        if self._root is None:
            self._root = OctreeNode(bounding_box=object_bounds)
            self._root.objects.append(spatial_object)
            return True

        if not self._contains(self._root.bounding_box, object_bounds):
            self._rebuild()
            return True

        self._insert_into_node(self._root, spatial_object, object_bounds)
        return True

    def remove(self, spatial_object: SpatialObjectT) -> bool:
        """Remove an indexed object by instance identity."""

        object_key = id(spatial_object)

        if object_key not in self._objects:
            return False

        del self._objects[object_key]

        if self._root is not None:
            self._remove_from_node(self._root, spatial_object)

        if not self._objects:
            self._root = None

        return True

    def update(self, spatial_object: SpatialObjectT) -> bool:
        """Reindex an object after its bounding box changes."""

        if id(spatial_object) not in self._objects:
            return False

        self._rebuild()
        return True

    def query(self, query: SpatialQuery) -> tuple[SpatialObjectT, ...]:
        """Return objects whose bounding boxes satisfy the query."""

        if self._root is None:
            return ()

        results: list[SpatialObjectT] = []
        self._query_node(self._root, query, results)
        return tuple(results)

    def clear(self) -> None:
        """Remove all indexed objects and nodes."""

        self._objects.clear()
        self._root = None

    def _rebuild(self) -> None:
        """Rebuild the hierarchy around all current object bounds."""

        objects = tuple(self._objects.values())

        if not objects:
            self._root = None
            return

        root_bounds = objects[0].bounding_box()

        for spatial_object in objects[1:]:
            root_bounds = self._union(
                root_bounds,
                spatial_object.bounding_box(),
            )

        self._root = OctreeNode(bounding_box=root_bounds)

        for spatial_object in objects:
            self._insert_into_node(
                self._root,
                spatial_object,
                spatial_object.bounding_box(),
            )

    def _insert_into_node(
        self,
        node: OctreeNode[SpatialObjectT],
        spatial_object: SpatialObjectT,
        object_bounds: BoundingBox,
    ) -> None:
        """Insert one object into the deepest containing node."""

        child = self._containing_child(node, object_bounds)

        if child is not None:
            self._insert_into_node(child, spatial_object, object_bounds)
            return

        node.objects.append(spatial_object)

        if (
            len(node.objects) > self._config.max_objects_per_node
            and not node.children
            and self._can_subdivide(node)
        ):
            self._subdivide(node)

    def _subdivide(self, node: OctreeNode[SpatialObjectT]) -> None:
        """Create child nodes and redistribute contained objects."""

        if not node.objects:
            return

        node.children = [
            OctreeNode(bounding_box=bounds, depth=node.depth + 1)
            for bounds in self._child_bounds(node.bounding_box)
        ]

        retained: list[SpatialObjectT] = []

        for spatial_object in node.objects:
            object_bounds = spatial_object.bounding_box()
            child = self._containing_child(node, object_bounds)

            if child is None:
                retained.append(spatial_object)
            else:
                self._insert_into_node(
                    child,
                    spatial_object,
                    object_bounds,
                )

        node.objects = retained

    def _can_subdivide(self, node: OctreeNode[SpatialObjectT]) -> bool:
        """Return whether depth and minimum-size limits allow a split."""

        if node.depth >= self._config.max_depth:
            return False

        return all(
            (maximum - minimum) / 2.0
            >= self._config.minimum_cell_size
            and maximum > minimum
            for minimum, maximum in zip(
                node.bounding_box.minimum,
                node.bounding_box.maximum,
            )
        )

    def _containing_child(
        self,
        node: OctreeNode[SpatialObjectT],
        object_bounds: BoundingBox,
    ) -> OctreeNode[SpatialObjectT] | None:
        """Return the single child that fully contains object bounds."""

        for child in node.children:
            if self._contains(child.bounding_box, object_bounds):
                return child

        return None

    def _query_node(
        self,
        node: OctreeNode[SpatialObjectT],
        query: SpatialQuery,
        results: list[SpatialObjectT],
    ) -> None:
        """Collect matching objects from intersecting nodes."""

        if not query.intersects(node.bounding_box):
            return

        results.extend(
            spatial_object
            for spatial_object in node.objects
            if query.intersects(spatial_object.bounding_box())
        )

        for child in node.children:
            self._query_node(child, query, results)

    def _remove_from_node(
        self,
        node: OctreeNode[SpatialObjectT],
        spatial_object: SpatialObjectT,
    ) -> bool:
        """Remove an object identity from this node or its descendants."""

        for index, candidate in enumerate(node.objects):
            if candidate is spatial_object:
                del node.objects[index]
                return True

        for child in node.children:
            if self._remove_from_node(child, spatial_object):
                return True

        return False

    @staticmethod
    def _contains(container: BoundingBox, item: BoundingBox) -> bool:
        """Return whether one bounding box fully contains another."""

        return all(
            container_minimum <= item_minimum
            and item_maximum <= container_maximum
            for container_minimum, container_maximum, item_minimum, item_maximum
            in zip(
                container.minimum,
                container.maximum,
                item.minimum,
                item.maximum,
            )
        )

    @staticmethod
    def _union(first: BoundingBox, second: BoundingBox) -> BoundingBox:
        """Return bounds containing both input bounding boxes."""

        return BoundingBox(
            minimum=tuple(
                min(first_value, second_value)
                for first_value, second_value in zip(
                    first.minimum,
                    second.minimum,
                )
            ),
            maximum=tuple(
                max(first_value, second_value)
                for first_value, second_value in zip(
                    first.maximum,
                    second.maximum,
                )
            ),
        )

    @staticmethod
    def _child_bounds(bounds: BoundingBox) -> tuple[BoundingBox, ...]:
        """Return the eight equal octants of a bounding box."""

        midpoint = tuple(
            (minimum + maximum) / 2.0
            for minimum, maximum in zip(bounds.minimum, bounds.maximum)
        )
        children: list[BoundingBox] = []

        for x_upper in (False, True):
            for y_upper in (False, True):
                for z_upper in (False, True):
                    upper_flags = (x_upper, y_upper, z_upper)
                    minimum = tuple(
                        midpoint[axis]
                        if upper_flags[axis]
                        else bounds.minimum[axis]
                        for axis in range(3)
                    )
                    maximum = tuple(
                        bounds.maximum[axis]
                        if upper_flags[axis]
                        else midpoint[axis]
                        for axis in range(3)
                    )
                    children.append(
                        BoundingBox(minimum=minimum, maximum=maximum)
                    )

        return tuple(children)
