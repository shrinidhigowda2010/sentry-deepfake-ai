"""Tests for multimodal risk combination."""

from sentrydeepfake.services.audio_detector import AudioDetectionResult
from sentrydeepfake.services.risk_engine import assess_risk
from sentrydeepfake.services.sync_analyzer import SyncAnalysisResult
from sentrydeepfake.services.video_detector import VideoDetectionResult


def _video(status="success", mean=0.1, max_f=0.2, label="likely_authentic_media"):
    return VideoDetectionResult(
        status=status,
        model_id="test-model",
        model_loaded=status == "success",
        mean_fake_score=mean,
        max_fake_score=max_f,
        mean_real_score=None if mean is None else 1 - mean,
        aggregate_label=label,
        frames_analyzed=4,
    )


def _audio(status="unavailable", spoof=None):
    return AudioDetectionResult(
        status=status,
        model_id="audio-test",
        model_loaded=status == "success",
        spoof_score=spoof,
        aggregate_label="spoof" if spoof and spoof > 0.5 else "bona_fide",
    )


def _sync(status="success", corr=0.4):
    return SyncAnalysisResult(
        status=status,
        method="test",
        correlation=corr,
        lag_estimate_sec=0.0,
        interpretation="test",
    )


def test_lower_risk_when_video_clean_and_audio_unavailable():
    risk = assess_risk(_video(mean=0.1), _audio("unavailable"), _sync())
    assert risk.category == "LOWER RISK"
    assert risk.modules_run["audio"] == "unavailable"
    assert "not treated as a pass" in " ".join(risk.evidence).lower() or any(
        "not treated as a pass" in e.lower() for e in risk.evidence
    )


def test_suspicious_on_elevated_fake_score():
    risk = assess_risk(_video(mean=0.8, max_f=0.9, label="likely_synthetic"), _audio("skipped"), None)
    assert risk.category == "SUSPICIOUS"
    assert risk.recommended_verification


def test_inconclusive_when_video_missing():
    risk = assess_risk(None, _audio("unavailable"), None)
    assert risk.category == "INCONCLUSIVE"


def test_inconclusive_on_failed_inference():
    risk = assess_risk(_video(status="failed", mean=None), _audio("skipped"), _sync(status="failed"))
    assert risk.category == "INCONCLUSIVE"


def test_unknown_label_mapping_inconclusive():
    risk = assess_risk(_video(mean=None, label="unknown"), _audio("skipped"), None)
    assert risk.category == "INCONCLUSIVE"


def test_missing_detector_not_counted_as_authentic():
    risk = assess_risk(_video(mean=0.1), _audio("unavailable"), _sync(status="unavailable"))
    assert risk.modules_run["audio"] == "unavailable"
    assert risk.modules_run["sync"] == "unavailable"
    # Still can be LOWER RISK from video alone, but caveats present
    assert any("ignored" in c.lower() or "do not" in c.lower() for c in risk.caveats + risk.evidence)


def test_low_sync_does_not_alone_force_suspicious():
    risk = assess_risk(_video(mean=0.1), _audio("skipped"), _sync(corr=0.05))
    assert risk.category != "SUSPICIOUS"


def test_conflicting_audio_video_inconclusive():
    risk = assess_risk(
        _video(mean=0.1),
        _audio(status="success", spoof=0.9),
        None,
    )
    assert risk.category == "INCONCLUSIVE"
