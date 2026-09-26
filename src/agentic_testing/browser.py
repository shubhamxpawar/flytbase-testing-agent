"""Playwright scenario contexts with mandatory, isolated video capture."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ScenarioVideo:
    """Lifecycle state for one scenario or retry attempt."""

    scenario_id: str
    started_at: float = field(default_factory=time.time)
    failure_at: float | None = None
    ended_at: float | None = None
    video_path: Path | None = None

    def mark_failure(self) -> None:
        self.failure_at = time.time()


class PlaywrightScenario:
    """An isolated Playwright context which always flushes a scenario video.

    The context owns one page. Creating a new instance for a retry prevents cookies,
    DOM state, and video artifacts from leaking across attempts.
    """

    def __init__(
        self,
        browser: Any,
        *,
        scenario_id: str,
        video_dir: Path,
        viewport: tuple[int, int],
    ) -> None:
        self._browser = browser
        self._video_dir = video_dir
        self._viewport = viewport
        self.capture = ScenarioVideo(scenario_id)
        self.context: Any | None = None
        self.page: Any | None = None

    async def __aenter__(self) -> "PlaywrightScenario":
        self._video_dir.mkdir(parents=True, exist_ok=True)
        self.context = await self._browser.new_context(
            viewport={"width": self._viewport[0], "height": self._viewport[1]},
            record_video_dir=str(self._video_dir),
        )
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.page is not None and self.page.video is not None:
            # Playwright makes the final path available after context closure.
            video = self.page.video
            await self.context.close()
            self.capture.video_path = Path(await video.path())
        elif self.context is not None:
            await self.context.close()
        self.capture.ended_at = time.time()

    def evidence_window(self, lead_in_s: float = 3.0) -> tuple[float, float]:
        """Return seconds relative to scenario start for video trimming."""
        end = (self.capture.ended_at or time.time()) - self.capture.started_at
        failure = self.capture.failure_at or self.capture.started_at
        start = max(0.0, failure - self.capture.started_at - lead_in_s)
        return start, max(start, end)
