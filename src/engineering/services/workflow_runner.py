"""
workflow_runner.py

FLCAD Reverse AI

Engineering Services

Coordinates the execution of Engineering Strategies.
"""

from __future__ import annotations

from engineering.brain.executor import Executor
from engineering.domain.engineering_session import EngineeringSession


class WorkflowRunner:
    """
    Coordinates the execution of an Engineering Session.

    Future responsibilities:

    - Progress monitoring
    - Logging
    - Pause / Resume
    - Retry
    - Parallel execution
    - Cloud execution
    """

    def __init__(self) -> None:

        self._executor = Executor()

    def run(
        self,
        session: EngineeringSession,
    ) -> EngineeringSession:
        """
        Executes an Engineering Session.
        """

        session.start()

        self._executor.execute(
            session.strategy
        )

        session.finish()

        return session