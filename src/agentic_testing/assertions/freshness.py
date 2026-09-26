"""Validate stale/current UI semantics against an observed payload age."""

from __future__ import annotations

from ..models import Verdict


def assert_freshness(
    payload_age_s: float | None,
    rendered_is_stale: bool | None,
    threshold_s: float,
) -> Verdict:
    if payload_age_s is None or rendered_is_stale is None:
        return Verdict.uncertain("payload age or rendered freshness indicator is unavailable")
    expected_is_stale = payload_age_s > threshold_s
    if expected_is_stale == rendered_is_stale:
        state = "stale" if expected_is_stale else "current"
        return Verdict.passed(f"payload age {payload_age_s:.1f}s is correctly shown as {state}")
    expected = "stale" if expected_is_stale else "current"
    actual = "stale" if rendered_is_stale else "current"
    return Verdict.failed(f"payload age {payload_age_s:.1f}s should be {expected}, but UI shows {actual}")
