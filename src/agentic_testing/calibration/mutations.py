"""Level 1 reversible mutation catalog used by fixture and target adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Mutation:
    id: str
    category: str
    goal_id: str
    description: str


MUTATIONS: tuple[Mutation, ...] = (
    Mutation("M1", "visual", "G9", "Hide required primary action"),
    Mutation("M2", "responsive", "G6", "Move primary action off-screen at 375px"),
    Mutation("M3", "functional", "G2", "Make join action a no-op"),
    Mutation("M4", "api-data", "G4,G7", "Freeze telemetry while UI remains current/online"),
    Mutation("M5", "map-geospatial", "G10", "Offset rendered map marker from telemetry"),
    Mutation("M6", "video-media", "G5", "Bind selected device to another device's stream"),
    Mutation("M7", "security", "G1", "Remove unauthenticated-route guard"),
    Mutation("M8", "security", "G8", "Leave edit controls reachable after incident ends"),
    Mutation("M9", "state-persistence", "G3", "Reload with stale participant list"),
)
