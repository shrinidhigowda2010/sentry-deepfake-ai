"""Tests for report generation and temp cleanup."""

from pathlib import Path

from sentrydeepfake.services.audio_detector import AudioDetectionResult
from sentrydeepfake.services.demo_data import simulated_manipulated_bundle
from sentrydeepfake.services.report_generator import build_report, report_to_csv, report_to_json
from sentrydeepfake.services.risk_engine import assess_risk
from sentrydeepfake.services.sync_analyzer import SyncAnalysisResult
from sentrydeepfake.services.video_detector import VideoDetectionResult
from sentrydeepfake.utils.tempfiles import cleanup_path, new_session_dir, temporary_upload


def test_report_json_csv_and_flags():
    video = VideoDetectionResult(
        status="success",
        model_id="m",
        model_loaded=True,
        mean_fake_score=0.2,
        max_fake_score=0.3,
        frames_analyzed=3,
        aggregate_label="likely_authentic_media",
    )
    audio = AudioDetectionResult(status="unavailable", model_id="a", model_loaded=False)
    sync = SyncAnalysisResult(status="skipped", method="n/a")
    risk = assess_risk(video, audio, sync)
    report = build_report(
        file_details={"filename": "x.mp4", "size_bytes": 10, "duration_sec": 1.5},
        video=video,
        audio=audio,
        sync=sync,
        risk=risk,
        session_id="abc",
        simulated=False,
    )
    js = report_to_json(report)
    csv = report_to_csv(report)
    assert "SentryDeepfake AI" in js
    assert "risk_category" in csv
    assert report["simulated_demo_data"] is False
    assert "video" in report["module_status"]


def test_simulated_report_banner():
    bundle = simulated_manipulated_bundle()
    assert bundle["report"]["simulated_demo_data"] is True
    assert "SIMULATED" in bundle["report"]["simulation_banner"]


def test_tempfile_cleanup():
    data = b"hello-world"
    with temporary_upload(data, suffix=".bin") as path:
        assert path.exists()
        assert path.read_bytes() == data
        kept = path
    assert not kept.exists()


def test_session_dir_cleanup():
    d = new_session_dir("pytest")
    f = d / "a.txt"
    f.write_text("x", encoding="utf-8")
    assert f.exists()
    cleanup_path(d)
    assert not d.exists()


def test_missing_streams_in_report_modules():
    risk = assess_risk(None, None, None)
    report = build_report(
        file_details={"filename": "none"},
        video=None,
        audio=None,
        sync=None,
        risk=risk,
        session_id="s",
    )
    assert report["module_status"]["video"] == "not_provided"
    assert risk.category == "INCONCLUSIVE"
