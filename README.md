# FlytBase Testing Agent

An evidence-backed, deterministic-first testing agent for FlytBase Cockpit and other controllable web systems. It turns outcome-level product goals into browser scenarios, prefers application ground truth over visual guesses, and preserves screenshots, oracle payloads, and Playwright video for every executed capability.

## Why this exists

Screenshot-only testing is noisy: it can confuse expected loading states with bugs and cannot prove whether a UI reflects the application’s real state. This project uses a tiered approach:

1. **Tier 0 — oracle-backed checks:** compare UI state with a control API or live telemetry source.
2. **Tier 1 — deterministic browser checks:** validate presence, visibility, clipping, responsive layout, and route protection without an LLM.
3. **Tier 2 — optional vision:** reserved for genuinely ambiguous visual decisions; it is not on the hot path.

The result is designed for reproducible hackathon evidence, not a pile of speculative bug reports.

## Implemented capabilities

| Area | What the project provides |
| --- | --- |
| Browser execution | Playwright Chromium, fixed viewports, bounded 30-second readiness/navigation/screenshot timeouts, and explicit Socket.IO readiness checks. |
| Evidence | Screenshot, normalized oracle JSON, `report.json`, and a Playwright video per executed capability. |
| Reliability | Fresh-context retries for deterministic failures; `uncertain` results are skipped rather than reported as bugs. |
| Demo mode | One visible headed Chromium context with 250 ms action pacing and a separately recorded tab per capability. |
| Oracle/configuration | YAML target profile, live cockpit/control API preflight, Socket.IO/WHEP metadata, freshness threshold, and target-namespaced locator persistence. |
| Assertions | Source-backed connection, device-selection, map-mode, responsive-control, telemetry, video-tile, and live-interaction checks. Generic assertion modules remain available for targets that expose those product concepts. |
| Calibration | Nine reversible Level 1 mutation definitions, local fixture state, and separate fixture/target scorecard support. |

### Current Cockpit run coverage

The live FlytBase profile runs seven Cockpit-specific browser journeys. They select real drones, change map mode, resize to a mobile viewport, read rendered telemetry, inspect the video tile, and audit live links/buttons. Every journey captures its post-action state, so capability screenshots and videos are not repeated home-page captures. Product concepts that Cockpit does not have (incident joining, participants, auth gates) remain unsupported rather than being guessed.

## Quick start

### 1. Start FlytBase Cockpit

```bash
cd "/home/shubhamxpawar/Tech/Hacks/cockpit-app"
npm run dev
```

Expected local services:

- Cockpit: `http://localhost:5173`
- Control API: `http://localhost:4000/api/health`

### 2. Install the agent

```bash
cd "/home/shubhamxpawar/Tech/Hacks/Testing agent"
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

### 3. Run normally

```bash
./scripts/run-live.sh
```

This is headless and writes a timestamped directory under `artifacts/`. If the cockpit or control API is stopped, it exits with a short actionable error before opening Chromium or creating artifacts.

### 4. Run a visual demo

```bash
./scripts/run-demo.sh
```

This opens one Chromium window at a 250 ms action pace. The browser context remains open for the whole run; each capability uses a recorded tab so the report still has individual video evidence.

## Hackathon video walkthrough

Use the detailed [demo storyboard](docs/hackathon-demo.md). A concise 2-minute sequence is:

1. Show Cockpit at `localhost:5173`, the `socket connected` badge, drones, telemetry, and control panel.
2. Show `configs/flytbase-cockpit.yaml` and explain that URLs, Socket.IO, WHEP, freshness threshold, and test IDs were verified from source and the live app.
3. Run `./scripts/run-demo.sh`; narrate that the test agent waits for the real socket badge instead of `networkidle`, then runs distinct journeys—device selection, map switching, responsive layout, telemetry comparison, video inspection, and interactive-control audit—with a video/screenshot/oracle payload for each.
4. Open `artifacts/run-*/report.json`, one screenshot, one video, and its oracle payload.
5. Explain the mutation catalog and that target scorecards are kept separate from fixture scorecards.

Do not describe `uncertain` goals as passing. Their value is that the agent reports a coverage gap honestly rather than hallucinating a result.

## Using this with your own system

1. Copy `configs/target.example.yaml` and assign a stable, unique `target_id`. This prevents locator knowledge from one application being reused against another.
2. Set the frontend URL, control API, transport metadata, source-backed video identity, map convention, and freshness threshold. Verify each value from your source or live instance.
3. Copy `configs/capabilities.example.yaml` and write outcome goals—what the user must be able to accomplish—not selectors or bug descriptions. Add a source-backed target adapter, like `cockpit.py`, for the interactions and data extraction specific to that system.
4. Add a target evaluator/mapping in `planner.py` and `runner.py` only where you have both a trustworthy oracle and a rendered UI value. Return `uncertain` when either is absent.
5. Add a reversible calibration mutation and unit/integration test for each new check before trusting its catch rate.
6. Run `agentic-testing run --target <target.yaml> --capabilities <goals.yaml> --out artifacts/ --headless` in CI or `--headed --reuse-session` for demonstrations.

## Artifacts and exit behavior

Each successful run writes:

```text
artifacts/run-<timestamp>/
├── report.json
└── capabilities/<goal-id>/
    ├── attempt-1.png
    ├── attempt-1-oracle.json
    └── attempt-1/scenario-trimmed.webm
```

`report.json` records each goal as `pass`, `fail`, or `uncertain`. Confirmed failures are emitted as `Finding` records with evidence. A healthy run with zero findings exits `0`; an unavailable cockpit/control API exits `2` without a browser session or artifact directory.

## Development

```bash
.venv/bin/python -m pytest -q
.venv/bin/agentic-testing validate-config configs/flytbase-cockpit.yaml configs/flytbase-capabilities.yaml
```
