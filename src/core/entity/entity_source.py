"""Creation sources for FLCAD engineering entities."""

from enum import Enum


class EntitySource(str, Enum):
    """Identify how an engineering entity was created."""

    IMPORTED = "imported"
    RECOGNIZED = "recognized"
    CALCULATED = "calculated"
    GENERATED = "generated"
    USER = "user"
    AI = "ai"
