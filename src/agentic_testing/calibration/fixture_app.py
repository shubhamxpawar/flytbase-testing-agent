"""In-memory fixture state used to exercise mutation contracts before target wiring.

The browser-facing fixture server will expose this state in a later integration slice;
keeping mutation state separate makes every mutation reversible and unit-testable now.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .mutations import MUTATIONS


@dataclass(frozen=True)
class FixtureState:
    primary_action_visible: bool = True
    primary_action_offscreen: bool = False
    join_reaches_dashboard: bool = True
    telemetry_current: bool = True
    status_online: bool = True
    marker_offset_m: float = 0.0
    video_matches_selected_device: bool = True
    auth_guard_enabled: bool = True
    ended_incident_editable: bool = False
    participant_list_current: bool = True

    @classmethod
    def healthy(cls) -> "FixtureState":
        return cls()

    def apply(self, mutation_id: str) -> "FixtureState":
        if mutation_id not in {mutation.id for mutation in MUTATIONS}:
            raise ValueError(f"unknown mutation {mutation_id}")
        overrides = {
            "M1": {"primary_action_visible": False},
            "M2": {"primary_action_offscreen": True},
            "M3": {"join_reaches_dashboard": False},
            "M4": {"telemetry_current": False, "status_online": True},
            "M5": {"marker_offset_m": 500.0},
            "M6": {"video_matches_selected_device": False},
            "M7": {"auth_guard_enabled": False},
            "M8": {"ended_incident_editable": True},
            "M9": {"participant_list_current": False},
        }
        return replace(self, **overrides[mutation_id])
