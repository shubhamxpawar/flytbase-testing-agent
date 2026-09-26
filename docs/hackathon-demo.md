# Hackathon Demo Storyboard

This video should demonstrate repeatability and evidence quality, not merely that Chromium can click around.

## Before recording

1. Start the FlytBase cockpit with `npm run dev` and wait for `http://localhost:5173` plus `http://localhost:4000/api/health`.
2. Open the cockpit once and confirm the visible `socket connected` badge and device list.
3. In the testing-agent project, remove only disposable old artifact folders if you want a clean recording; do not remove evidence you intend to submit.
4. Keep two terminals visible: one for Cockpit and one for the agent. Use a terminal font large enough to read in the video.

## Two-minute recording script

### 0:00–0:20 — establish the product and oracle

Show the Cockpit at `http://localhost:5173` and briefly show the backend health endpoint. Explain that the frontend’s Socket.IO status and the control API are independent sources, so a visual claim can be checked against live state.

### 0:20–0:40 — show configuration discipline

Open `configs/flytbase-cockpit.yaml`. Point out the verified frontend/control API URLs, Socket.IO transport, WHEP URL, video test ID, and five-second freshness rule. State that values are taken from the live app and its source, not guessed.

### 0:40–1:15 — run the visible agent

Run:

```bash
./scripts/run-demo.sh
```

Explain that this keeps one Chromium session open for a clean visual demo. Each capability still creates its own recorded tab and evidence folder. Mention the 30-second bounded socket-readiness check and that the runner fails clearly if the app is down.

### 1:15–1:45 — inspect evidence

Open the newest `artifacts/run-*/report.json`. Then open the matching screenshot, `attempt-1-oracle.json`, and `scenario-trimmed.webm` for one capability. Explain how these make a result reproducible.

### 1:45–2:00 — explain scope honestly

Show the capability verdicts. Explain that unsupported UI-to-oracle mappings are marked `uncertain`, not reported as fabricated bugs. Close by showing the mutation catalog and explaining that catch-rate claims are only made after calibration.

## Optional mutation segment

Only include this after a mutation is wired to a real target check and its calibration result is available. Record the healthy run first, activate one reversible mutation, rerun, then show the resulting finding with its screenshot, oracle payload, and video. Never present a fixture-only score as a real-target catch rate.
