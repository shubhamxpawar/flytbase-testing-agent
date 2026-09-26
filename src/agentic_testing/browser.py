"""Playwright scenario contexts with mandatory, isolated video capture."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError


# A local app needs enough time to start its socket connection without making a
# stuck run wait indefinitely. All Playwright operations use this same bound.
READINESS_TIMEOUT_MS = 30_000
SOCKET_CONNECTED_SELECTOR = '[data-testid="socket-status"]:has-text("socket connected")'


async def wait_for_socket_connected(page: Any, *, timeout_ms: int = READINESS_TIMEOUT_MS) -> None:
    """Wait for the cockpit's source-backed Socket.IO readiness badge.

    `frontend/src/components/SocketBadge.tsx` renders the element as
    `data-testid="socket-status"` with text `socket connected` once the
    Socket.IO client is ready. This deliberately avoids `networkidle`, because
    the cockpit maintains a long-lived socket connection.
    """
    try:
        await page.wait_for_selector(
            SOCKET_CONNECTED_SELECTOR,
            state="visible",
            timeout=timeout_ms,
        )
    except PlaywrightTimeoutError as error:
        raise TimeoutError(
            f"Cockpit socket readiness timed out after {timeout_ms / 1000:.0f}s: "
            f"expected visible {SOCKET_CONNECTED_SELECTOR}"
        ) from error


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


class PlaywrightBrowserSession:
    """One visible context for demos, with a separately recorded tab per scenario."""

    def __init__(self, browser: Any, *, video_dir: Path, viewport: tuple[int, int]) -> None:
        self._browser = browser
        self._video_dir = video_dir
        self._viewport = viewport
        self.context: Any | None = None

    async def __aenter__(self) -> "PlaywrightBrowserSession":
        self._video_dir.mkdir(parents=True, exist_ok=True)
        self.context = await self._browser.new_context(
            viewport={"width": self._viewport[0], "height": self._viewport[1]},
            record_video_dir=str(self._video_dir),
        )
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.context is not None:
            await self.context.close(reason="demo session completed")

    def scenario(self, scenario_id: str) -> "PlaywrightSessionScenario":
        if self.context is None:
            raise RuntimeError("demo browser session is not open")
        return PlaywrightSessionScenario(self.context, scenario_id)


class PlaywrightSessionScenario:
    """A per-capability tab within a persistent demo browser context."""

    def __init__(self, context: Any, scenario_id: str) -> None:
        self._context = context
        self.capture = ScenarioVideo(scenario_id)
        self.page: Any | None = None

    async def __aenter__(self) -> "PlaywrightSessionScenario":
        self.page = await self._context.new_page()
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.page is not None and self.page.video is not None:
            video = self.page.video
            await self.page.close(reason="capability evidence captured")
            self.capture.video_path = Path(await video.path())
        elif self.page is not None:
            await self.page.close(reason="capability scenario completed")
        self.capture.ended_at = time.time()

    def evidence_window(self, lead_in_s: float = 3.0) -> tuple[float, float]:
        end = (self.capture.ended_at or time.time()) - self.capture.started_at
        failure = self.capture.failure_at or self.capture.started_at
        start = max(0.0, failure - self.capture.started_at - lead_in_s)
        return start, max(start, end)
