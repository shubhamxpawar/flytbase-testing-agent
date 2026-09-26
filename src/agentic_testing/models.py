"""Stable domain types shared by orchestration, assertions, and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping


class VerdictStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class Verdict:
    status: VerdictStatus
    reason: str
    evidence_refs: tuple[str, ...] = ()

    @classmethod
    def passed(cls, reason: str, *evidence_refs: str) -> "Verdict":
        return cls(VerdictStatus.PASS, reason, evidence_refs)

    @classmethod
    def failed(cls, reason: str, *evidence_refs: str) -> "Verdict":
        return cls(VerdictStatus.FAIL, reason, evidence_refs)

    @classmethod
    def uncertain(cls, reason: str, *evidence_refs: str) -> "Verdict":
        return cls(VerdictStatus.UNCERTAIN, reason, evidence_refs)


@dataclass(frozen=True)
class Capability:
    id: str
    goal: str
    category: str


@dataclass(frozen=True)
class TargetConfig:
    """Target-specific, non-secret assertion and integration configuration."""

    target_id: str
    base_url: str
    map_position_epsilon_m: float = 25.0
    freshness_threshold_s: float = 30.0
    control_api_base_url: str | None = None
    websocket_url: str | None = None
    socket_transport: str | None = None
    socket_namespace: str | None = None
    socket_org_id: str | None = None
    whep_base_url: str | None = None
    video_player_testid: str | None = None
    video_stream_payload_path: str | None = None

    def __post_init__(self) -> None:
        if not self.target_id.strip():
            raise ValueError("target_id is required for locator isolation")
        if self.map_position_epsilon_m < 0:
            raise ValueError("map_position_epsilon_m must be non-negative")
        if self.freshness_threshold_s < 0:
            raise ValueError("freshness_threshold_s must be non-negative")


@dataclass(frozen=True)
class LocatorKey:
    target_id: str
    page_identity: str
    element_intent: str


@dataclass(frozen=True)
class LocatorRecord:
    key: LocatorKey
    strategy: str
    value: str
    expected_role: str | None = None
    expected_name: str | None = None
    viewport: tuple[int, int] | None = None
    version: int = 1


@dataclass(frozen=True)
class Evidence:
    screenshot_path: Path | None = None
    video_path: Path | None = None
    oracle_payload: Mapping[str, Any] | None = None
    extra_paths: tuple[Path, ...] = ()


@dataclass(frozen=True)
class Finding:
    id: str
    title: str
    category: str
    description: str
    approach: str
    repro_steps: tuple[str, ...]
    evidence: Evidence

    def __post_init__(self) -> None:
        if self.evidence.video_path is None:
            raise ValueError("confirmed findings require a video artifact")


@dataclass(frozen=True)
class CalibrationResult:
    name: str
    category: str
    expected_finding: bool
    observed_finding: bool
    target_kind: str
    artifact_paths: tuple[Path, ...] = ()


@dataclass
class RunResult:
    target_id: str
    findings: list[Finding] = field(default_factory=list)
    calibration: list[CalibrationResult] = field(default_factory=list)
