"""Normalization helpers for source-of-truth telemetry and participant payloads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class DeviceTruth:
    device_id: str
    connected: bool | None
    latitude: float | None
    longitude: float | None
    stream_identity: str | None
    observed_at: datetime | None


def normalize_device(payload: Mapping[str, Any]) -> DeviceTruth:
    """Normalize common target field aliases without inventing absent truth."""
    timestamp = payload.get("received_at") or payload.get("timestamp") or payload.get("observed_at")
    observed_at = None
    if isinstance(timestamp, str):
        observed_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(timezone.utc)
    return DeviceTruth(
        device_id=str(payload["device_id"] if "device_id" in payload else payload["id"]),
        connected=payload.get("connected", payload.get("online")),
        latitude=_as_float(payload.get("latitude", payload.get("lat"))),
        longitude=_as_float(payload.get("longitude", payload.get("lon"))),
        stream_identity=payload.get("stream_identity", payload.get("stream_id")),
        observed_at=observed_at,
    )


def _as_float(value: Any) -> float | None:
    return None if value is None else float(value)
