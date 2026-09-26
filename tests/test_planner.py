from agentic_testing.models import Capability
from agentic_testing.planner import plan_capability


def test_planner_maps_connection_goal_to_deterministic_evaluator() -> None:
    plan = plan_capability(Capability("G4", "Connection status matches telemetry", "telemetry"))
    assert plan.evaluator == "connection_state"


def test_planner_marks_unknown_goal_unsupported() -> None:
    plan = plan_capability(Capability("unknown", "Unknown", "other"))
    assert plan.evaluator == "unsupported"
