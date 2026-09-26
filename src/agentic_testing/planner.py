"""Deterministic capability planning for known Level 1 goal categories."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Capability


@dataclass(frozen=True)
class CapabilityPlan:
    capability: Capability
    evaluator: str


_EVALUATORS = {
    "G1": "auth_gate",
    "G2": "join_flow",
    "G3": "participants",
    "G4": "connection_state",
    "G5": "selected_device_media",
    "G6": "responsive_primary_action",
    "G7": "freshness",
    "G8": "ended_incident_read_only",
    "G9": "required_controls",
    "G10": "map_position",
}


def plan_capability(capability: Capability) -> CapabilityPlan:
    """Map an outcome goal to a deterministic evaluator, never to selectors."""
    return CapabilityPlan(capability, _EVALUATORS.get(capability.id, "unsupported"))
