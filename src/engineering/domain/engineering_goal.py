"""
engineering_goal.py

FLCAD Reverse AI
Engineering Domain

Represents the high-level engineering objective requested by the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


class GoalType(Enum):
    """Supported engineering goals."""

    RECONSTRUCT_PART = "reconstruct_part"
    INSPECT_PART = "inspect_part"
    PREPARE_MANUFACTURING = "prepare_manufacturing"
    REPAIR_MESH = "repair_mesh"
    ALIGN_SCAN = "align_scan"
    COMPARE_SCAN = "compare_scan"
    GENERATE_CAD = "generate_cad"
    GENERATE_DRAWING = "generate_drawing"
    ESTIMATE_COST = "estimate_cost"
    CUSTOM = "custom"


@dataclass(slots=True)
class EngineeringGoal:
    """
    Represents the user's engineering objective.

    The Engineering Goal is the highest abstraction inside the
    Engineering Brain workflow.

    Goal
        ↓
    Intent
        ↓
    Strategy
        ↓
    Tasks
        ↓
    Execution
    """

    goal_type: GoalType

    title: str

    description: str = ""

    context: Dict[str, Any] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_context(self, key: str, value: Any) -> None:
        """Adds contextual information."""

        self.context[key] = value

    def add_metadata(self, key: str, value: Any) -> None:
        """Adds metadata."""

        self.metadata[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Returns context information."""

        return self.context.get(key, default)

    def __str__(self) -> str:
        return f"{self.goal_type.name}: {self.title}"