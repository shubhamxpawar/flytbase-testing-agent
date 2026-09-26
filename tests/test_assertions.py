from agentic_testing.assertions.freshness import assert_freshness
from agentic_testing.assertions.geospatial import assert_marker_position
from agentic_testing.assertions.geometry import Rect, assert_visible_in_viewport
from agentic_testing.assertions.media import assert_video_identity
from agentic_testing.assertions.consistency import assert_selected_device_consistency
from agentic_testing.assertions.participants import assert_participants
from agentic_testing.assertions.security import assert_ended_incident_read_only, assert_route_protected
from agentic_testing.assertions.workflow import assert_join_flow
from agentic_testing.models import VerdictStatus


def test_primary_action_off_screen_fails() -> None:
    verdict = assert_visible_in_viewport("join", Rect(350, 10, 50, 30), (375, 667))
    assert verdict.status is VerdictStatus.FAIL


def test_marker_outside_epsilon_fails() -> None:
    verdict = assert_marker_position("drone-1", (19.076, 72.8777), (19.077, 72.8777), 25)
    assert verdict.status is VerdictStatus.FAIL


def test_wrong_video_identity_fails() -> None:
    verdict = assert_video_identity("drone-1", "stream-1", "stream-2")
    assert verdict.status is VerdictStatus.FAIL


def test_stale_data_shown_current_fails() -> None:
    verdict = assert_freshness(31, False, 30)
    assert verdict.status is VerdictStatus.FAIL


def test_protected_route_redirect_passes() -> None:
    verdict = assert_route_protected(
        authenticated=False,
        current_url="https://test.invalid/login",
        protected_path="/dashboard",
        login_path="/login",
    )
    assert verdict.status is VerdictStatus.PASS


def test_ended_incident_controls_fail() -> None:
    verdict = assert_ended_incident_read_only(incident_ended=True, interactive_controls=1)
    assert verdict.status is VerdictStatus.FAIL


def test_join_no_op_fails() -> None:
    assert assert_join_flow(action_count=1, reached_dashboard=False).status is VerdictStatus.FAIL


def test_stale_participant_list_fails() -> None:
    assert assert_participants(["ada", "lin"], ["ada"]).status is VerdictStatus.FAIL


def test_cross_wired_device_panel_fails() -> None:
    verdict = assert_selected_device_consistency("drone-1", "drone-1", "drone-1", "drone-2")
    assert verdict.status is VerdictStatus.FAIL
