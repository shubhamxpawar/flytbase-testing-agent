"""Oracle-backed state equality checks."""

from __future__ import annotations

from typing import Any

from ..models import Verdict


def assert_state_equal(label: str, oracle_value: Any, rendered_value: Any) -> Verdict:
    if oracle_value is None or rendered_value is None:
        return Verdict.uncertain(f"{label} is unavailable in oracle or rendered state")
    if oracle_value == rendered_value:
        return Verdict.passed(f"{label} matches oracle state")
    return Verdict.failed(f"{label} differs: oracle={oracle_value!r}, rendered={rendered_value!r}")
