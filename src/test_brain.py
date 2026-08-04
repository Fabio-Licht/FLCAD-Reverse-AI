from engineering.brain.engineering_brain import EngineeringBrain

from engineering.domain.engineering_goal import (
    EngineeringGoal,
    GoalType,
)


brain = EngineeringBrain()

goal = EngineeringGoal(

    goal_type=GoalType.RECONSTRUCT_PART,

    title="Reverse Engineering",

    description="Reconstruct scanned mold.",
)

session = brain.process(goal)

print()

print("========== RESULT ==========")

print(session.goal)

print(session.intent)

print(session.strategy)

print()

for task in session.strategy.tasks:

    print(task)

print()

print("Duration:", session.duration_seconds)