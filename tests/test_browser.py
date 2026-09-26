import asyncio

import pytest

from agentic_testing.browser import SOCKET_CONNECTED_SELECTOR, wait_for_socket_connected


class _ReadyPage:
    def __init__(self) -> None:
        self.args = None

    async def wait_for_selector(self, selector: str, *, state: str, timeout: int) -> None:
        self.args = (selector, state, timeout)


class _TimeoutPage:
    async def wait_for_selector(self, selector: str, *, state: str, timeout: int) -> None:
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        raise PlaywrightTimeoutError("timed out")


def test_socket_readiness_uses_source_backed_selector_and_explicit_timeout() -> None:
    page = _ReadyPage()
    asyncio.run(wait_for_socket_connected(page, timeout_ms=15_000))
    assert page.args == (SOCKET_CONNECTED_SELECTOR, "visible", 15_000)


def test_socket_readiness_raises_clear_timeout_error() -> None:
    with pytest.raises(TimeoutError, match="Cockpit socket readiness timed out after 15s"):
        asyncio.run(wait_for_socket_connected(_TimeoutPage(), timeout_ms=15_000))
