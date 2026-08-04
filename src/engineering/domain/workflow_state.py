"""
workflow_state.py

FLCAD Reverse AI
Engineering Domain

Defines the execution states of engineering workflows and tasks.
"""

from enum import Enum


class WorkflowState(Enum):
    """Execution state of a workflow or engineering task."""

    CREATED = "created"

    WAITING = "waiting"

    READY = "ready"

    RUNNING = "running"

    PAUSED = "paused"

    COMPLETED = "completed"

    FAILED = "failed"

    CANCELLED = "cancelled"

    SKIPPED = "skipped"

    VALIDATED = "validated"

    APPROVED = "approved"

    REJECTED = "rejected"

    def is_finished(self) -> bool:
        """Returns True if the workflow reached a terminal state."""

        return self in {
            WorkflowState.COMPLETED,
            WorkflowState.CANCELLED,
            WorkflowState.FAILED,
            WorkflowState.REJECTED,
        }

    def can_execute(self) -> bool:
        """Returns True if execution may start."""

        return self in {
            WorkflowState.CREATED,
            WorkflowState.WAITING,
            WorkflowState.READY,
        }