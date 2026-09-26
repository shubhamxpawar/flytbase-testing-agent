"""Deterministic capability planning for known Level 1 goal categories."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Capability


@dataclass(frozen=True)
class CapabilityPlan:
    capability: Capability
    evaluator: str


_EVALUATORS = {
    # These are Cockpit product capabilities, not a generic incident-app
    # checklist. Each evaluator has a source-verified DOM contract.
    "C1": "connection_state",
    "C2": "device_selection",
    "C3": "map_view_toggle",
    "C4": "responsive_controls",
    "C5": "telemetry_state",
    "C6": "video_selection",
    "C7": "interactive_surface",
    "R1": "authentication_required",
    "C8": "control_panel_popup",
}


def plan_capability(capability: Capability) -> CapabilityPlan:
    """Map an outcome goal to a deterministic evaluator, never to selectors."""
    return CapabilityPlan(capability, _EVALUATORS.get(capability.id, "unsupported"))
