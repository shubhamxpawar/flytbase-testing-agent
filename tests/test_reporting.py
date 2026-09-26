from pathlib import Path

import pytest

from agentic_testing.models import Evidence, Finding
from agentic_testing.reporting import write_finding, write_run_report


def test_confirmed_finding_requires_video() -> None:
    with pytest.raises(ValueError, match="video artifact"):
        Finding("M1", "Missing action", "visual", "desc", "tier 1", ("Open",), Evidence())


def test_report_rejects_missing_video_file(tmp_path: Path) -> None:
    finding = Finding(
        "M1", "Missing action", "visual", "desc", "tier 1", ("Open",), Evidence(video_path=tmp_path / "missing.webm")
    )
    with pytest.raises(ValueError, match="no persisted video"):
        write_finding(finding, tmp_path / "report")


def test_report_writes_video_reference(tmp_path: Path) -> None:
    video = tmp_path / "clip.webm"
    video.write_bytes(b"not-a-real-video")
    finding = Finding("M1", "Missing action", "visual", "desc", "tier 1", ("Open",), Evidence(video_path=video))
    result = write_finding(finding, tmp_path / "report")
    assert result.is_file()
    assert str(video) in result.read_text()


def test_run_report_writes_skipped_capability_summary(tmp_path: Path) -> None:
    result = write_run_report({"status": "completed", "capabilities": [{"verdict": "uncertain"}]}, tmp_path)
    assert result.is_file()
    assert '"uncertain"' in result.read_text()
