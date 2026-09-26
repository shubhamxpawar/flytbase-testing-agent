from pathlib import Path

from agentic_testing.locators import LocatorMap
from agentic_testing.models import LocatorKey, LocatorRecord


def test_locator_map_never_crosses_target_boundaries(tmp_path: Path) -> None:
    locator_map = LocatorMap(tmp_path / "locators.json")
    cockpit = LocatorKey("cockpit", "dashboard", "primary-action")
    application = LocatorKey("incident-app", "dashboard", "primary-action")
    locator_map.put(LocatorRecord(cockpit, "role", "Join", "button", "Join"))
    assert locator_map.get(application) is None
    assert locator_map.get(cockpit) is not None


def test_cached_locator_requires_matching_intent() -> None:
    record = LocatorRecord(LocatorKey("target", "page", "join"), "role", "Join", "button", "Join")
    assert LocatorMap.matches_intent(record, role="button", name="Join")
    assert not LocatorMap.matches_intent(record, role="button", name="Delete")


def test_viewport_specific_locator_is_not_reused() -> None:
    locator_map = LocatorMap(Path("/tmp/unused-locator-map.json"))
    key = LocatorKey("target", "page", "join")
    locator_map.put(LocatorRecord(key, "bbox", "100,100", viewport=(375, 667)))
    assert locator_map.get(key, viewport=(1440, 900)) is None
