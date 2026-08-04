"""
engineering_strategy.py

FLCAD Reverse AI
Engineering Domain

Represents an executable engineering strategy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engineering.domain.engineering_task import EngineeringTask


@dataclass(slots=True)
class EngineeringStrategy:
    """
    Represents a complete engineering execution strategy.

    A Strategy is composed of multiple EngineeringTasks.
    """

    name: str

    description: str = ""

    tasks: list[EngineeringTask] = field(default_factory=list)

    confidence: float = 1.0

    estimated_duration: float = 0.0

    warnings: list[str] = field(default_factory=list)

    metadata: dict[str, object] = field(default_factory=dict)

    def add_task(self, task: EngineeringTask) -> None:
        """Adds a task to the strategy."""

        self.tasks.append(task)

    def add_warning(self, warning: str) -> None:
        """Registers a warning."""

        self.warnings.append(warning)

    @property
    def task_count(self) -> int:
        """Returns the number of tasks."""

        return len(self.tasks)

    @property
    def completed_tasks(self) -> int:
        """Returns the number of completed tasks."""

        return sum(task.finished for task in self.tasks)

    @property
    def progress(self) -> float:
        """
        Returns execution progress between 0.0 and 1.0.
        """

        if not self.tasks:
            return 0.0

        return self.completed_tasks / self.task_count

    def __str__(self) -> str:
        return (
            f"{self.name} "
            f"({self.completed_tasks}/{self.task_count})"
        )