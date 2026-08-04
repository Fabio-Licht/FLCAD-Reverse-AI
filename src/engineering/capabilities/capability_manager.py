"""
capability_manager.py

FLCAD Reverse AI

Engineering Capability Manager
"""

from __future__ import annotations

from engineering.capabilities.capability_provider import CapabilityProvider
from engineering.domain.engineering_task import EngineeringTask


class CapabilityManager:
    """
    Central registry for Engineering Capabilities.
    """

    def __init__(self) -> None:

        self._providers: dict[str, CapabilityProvider] = {}

    def register_provider(
        self,
        provider: CapabilityProvider,
    ) -> None:
        """
        Registers every capability exposed by a provider.
        """

        for capability in provider.capabilities():
            self._providers[capability] = provider

    def resolve(
        self,
        capability: str,
    ) -> CapabilityProvider | None:

        return self._providers.get(capability)

    def execute(
        self,
        task: EngineeringTask,
    ) -> None:

        provider = self.resolve(task.capability)

        if provider is None:

            print(
                f"[CapabilityManager] "
                f"No provider for {task.capability}"
            )

            return

        provider.execute(task)