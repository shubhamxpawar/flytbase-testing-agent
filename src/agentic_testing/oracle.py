"""Normalization helpers for source-of-truth telemetry and participant payloads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

import httpx

from .models import TargetConfig


# Preflight should fail fast when a local dev server is stopped. The 30-second
# browser timeout is intentionally separate and applies after this succeeds.
REQUEST_TIMEOUT_S = 5.0


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


async def read_live_oracle(target: TargetConfig) -> dict[str, Any]:
    """Read the control-plane state used as evidence for a browser scenario."""
    if target.control_api_base_url is None:
        return {"available": False, "reason": "target has no control_api_base_url"}
    base_url = target.control_api_base_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
            health_response = await client.get(f"{base_url}/health")
            health_response.raise_for_status()
            devices_response = await client.get(f"{base_url}/devices")
            devices_response.raise_for_status()
    except httpx.HTTPError as error:
        return {
            "available": False,
            "reason": (
                f"FlytBase control API is unavailable at {base_url}: {error}. "
                "Start the cockpit with `npm run dev` before running the agent."
            ),
        }
    return {
        "available": True,
        "health": health_response.json(),
        "devices": devices_response.json(),
    }


async def check_cockpit_page(target: TargetConfig) -> dict[str, Any]:
    """Confirm that the browser target is a reachable HTML cockpit before launch."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S, follow_redirects=True) as client:
            response = await client.get(target.base_url)
            response.raise_for_status()
    except httpx.HTTPError as error:
        return {
            "available": False,
            "reason": (
                f"FlytBase cockpit is unavailable at {target.base_url}: {error}. "
                "Start the cockpit with `npm run dev` before running the agent."
            ),
        }
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type.lower():
        return {
            "available": False,
            "reason": f"FlytBase cockpit at {target.base_url} returned {content_type or 'no content type'}, not HTML.",
        }
    return {"available": True, "status_code": response.status_code, "content_type": content_type}
