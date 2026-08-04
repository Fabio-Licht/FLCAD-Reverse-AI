"""
capability_provider.py

FLCAD Reverse AI

Capability Provider Interface
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from engineering.domain.engineering_task import EngineeringTask


class CapabilityProvider(ABC):
    """
    Base interface implemented by every Capability Provider.
    """

    @abstractmethod
    def capabilities(self) -> list[str]:
        """
        Returns all supported capabilities.
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, task: EngineeringTask) -> None:
        """
        Executes the supplied engineering task.
        """
        raise NotImplementedError