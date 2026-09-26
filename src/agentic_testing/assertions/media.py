"""Validate that an active video stream belongs to the selected device."""

from __future__ import annotations

from ..models import Verdict


def assert_video_identity(
    selected_device_id: str | None,
    oracle_stream_identity: str | None,
    rendered_stream_identity: str | None,
) -> Verdict:
    if not selected_device_id or not oracle_stream_identity or not rendered_stream_identity:
        return Verdict.uncertain("selected device or video stream identity is unavailable")
    if oracle_stream_identity == rendered_stream_identity:
        return Verdict.passed(f"active video belongs to selected device {selected_device_id}")
    return Verdict.failed(
        f"selected device {selected_device_id} expects stream {oracle_stream_identity!r}, "
        f"but UI renders {rendered_stream_identity!r}"
    )
