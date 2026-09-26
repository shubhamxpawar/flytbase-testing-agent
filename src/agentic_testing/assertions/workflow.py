"""Deterministic flow assertions, such as the bounded-action join journey."""

from __future__ import annotations

from ..models import Verdict


def assert_join_flow(*, action_count: int | None, reached_dashboard: bool | None, max_actions: int = 2) -> Verdict:
    if action_count is None or reached_dashboard is None:
        return Verdict.uncertain("join action count or destination state is unavailable")
    if not reached_dashboard:
        return Verdict.failed("join flow did not reach the dashboard")
    if action_count > max_actions:
        return Verdict.failed(f"join flow required {action_count} actions; limit is {max_actions}")
    return Verdict.passed(f"join flow reached dashboard in {action_count} action(s)")
