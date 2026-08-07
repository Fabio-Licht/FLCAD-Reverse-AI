"""Lifecycle states for FLCAD engineering entities."""

from enum import Enum


class EntityState(str, Enum):
    """Represent the lifecycle state of an engineering entity."""

    DRAFT = "draft"
    DETECTED = "detected"
    VALIDATED = "validated"
    CONFIRMED = "confirmed"
    REFERENCED = "referenced"
    LOCKED = "locked"
    MODIFIED = "modified"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
