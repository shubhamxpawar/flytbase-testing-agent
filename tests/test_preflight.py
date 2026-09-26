import asyncio

from agentic_testing.browser import READINESS_TIMEOUT_MS
from agentic_testing.models import TargetConfig
from agentic_testing.oracle import check_cockpit_page, read_live_oracle


def test_default_browser_timeout_is_at_least_thirty_seconds() -> None:
    assert READINESS_TIMEOUT_MS >= 30_000


def test_stopped_cockpit_returns_clear_preflight_result() -> None:
    target = TargetConfig("offline", "http://127.0.0.1:9", control_api_base_url="http://127.0.0.1:9/api")
    page_result = asyncio.run(check_cockpit_page(target))
    oracle_result = asyncio.run(read_live_oracle(target))
    assert page_result["available"] is False
    assert oracle_result["available"] is False
    assert "Start the cockpit with `npm run dev`" in page_result["reason"]
    assert "Start the cockpit with `npm run dev`" in oracle_result["reason"]
