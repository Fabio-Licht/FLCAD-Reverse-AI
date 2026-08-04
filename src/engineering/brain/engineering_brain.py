"""
engineering_brain.py

FLCAD Reverse AI

Engineering Brain

Main entry point for Engineering workflow planning.
"""

from __future__ import annotations

from engineering.brain.planner import Planner
from engineering.services.workflow_runner import WorkflowRunner

from engineering.domain.engineering_goal import EngineeringGoal
from engineering.domain.engineering_session import EngineeringSession


class EngineeringBrain:
    """
    Main entry point of the Engineering Brain.

    Responsibilities:

    - Receive Engineering Goals
    - Create Engineering Intent
    - Create Engineering Strategy
    - Build Engineering Session
    - Execute Workflow
    """

    def __init__(self) -> None:

        self._planner = Planner()

        self._runner = WorkflowRunner()

    def process(
        self,
        goal: EngineeringGoal,
    ) -> EngineeringSession:
        """
        Complete engineering workflow.
        """

        intent = self._planner.create_intent(goal)

        strategy = self._planner.create_strategy(
            goal,
            intent,
        )

        session = EngineeringSession(
            id="SESSION-001",
            goal=goal,
            intent=intent,
            strategy=strategy,
        )

        return self._runner.run(session)