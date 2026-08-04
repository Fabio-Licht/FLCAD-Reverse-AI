"""
engineering_session.py

FLCAD Reverse AI
Engineering Domain

Represents a complete engineering session.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from engineering.domain.engineering_goal import EngineeringGoal
from engineering.domain.engineering_intent import EngineeringIntent
from engineering.domain.engineering_strategy import EngineeringStrategy


@dataclass(slots=True)
class EngineeringSession:
    """
    Represents one engineering workflow execution.

    A session stores everything that happened during the
    engineering process.
    """

    id: str

    goal: EngineeringGoal

    intent: EngineeringIntent

    strategy: EngineeringStrategy

    created_at: datetime = field(default_factory=datetime.now)

    started_at: datetime | None = None

    finished_at: datetime | None = None

    notes: list[str] = field(default_factory=list)

    metadata: dict[str, object] = field(default_factory=dict)

    def start(self) -> None:
        """Marks the beginning of execution."""

        self.started_at = datetime.now()

    def finish(self) -> None:
        """Marks the end of execution."""

        self.finished_at = datetime.now()

    def add_note(self, note: str) -> None:
        """Adds a session note."""

        self.notes.append(note)

    @property
    def duration_seconds(self) -> float:

        if self.started_at is None:
            return 0.0

        end = self.finished_at or datetime.now()

        return (end - self.started_at).total_seconds()

    def __str__(self) -> str:

        return (
            f"EngineeringSession("
            f"{self.goal.title}"
            f")"
        )