"""Data-only snapshot primitives, kept separate from assertions for testability."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class RenderedDeviceState:
    device_id: str | None
    connected: bool | None
    marker_position: tuple[float, float] | None
    video_stream_identity: str | None
    freshness_is_stale: bool | None


@dataclass(frozen=True)
class StateSnapshot:
    screenshot_path: Path | None
    rendered: RenderedDeviceState
    oracle_payload: Mapping[str, Any]
    accessibility_tree: Mapping[str, Any] | None = None
