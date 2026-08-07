"""Relationship types between FLCAD engineering entities."""

from enum import Enum


class EntityRelationship(str, Enum):
    """Describe a governed relationship between engineering entities."""

    CONTAINS = "contains"
    PARALLEL = "parallel"
    PERPENDICULAR = "perpendicular"
    COINCIDENT = "coincident"
    INTERSECT = "intersect"
    TANGENT = "tangent"
    DEPENDS_ON = "depends_on"
    REFERENCES = "references"
    PARENT = "parent"
    CHILD = "child"
