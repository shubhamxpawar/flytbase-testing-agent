"""Honest calibration metrics that keep fixture and target results separate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..models import CalibrationResult


@dataclass(frozen=True)
class Scorecard:
    target_kind: str
    total: int
    caught: int
    false_positives: int
    not_calibrated: int

    @property
    def catch_rate(self) -> float | None:
        denominator = self.total - self.not_calibrated
        return None if denominator == 0 else self.caught / denominator


def score(results: Iterable[CalibrationResult], target_kind: str) -> Scorecard:
    selected = [result for result in results if result.target_kind == target_kind]
    not_calibrated = sum(not result.artifact_paths for result in selected if result.expected_finding)
    caught = sum(result.expected_finding and result.observed_finding and bool(result.artifact_paths) for result in selected)
    false_positives = sum(not result.expected_finding and result.observed_finding for result in selected)
    return Scorecard(target_kind, len(selected), caught, false_positives, not_calibrated)


def is_publishable_target_scorecard(scorecard: Scorecard) -> bool:
    return (
        scorecard.target_kind == "target"
        and scorecard.not_calibrated == 0
        and scorecard.false_positives == 0
        and scorecard.catch_rate == 1.0
    )
