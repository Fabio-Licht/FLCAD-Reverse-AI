"""
recognition_adapter.py

FLCAD Reverse AI

Engineering Adapter

Bridge between the Engineering Brain and the Recognition module.
"""

from __future__ import annotations

from engineering.capabilities.capability_provider import CapabilityProvider
from engineering.domain.engineering_task import EngineeringTask


class RecognitionAdapter(CapabilityProvider):
    """
    Adapter responsible for forwarding Engineering Tasks
    to the Recognition subsystem.
    """

    def capabilities(self) -> list[str]:
        """
        Returns all capabilities provided by this adapter.
        """

        return [
            "recognition.detect_planes",
            "recognition.detect_cylinders",
        ]

    def execute(self, task: EngineeringTask) -> None:
        """
        Executes a Recognition task using Engineering Capabilities.
        """

        if task.capability == "recognition.detect_planes":
            print("[Recognition] Detect Planes")

        elif task.capability == "recognition.detect_cylinders":
            print("[Recognition] Detect Cylinders")

        else:
            print(
                f"[Recognition] Unsupported capability: {task.capability}"
            )