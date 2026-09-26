"""YAML configuration loading with a small dependency boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import Capability, TargetConfig


def _yaml_load(path: Path) -> Any:
    try:
        import yaml
    except ImportError as error:  # pragma: no cover - exercised in deployed installation
        raise RuntimeError("PyYAML is required to load configuration; install project dependencies") from error
    return yaml.safe_load(path.read_text())


def load_target(path: Path) -> TargetConfig:
    raw = _yaml_load(path) or {}
    return TargetConfig(
        target_id=raw["target_id"],
        base_url=raw["base_url"],
        map_position_epsilon_m=float(raw.get("map_position_epsilon_m", 25)),
        freshness_threshold_s=float(raw.get("freshness_threshold_s", 30)),
        control_api_base_url=raw.get("control_api_base_url"),
        websocket_url=raw.get("websocket_url"),
        socket_transport=raw.get("socket_transport"),
        socket_namespace=raw.get("socket_namespace"),
        socket_org_id=raw.get("socket_org_id"),
        whep_base_url=raw.get("whep_base_url"),
        video_player_testid=raw.get("video_player_testid"),
        video_stream_payload_path=raw.get("video_stream_payload_path"),
    )


def load_capabilities(path: Path) -> list[Capability]:
    raw = _yaml_load(path) or []
    return [Capability(id=item["id"], goal=item["goal"], category=item["category"]) for item in raw]
