"""
engineering_intent.py

FLCAD Reverse AI
Engineering Domain

Represents the engineering intent inferred from an Engineering Goal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


class IntentType(Enum):
    """Supported engineering intents."""

    REVERSE_ENGINEERING = "reverse_engineering"
    INSPECTION = "inspection"
    MANUFACTURING = "manufacturing"
    MESH_EDITING = "mesh_editing"
    CAD_MODELING = "cad_modeling"
    ALIGNMENT = "alignment"
    FEATURE_RECOGNITION = "feature_recognition"
    COST_ESTIMATION = "cost_estimation"
    DRAWING_GENERATION = "drawing_generation"
    CUSTOM = "custom"


@dataclass(slots=True)
class EngineeringIntent:
    """
    Represents the engineering intent derived from a user's goal.

    The Planner is responsible for converting Goals into Intents.
    """

    intent_type: IntentType

    title: str

    description: str = ""

    parameters: Dict[str, Any] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def set_parameter(self, key: str, value: Any) -> None:
        """Stores an execution parameter."""

        self.parameters[key] = value

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Returns an execution parameter."""

        return self.parameters.get(key, default)

    def add_metadata(self, key: str, value: Any) -> None:
        """Stores metadata."""

        self.metadata[key] = value

    def __str__(self) -> str:
        return f"{self.intent_type.name}: {self.title}"