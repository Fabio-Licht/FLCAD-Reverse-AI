"""Structural quality classifications for mesh analysis."""

from enum import Enum


class MeshQuality(str, Enum):
    """Classify whether a mesh is structurally available for analysis."""

    UNKNOWN = "unknown"
    EMPTY = "empty"
    INCOMPLETE = "incomplete"
    ANALYZABLE = "analyzable"
