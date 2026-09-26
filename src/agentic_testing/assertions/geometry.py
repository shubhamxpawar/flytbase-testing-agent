"""Viewport and clipping checks that do not depend on model judgement."""

from __future__ import annotations

from dataclasses import dataclass

from ..models import Verdict


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float


def assert_visible_in_viewport(
    label: str,
    rect: Rect | None,
    viewport: tuple[int, int],
    *,
    visible: bool = True,
    enabled: bool = True,
) -> Verdict:
    if rect is None:
        return Verdict.uncertain(f"{label} has no bounding rectangle")
    if not visible or not enabled:
        return Verdict.failed(f"{label} is present but not operable")
    width, height = viewport
    if rect.width <= 0 or rect.height <= 0:
        return Verdict.failed(f"{label} has no visible area")
    if rect.x < 0 or rect.y < 0 or rect.x + rect.width > width or rect.y + rect.height > height:
        return Verdict.failed(f"{label} is clipped or off-screen at {width}x{height}")
    return Verdict.passed(f"{label} is visible and operable at {width}x{height}")
