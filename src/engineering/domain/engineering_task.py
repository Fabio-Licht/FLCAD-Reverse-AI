"""
engineering_task.py

FLCAD Reverse AI
Engineering Domain

Represents a single executable engineering task.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from engineering.domain.workflow_state import WorkflowState


class TaskPriority(Enum):
    """Execution priority."""

    LOW = 10
    NORMAL = 20
    HIGH = 30
    CRITICAL = 40


@dataclass(slots=True)
class EngineeringTask:
    """
    Represents one executable engineering task.

    Examples
    --------
    - Detect Planes
    - Detect Cylinders
    - Generate References
    - Align Scan
    - Generate CAD
    """

    id: str

    name: str

    description: str = ""

    engine: str = ""

    capability: str = ""

    priority: TaskPriority = TaskPriority.NORMAL

    state: WorkflowState = WorkflowState.CREATED

    parameters: dict[str, Any] = field(default_factory=dict)

    result: Any | None = None

    error_message: str | None = None

    def start(self) -> None:
        """Marks the task as running."""

        self.state = WorkflowState.RUNNING

    def complete(self, result: Any = None) -> None:
        """Marks the task as completed."""

        self.result = result
        self.state = WorkflowState.COMPLETED

    def fail(self, message: str) -> None:
        """Marks the task as failed."""

        self.error_message = message
        self.state = WorkflowState.FAILED

    @property
    def finished(self) -> bool:
        """Returns True if execution has finished."""

        return self.state.is_finished()

    def __str__(self) -> str:
        return (
            f"{self.name} "
            f"[{self.state.name}] "
            f"({self.priority.name})"
        )