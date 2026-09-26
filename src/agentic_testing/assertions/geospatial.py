"""Compare rendered map positions to telemetry using great-circle distance."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from ..models import Verdict


def distance_meters(left: tuple[float, float], right: tuple[float, float]) -> float:
    """Return great-circle distance for `(latitude, longitude)` pairs."""
    lat1, lon1, lat2, lon2 = map(radians, (*left, *right))
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    haversine = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 6_371_000 * 2 * asin(sqrt(haversine))


def assert_marker_position(
    device_id: str,
    telemetry_position: tuple[float, float] | None,
    marker_position: tuple[float, float] | None,
    epsilon_m: float,
) -> Verdict:
    if telemetry_position is None or marker_position is None:
        return Verdict.uncertain(f"map or telemetry position for {device_id} is unavailable")
    distance = distance_meters(telemetry_position, marker_position)
    if distance <= epsilon_m:
        return Verdict.passed(f"{device_id} marker is {distance:.1f}m from telemetry position")
    return Verdict.failed(
        f"{device_id} marker is {distance:.1f}m from telemetry position; tolerance is {epsilon_m:.1f}m"
    )
