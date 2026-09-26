"""Cross-panel identity checks for a selected device."""

from __future__ import annotations

from ..models import Verdict


def assert_selected_device_consistency(
    selected_device_id: str | None,
    telemetry_device_id: str | None,
    map_device_id: str | None,
    video_device_id: str | None,
) -> Verdict:
    values = (selected_device_id, telemetry_device_id, map_device_id, video_device_id)
    if any(value is None for value in values):
        return Verdict.uncertain("selected-device identity is unavailable in one or more panels")
    if len(set(values)) == 1:
        return Verdict.passed(f"telemetry, map, and video all identify {selected_device_id}")
    return Verdict.failed(
        f"selected={selected_device_id!r}, telemetry={telemetry_device_id!r}, "
        f"map={map_device_id!r}, video={video_device_id!r}"
    )
