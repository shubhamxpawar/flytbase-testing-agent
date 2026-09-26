"""Basic auth-gating and read-only assertions."""

from __future__ import annotations

from ..models import Verdict


def assert_route_protected(*, authenticated: bool, current_url: str, protected_path: str, login_path: str) -> Verdict:
    if authenticated:
        return Verdict.uncertain("auth-gate assertion requires an unauthenticated browser context")
    if current_url.rstrip("/").endswith(login_path.rstrip("/")):
        return Verdict.passed(f"unauthenticated navigation to {protected_path} redirects to login")
    return Verdict.failed(f"unauthenticated navigation reached protected route {current_url}")


def assert_ended_incident_read_only(*, incident_ended: bool | None, interactive_controls: int | None) -> Verdict:
    if incident_ended is None or interactive_controls is None:
        return Verdict.uncertain("ended state or interactive-control count is unavailable")
    if not incident_ended:
        return Verdict.uncertain("incident is not ended; read-only assertion is not applicable")
    if interactive_controls == 0:
        return Verdict.passed("ended incident exposes no interactive controls")
    return Verdict.failed(f"ended incident exposes {interactive_controls} interactive control(s)")
