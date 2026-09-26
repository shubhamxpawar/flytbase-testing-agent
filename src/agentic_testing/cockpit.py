"""Source-backed browser journeys for the FlytBase Cockpit target.

This adapter intentionally performs only interactions that the Cockpit source
defines as safe: selecting a device and switching the map view.  It never
guesses selectors from labels or clicks operational controls.
"""

from __future__ import annotations

from typing import Any

from .assertions.geometry import Rect, assert_visible_in_viewport
from .assertions.state import assert_state_equal
from .models import TargetConfig, Verdict, VerdictStatus


ACTION_TIMEOUT_MS = 5_000
MAP_LOAD_TIMEOUT_MS = 30_000


def _failed_or_uncertain(verdicts: list[Verdict]) -> Verdict:
    failures = [item.reason for item in verdicts if item.status is VerdictStatus.FAIL]
    if failures:
        return Verdict.failed("; ".join(failures))
    uncertain = [item.reason for item in verdicts if item.status is VerdictStatus.UNCERTAIN]
    if uncertain:
        return Verdict.uncertain("; ".join(uncertain))
    return Verdict.passed("; ".join(item.reason for item in verdicts))


async def _select_nondefault_drone(
    page: Any, oracle: dict[str, Any], *, preferred_index: int = 1
) -> tuple[str | None, str | None]:
    devices = oracle.get("devices", {}).get("devices", [])
    drones = [device for device in devices if isinstance(device, dict) and device.get("type") == "drone"]
    if not drones:
        return None, None
    chosen = drones[min(preferred_index, len(drones) - 1)]
    device_id, name = chosen.get("id"), chosen.get("name")
    if not isinstance(device_id, str) or not isinstance(name, str):
        return None, None
    row = page.get_by_test_id(f"device-row-{device_id}")
    await row.click(timeout=ACTION_TIMEOUT_MS)
    await row.wait_for(state="visible", timeout=ACTION_TIMEOUT_MS)
    return device_id, name


async def _visible_rect(page: Any, test_id: str) -> tuple[Rect | None, bool]:
    locator = page.get_by_test_id(test_id)
    try:
        await locator.wait_for(state="visible", timeout=ACTION_TIMEOUT_MS)
        box = await locator.bounding_box(timeout=ACTION_TIMEOUT_MS)
        visible = await locator.is_visible(timeout=ACTION_TIMEOUT_MS)
    except Exception:
        return None, False
    if box is None:
        return None, visible
    return Rect(box["x"], box["y"], box["width"], box["height"]), visible


async def _wait_for_map_controls(page: Any) -> None:
    """Wait for the lazy Cesium component to attach its source-defined controls."""
    await page.get_by_test_id("map-view-2d").wait_for(state="attached", timeout=MAP_LOAD_TIMEOUT_MS)
    await page.get_by_test_id("map-view-3d").wait_for(state="attached", timeout=MAP_LOAD_TIMEOUT_MS)


