"""Type classifications for FLCAD engineering entities."""

from enum import Enum


class EntityType(str, Enum):
    """Classify an engineering entity by its domain type."""

    UNKNOWN = "unknown"
    MESH = "mesh"
    POINT = "point"
    AXIS = "axis"
    PLANE = "plane"
    CYLINDER = "cylinder"
    CONE = "cone"
    SPHERE = "sphere"
    TORUS = "torus"
    CURVE = "curve"
    SURFACE = "surface"
    SKETCH = "sketch"
