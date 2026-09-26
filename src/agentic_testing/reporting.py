"""Persist evidence and enforce the mandatory video-evidence contract."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .models import Finding


def preserve_video(source: Path, destination_dir: Path, *, trim_start_s: float | None = None, trim_end_s: float | None = None) -> Path:
    """Save a report-owned video, trimming with ffmpeg when timing is known.

    A copy of the original WebM is retained when ffmpeg is unavailable or the trim fails.
    """
    if not source.is_file():
        raise FileNotFoundError(f"video artifact was not produced: {source}")
    destination_dir.mkdir(parents=True, exist_ok=True)
    original = destination_dir / "scenario.webm"
    shutil.copy2(source, original)
    if trim_start_s is None or trim_end_s is None or trim_end_s <= trim_start_s or shutil.which("ffmpeg") is None:
        return original
    trimmed = destination_dir / "scenario-trimmed.webm"
    command = [
        "ffmpeg", "-y", "-ss", str(trim_start_s), "-to", str(trim_end_s), "-i", str(original), "-c", "copy", str(trimmed),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return trimmed if completed.returncode == 0 and trimmed.is_file() else original


def write_finding(finding: Finding, output_dir: Path) -> Path:
    """Write a portable JSON record after validating the mandatory video path."""
    video_path = finding.evidence.video_path
    if video_path is None or not video_path.is_file():
        raise ValueError(f"finding {finding.id} has no persisted video evidence")
    output_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "id": finding.id,
        "title": finding.title,
        "category": finding.category,
        "description": finding.description,
        "approach": finding.approach,
        "repro_steps": list(finding.repro_steps),
        "evidence": {
            "video": str(video_path),
            "screenshot": str(finding.evidence.screenshot_path) if finding.evidence.screenshot_path else None,
            "oracle_payload": finding.evidence.oracle_payload,
        },
    }
    path = output_dir / f"{finding.id}.json"
    path.write_text(json.dumps(record, indent=2, default=str) + "\n")
    return path


def write_run_report(summary: dict[str, object], output_dir: Path) -> Path:
    """Write the machine-readable summary for all findings and skipped capabilities."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "report.json"
    path.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    return path