async def evaluate_cockpit_capability(
    evaluator: str, page: Any, oracle: dict[str, Any], target: TargetConfig
) -> Verdict:
    """Exercise a capability-specific Cockpit journey and evaluate its result."""
    if evaluator == "connection_state":
        badge = page.get_by_test_id("socket-status")
        try:
            text = (await badge.inner_text(timeout=ACTION_TIMEOUT_MS)).lower()
        except Exception:
            return Verdict.uncertain("socket-status test id is unavailable in the rendered UI")
        simulator = oracle.get("health", {}).get("simulator")
        if simulator != "connected":
            return Verdict.uncertain("control API does not report a connected simulator")
        return Verdict.passed("backend simulator and rendered Socket.IO badge are connected") if (
            "connected" in text and "disconnected" not in text
        ) else Verdict.failed(f"backend simulator is connected but UI badge reads {text!r}")

    if evaluator == "device_selection":
        device_id, name = await _select_nondefault_drone(page, oracle)
        if device_id is None or name is None:
            return Verdict.uncertain("control API exposes no selectable drone")
        row = page.get_by_test_id(f"device-row-{device_id}")
        telemetry_title = page.get_by_text(f"Drone Telemetry · {name}", exact=True)
        await telemetry_title.wait_for(
            state="visible", timeout=ACTION_TIMEOUT_MS
        )
        row_class = await row.get_attribute("class", timeout=ACTION_TIMEOUT_MS)
        telemetry_matches = await telemetry_title.is_visible(timeout=ACTION_TIMEOUT_MS)
        video_header = await page.locator(".video-header").inner_text(timeout=ACTION_TIMEOUT_MS)
        return _failed_or_uncertain(
            [
                assert_state_equal("selected device row", True, "selected" in (row_class or "")),
                # The exact-text locator above is the rendered UI observation;
                # reusing its visibility avoids text-transform casing effects.
                assert_state_equal("telemetry panel device", True, telemetry_matches),
                assert_state_equal("video panel device", True, name in video_header),
            ]
        )

    if evaluator == "map_view_toggle":
        map_2d, map_3d = page.get_by_test_id("map-view-2d"), page.get_by_test_id("map-view-3d")
        await _wait_for_map_controls(page)
        # Cesium continuously repaints its sibling canvas, which means its map
        # controls do not remain "stable" long enough for Playwright's default
        # actionability wait. The buttons themselves are source-defined and
        # visible, so dispatch the user click without that unrelated stability
        # gate.
        await map_2d.dispatch_event("click", timeout=ACTION_TIMEOUT_MS)
        pressed_2d = await map_2d.get_attribute("aria-pressed", timeout=ACTION_TIMEOUT_MS)
        await map_3d.dispatch_event("click", timeout=ACTION_TIMEOUT_MS)
        pressed_3d = await map_3d.get_attribute("aria-pressed", timeout=ACTION_TIMEOUT_MS)
        canvas, visible = await _visible_rect(page, "map-canvas")
        return _failed_or_uncertain(
            [
                assert_state_equal("2D map selection", "true", pressed_2d),
                assert_state_equal("3D map selection", "true", pressed_3d),
                assert_visible_in_viewport("map canvas", canvas, (1440, 900), visible=visible),
            ]
        )

    if evaluator == "responsive_controls":
        await _wait_for_map_controls(page)
        await page.set_viewport_size({"width": 375, "height": 812})
        checks: list[Verdict] = []
        for test_id in ("socket-status", "map-view-2d", "map-view-3d"):
            rect, visible = await _visible_rect(page, test_id)
            checks.append(assert_visible_in_viewport(test_id, rect, (375, 812), visible=visible))
        link = page.locator("a.dashboard-link")
        try:
            await link.wait_for(state="visible", timeout=ACTION_TIMEOUT_MS)
            box = await link.bounding_box(timeout=ACTION_TIMEOUT_MS)
            visible = await link.is_visible(timeout=ACTION_TIMEOUT_MS)
            rect = None if box is None else Rect(box["x"], box["y"], box["width"], box["height"])
        except Exception:
            rect, visible = None, False
        checks.append(assert_visible_in_viewport("control panel link", rect, (375, 812), visible=visible))
        return _failed_or_uncertain(checks)

    if evaluator == "telemetry_state":
        device_id, name = await _select_nondefault_drone(page, oracle)
        if device_id is None or name is None:
            return Verdict.uncertain("control API exposes no selectable drone")
        drone = oracle.get("state", {}).get("drones", {}).get(device_id)
        if not isinstance(drone, dict):
            return Verdict.uncertain(f"control state contains no telemetry snapshot for {device_id}")
        battery = await page.get_by_test_id("telemetry-battery").inner_text(timeout=ACTION_TIMEOUT_MS)
        flight = await page.get_by_test_id("status-flight").inner_text(timeout=ACTION_TIMEOUT_MS)
        expected_battery = f"{float(drone['battery']):.0f} %"
        return _failed_or_uncertain(
            [
                assert_state_equal("battery telemetry", expected_battery, battery),
                assert_state_equal("flight status telemetry", drone.get("status"), flight),
            ]
        )

    if evaluator == "video_selection":
        _, name = await _select_nondefault_drone(page, oracle, preferred_index=2)
        if name is None:
            return Verdict.uncertain("control API exposes no selectable drone")
        header = await page.locator(".video-header").inner_text(timeout=ACTION_TIMEOUT_MS)
        state = await page.get_by_test_id("video-state").inner_text(timeout=ACTION_TIMEOUT_MS)
        player, visible = await _visible_rect(page, target.video_player_testid or "video-player")
        return _failed_or_uncertain(
            [
                assert_state_equal("video selected device", name, name if name in header else None),
                assert_state_equal("video state label", True, bool(state.strip())),
                assert_visible_in_viewport("video player", player, (1440, 900), visible=visible),
            ]
        )

    if evaluator == "interactive_surface":
        # Inventory is captured from the live DOM; every listed item must be
        # visible, have a usable rectangle, and not be an inert named control.
        # Select a different device before inventorying the current surface so
        # this evidence records an actual user journey. The dedicated map-mode
        # capability owns lazy Cesium readiness and reports map defects.
        device_id, _ = await _select_nondefault_drone(page, oracle, preferred_index=3)
        if device_id is None:
            return Verdict.uncertain("control API exposes no selectable drone")
        await _wait_for_map_controls(page)
        # Limit the audit to Cockpit-owned controls. Cesium contributes its own
        # attribution and accessibility controls, whose disabled/hidden state
        # is not an application defect and is covered by Cesium itself.
        items = await page.locator("a.dashboard-link, button[data-testid], [role='button'][data-testid]").evaluate_all(
            "els => els.map(el => ({tag: el.tagName, text: (el.textContent || '').trim(), disabled: el.matches(':disabled'), rect: el.getBoundingClientRect().toJSON()}))"
        )
        if not items:
            return Verdict.failed("Cockpit exposes no interactive controls")
        broken = [
            item["text"] or item["tag"]
            for item in items
            if item["disabled"] or item["rect"]["width"] <= 0 or item["rect"]["height"] <= 0
        ]
        if broken:
            return Verdict.failed(f"inert or invisible interactive controls: {', '.join(broken)}")
        return Verdict.passed(f"audited {len(items)} live interactive controls")

    return Verdict.uncertain(f"no Cockpit evaluator is implemented for {evaluator}")
