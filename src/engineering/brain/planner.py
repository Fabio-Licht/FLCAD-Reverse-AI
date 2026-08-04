"""
planner.py

FLCAD Reverse AI

Engineering Brain

Converts Engineering Goals into executable Engineering Strategies.
"""

from __future__ import annotations

from engineering.domain.engineering_goal import (
    EngineeringGoal,
    GoalType,
)

from engineering.domain.engineering_intent import (
    EngineeringIntent,
    IntentType,
)

from engineering.domain.engineering_strategy import EngineeringStrategy

from engineering.domain.engineering_task import (
    EngineeringTask,
)


class Planner:
    """
    First implementation of the Engineering Planner.

    Current version:
        Rule Based Planner

    Future versions:
        AI Planner
        Hybrid Planner
        Knowledge Planner
    """

    def create_intent(
        self,
        goal: EngineeringGoal,
    ) -> EngineeringIntent:

        mapping = {
            GoalType.RECONSTRUCT_PART:
                IntentType.REVERSE_ENGINEERING,

            GoalType.INSPECT_PART:
                IntentType.INSPECTION,

            GoalType.PREPARE_MANUFACTURING:
                IntentType.MANUFACTURING,

            GoalType.REPAIR_MESH:
                IntentType.MESH_EDITING,

            GoalType.ALIGN_SCAN:
                IntentType.ALIGNMENT,

            GoalType.COMPARE_SCAN:
                IntentType.INSPECTION,

            GoalType.GENERATE_CAD:
                IntentType.CAD_MODELING,

            GoalType.GENERATE_DRAWING:
                IntentType.DRAWING_GENERATION,

            GoalType.ESTIMATE_COST:
                IntentType.COST_ESTIMATION,
        }

        intent_type = mapping.get(
            goal.goal_type,
            IntentType.CUSTOM,
        )

        return EngineeringIntent(
            intent_type=intent_type,
            title=goal.title,
            description=goal.description,
        )

    def create_strategy(
        self,
        goal: EngineeringGoal,
        intent: EngineeringIntent,
    ) -> EngineeringStrategy:

        strategy = EngineeringStrategy(

            name=intent.title,

            description=intent.description,
        )

        if intent.intent_type == IntentType.REVERSE_ENGINEERING:

            strategy.add_task(

                EngineeringTask(

                    id="TASK-001",

                    name="Detect Planes",

                    engine="Recognition Engine",

                    capability="recognition.detect_planes",
                )
            )

            strategy.add_task(

                EngineeringTask(

                    id="TASK-002",

                    name="Detect Cylinders",

                    engine="Recognition Engine",

                    capability="recognition.detect_cylinders",
                )
            )

            strategy.add_task(

                EngineeringTask(

                    id="TASK-003",

                    name="Generate References",

                    engine="Engineering Kernel",

                    capability="kernel.generate_references",
                )
            )

        return strategy