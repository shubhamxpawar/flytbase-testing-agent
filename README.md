# FlytBase Testing Agent

An evidence-backed Level 1 testing foundation for controllable drone and incident-response dashboards.

The project prefers deterministic oracle and geometry assertions over model judgement. Confirmed findings require a video artifact, and learned locators are isolated by target ID to prevent unsafe cross-application reuse.

## Current foundation

- Tier 0/1 assertions for state, security, responsive geometry, device consistency, map position, video identity, telemetry freshness, join flow, and participants
- Nine-mutation Level 1 calibration catalog with fixture and target scorecards
- Target-scoped locator persistence and validation
- Playwright scenario contexts configured for isolated video capture
- YAML target and capability templates

## Development

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/agentic-testing validate-config configs/target.example.yaml configs/capabilities.example.yaml
```

The current slice is intentionally deterministic-first. Browser fixture wiring, runner orchestration, and real FlytBase cockpit configuration are the next implementation milestones.
