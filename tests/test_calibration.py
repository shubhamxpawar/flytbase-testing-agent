from pathlib import Path

from agentic_testing.calibration.metrics import is_publishable_target_scorecard, score
from agentic_testing.calibration.mutations import MUTATIONS
from agentic_testing.calibration.fixture_app import FixtureState
from agentic_testing.models import CalibrationResult


def test_level_one_catalog_has_nine_cross_category_mutations() -> None:
    assert len(MUTATIONS) == 9
    assert {"map-geospatial", "video-media", "security"}.issubset({mutation.category for mutation in MUTATIONS})


def test_only_complete_real_target_scorecards_are_publishable() -> None:
    results = [
        CalibrationResult(mutation.id, mutation.category, True, True, "target", (Path(f"{mutation.id}.webm"),))
        for mutation in MUTATIONS
    ]
    assert is_publishable_target_scorecard(score(results, "target"))


def test_missing_target_evidence_blocks_publication() -> None:
    results = [CalibrationResult("M1", "visual", True, True, "target")]
    assert not is_publishable_target_scorecard(score(results, "target"))


def test_every_mutation_is_reversible_from_the_healthy_fixture() -> None:
    healthy = FixtureState.healthy()
    mutated = [healthy.apply(mutation.id) for mutation in MUTATIONS]
    assert all(state != healthy for state in mutated)
    assert FixtureState.healthy() == healthy
