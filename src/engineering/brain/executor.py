"""
executor.py

FLCAD Reverse AI

Engineering Brain
"""

from __future__ import annotations

from engineering.adapters.recognition_adapter import RecognitionAdapter
from engineering.capabilities.capability_manager import CapabilityManager

from engineering.domain.engineering_strategy import EngineeringStrategy
from engineering.domain.engineering_task import EngineeringTask


class Executor:

    def __init__(self) -> None:

        self._capabilities = CapabilityManager()

        self._capabilities.register_provider(
            RecognitionAdapter()
        )

    def execute(
        self,
        strategy: EngineeringStrategy,
    ) -> EngineeringStrategy:

        for task in strategy.tasks:

            self.execute_task(task)

        return strategy

    def execute_task(
        self,
        task: EngineeringTask,
    ) -> None:

        task.start()

        self._capabilities.execute(task)

        task.complete()