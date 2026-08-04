"""
executor.py

FLCAD Reverse AI

Engineering Brain

Executes Engineering Strategies.
"""

from __future__ import annotations

from engineering.domain.engineering_strategy import EngineeringStrategy
from engineering.domain.engineering_task import EngineeringTask


class Executor:
    """
    Executes Engineering Strategies.

    Current version:

        Sequential execution.

    Future versions:

        Parallel execution
        Distributed execution
        Cloud execution
    """

    def execute(
        self,
        strategy: EngineeringStrategy,
    ) -> EngineeringStrategy:
        """
        Executes every task in the strategy.
        """

        for task in strategy.tasks:
            self.execute_task(task)

        return strategy

    def execute_task(
        self,
        task: EngineeringTask,
    ) -> None:
        """
        Executes one engineering task.

        Current implementation only simulates execution.
        """

        task.start()

        #
        # Future:
        #
        # Capability Manager
        #
        # Recognition Engine
        #
        # CAD Engine
        #
        # Mesh Engine
        #

        task.complete()