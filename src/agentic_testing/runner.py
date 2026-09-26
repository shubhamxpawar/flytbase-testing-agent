"""End-to-end deterministic capability runner with mandatory evidence capture."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from .browser import (
    READINESS_TIMEOUT_MS,
    PlaywrightBrowserSession,
    PlaywrightScenario,
    wait_for_cockpit_operational,
    wait_for_socket_connected,
)
from .config import load_capabilities, load_target
from .models import Capability, Evidence, Finding, TargetConfig, Verdict, VerdictStatus
from .oracle import check_cockpit_page, read_live_oracle
from .planner import CapabilityPlan, plan_capability
from .reporting import preserve_video, write_finding, write_run_report
from .cockpit import evaluate_cockpit_capability


@dataclass(frozen=True)
class CapabilityArtifact:
    capability_id: str
    verdict: Verdict
    screenshot_path: Path
    video_path: Path
    oracle_path: Path
    attempts: int


class RunnerPreflightError(RuntimeError):
    """A clear, expected failure when the local cockpit is not ready."""


async def _evaluate(plan: CapabilityPlan, page: Any, oracle: dict[str, Any], target: TargetConfig) -> Verdict:
    """Run a check only when both sides of its oracle are configured and observable."""
    if not oracle.get("available"):
        return Verdict.uncertain(str(oracle.get("reason", "oracle is unavailable")))

    if plan.evaluator != "unsupported":
        return await evaluate_cockpit_capability(plan.evaluator, page, oracle, target)

    # The remaining stock capability goals describe functionality not exposed by
    # the cockpit's control API/DOM contract. Do not replace missing mappings with
    # text heuristics or a model judgement.
    return Verdict.uncertain(
        f"{plan.capability.id} has no configured source-backed UI-to-oracle mapping for evaluator {plan.evaluator}"
    )


async def _run_async(
    target_config_path: Path,
    capabilities_path: Path,
    artifacts_dir: Path,
    *,
    headless: bool,
    reuse_session: bool,
) -> dict[str, Any]:
    target = load_target(target_config_path)
    capabilities = load_capabilities(capabilities_path)
    run_id = f"run-{time.strftime('%Y%m%d-%H%M%S')}"

    # Fail before creating artifacts or launching Chromium when the local target
    # is stopped or is not the expected cockpit HTML application.
    cockpit_preflight = await check_cockpit_page(target)
    if not cockpit_preflight.get("available"):
        raise RunnerPreflightError(str(cockpit_preflight["reason"]))
    oracle_preflight = await read_live_oracle(target)
    if not oracle_preflight.get("available"):
        raise RunnerPreflightError(str(oracle_preflight.get("reason", "oracle is unavailable")))

    run_dir = artifacts_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    capability_records: list[dict[str, Any]] = []
    findings: list[Finding] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=headless,
            slow_mo=0 if headless else 250,
            timeout=READINESS_TIMEOUT_MS,
        )
        try:
            demo_session: PlaywrightBrowserSession | None = None
            if reuse_session:
                demo_session = await PlaywrightBrowserSession(
                    browser,
                    video_dir=run_dir / "demo-session-video",
                    viewport=(1440, 900),
                ).__aenter__()
            for capability in capabilities:
                plan = plan_capability(capability)
                capability_dir = run_dir / "capabilities" / capability.id
                raw_video_dir = capability_dir / "raw-video"
                attempts = 0
                final_verdict: Verdict | None = None
                screenshot_path: Path | None = None
                oracle_path: Path | None = None
                persisted_video: Path | None = None

                # `fail` is retried once from a new context. `uncertain` is
                # intentionally not retried because it is a missing mapping, not flake.
                for attempt in range(2):
                    attempts += 1
                    scenario_manager = (
                        demo_session.scenario(f"{capability.id}-attempt-{attempt + 1}")
                        if demo_session is not None
                        else PlaywrightScenario(
                            browser,
                            scenario_id=f"{capability.id}-attempt-{attempt + 1}",
                            video_dir=raw_video_dir,
                            viewport=(1440, 900),
                        )
                    )
                    async with scenario_manager as scenario:
                        assert scenario.page is not None
                        await scenario.page.goto(
                            target.base_url,
                            wait_until="domcontentloaded",
                            timeout=READINESS_TIMEOUT_MS,
                        )
                        await wait_for_socket_connected(scenario.page, timeout_ms=READINESS_TIMEOUT_MS)
                        await wait_for_cockpit_operational(scenario.page, timeout_ms=READINESS_TIMEOUT_MS)
                        oracle = await read_live_oracle(target)
                        try:
                            final_verdict = await _evaluate(plan, scenario.page, oracle, target)
                        except Exception as error:
                            # An evaluator defect must become inspectable
                            # evidence, not prevent every later capability
                            # from running or hide the browser state.
                            final_verdict = Verdict.failed(
                                f"{plan.evaluator} evaluator raised {type(error).__name__}: {error}"
                            )
                        if final_verdict.status is VerdictStatus.FAIL:
                            scenario.capture.mark_failure()
                        screenshot_path = capability_dir / f"attempt-{attempt + 1}.png"
                        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                        await scenario.page.screenshot(
                            path=str(screenshot_path),
                            full_page=True,
                            timeout=READINESS_TIMEOUT_MS,
                        )
                        oracle_path = capability_dir / f"attempt-{attempt + 1}-oracle.json"
                        oracle_path.write_text(json.dumps(oracle, indent=2, default=str) + "\n")

                    if scenario.capture.video_path is None:
                        raise RuntimeError(f"Playwright did not produce video for {capability.id}")
                    start_s, end_s = scenario.evidence_window()
                    attempt_video = preserve_video(
                        scenario.capture.video_path,
                        capability_dir / f"attempt-{attempt + 1}",
                        trim_start_s=start_s,
                        trim_end_s=end_s,
                    )
                    persisted_video = attempt_video
                    if final_verdict.status is not VerdictStatus.FAIL:
                        break

                assert final_verdict is not None and screenshot_path is not None and oracle_path is not None and persisted_video is not None
                artifact = CapabilityArtifact(capability.id, final_verdict, screenshot_path, persisted_video, oracle_path, attempts)
                record = {
                    "capability_id": capability.id,
                    "category": capability.category,
                    "goal": capability.goal,
                    "verdict": final_verdict.status.value,
                    "reason": final_verdict.reason,
                    "attempts": artifact.attempts,
                    "screenshot": str(artifact.screenshot_path),
                    "video": str(artifact.video_path),
                    "oracle_payload": str(artifact.oracle_path),
                }
                capability_records.append(record)
                if final_verdict.status is VerdictStatus.FAIL:
                    finding = Finding(
                        id=capability.id,
                        title=f"{capability.id}: {capability.goal}",
                        category=capability.category,
                        description=final_verdict.reason,
                        approach=f"Deterministic evaluator: {plan.evaluator}",
                        repro_steps=(f"Open {target.base_url}", "Wait for the cockpit to load"),
                        evidence=Evidence(
                            screenshot_path=artifact.screenshot_path,
                            video_path=artifact.video_path,
                            oracle_payload=json.loads(artifact.oracle_path.read_text()),
                        ),
                    )
                    findings.append(finding)
                    write_finding(finding, run_dir / "findings")
        finally:
            if "demo_session" in locals() and demo_session is not None:
                await demo_session.__aexit__(None, None, None)
            await browser.close(reason="capability run completed")

    summary = {
        "run_id": run_id,
        "target_id": target.target_id,
        "base_url": target.base_url,
        "status": "completed",
        "findings": [finding.id for finding in findings],
        "finding_count": len(findings),
        "capabilities": capability_records,
    }
    write_run_report(summary, run_dir)
    return {"run_dir": str(run_dir), "summary": summary}


def run_capabilities(
    target_config_path: str | Path,
    capabilities_path: str | Path,
    artifacts_dir: str | Path,
    headless: bool = False,
    reuse_session: bool = False,
) -> dict[str, Any]:
    """Run all capability checks and return the persisted report summary.

    Findings are test results, not runner failures. Exceptions are reserved for
    missing prerequisites or incomplete evidence.
    """
    return asyncio.run(
        _run_async(
            Path(target_config_path),
            Path(capabilities_path),
            Path(artifacts_dir),
            headless=headless,
            reuse_session=reuse_session,
        )
    )
