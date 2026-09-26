"""Oracle-backed participant-list comparisons."""

from __future__ import annotations

from collections.abc import Iterable

from ..models import Verdict


def assert_participants(oracle_ids: Iterable[str] | None, rendered_ids: Iterable[str] | None) -> Verdict:
    if oracle_ids is None or rendered_ids is None:
        return Verdict.uncertain("oracle or rendered participant list is unavailable")
    expected, actual = set(oracle_ids), set(rendered_ids)
    if expected == actual:
        return Verdict.passed("participant list matches oracle")
    return Verdict.failed(f"participant list differs: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
