"""Demonstration helpers with clearly labeled simulated results when needed."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sentrydeepfake.services.audio_detector import AudioDetectionResult
from sentrydeepfake.services.report_generator import build_report
from sentrydeepfake.services.risk_engine import assess_risk
from sentrydeepfake.services.sync_analyzer import SyncAnalysisResult
from sentrydeepfake.services.video_detector import FramePrediction, VideoDetectionResult

SIMULATION_BANNER = "SIMULATED DEMO DATA — NOT LIVE AI DETECTION"


def simulated_genuine_bundle(session_id: str = "demo-genuine") -> Dict[str, Any]:
    video = VideoDetectionResult(
        status="success",
        model_id="(simulated)",
        model_loaded=False,
        labels_map={"Real": "real", "Fake": "fake"},
        frame_predictions=_frames([0.12, 0.18, 0.15, 0.11, 0.14]),
        aggregate_label="likely_authentic_media",
        mean_fake_score=0.14,
        max_fake_score=0.18,
        mean_real_score=0.86,
        frames_analyzed=5,
        latency_ms=42.0,
        limitations=["Simulated scores for offline demonstration only."],
        demo_mode=True,
        metadata={"note": SIMULATION_BANNER},
    )
    audio = AudioDetectionResult(
        status="unavailable",
        model_id="(not configured)",
        model_loaded=False,
        notes=["Audio module unavailable in demo simulation."],
    )
    sync = SyncAnalysisResult(
        status="success",
        method="simulated mouth-motion vs audio-RMS",
        correlation=0.48,
        lag_estimate_sec=0.0,
        samples_compared=40,
        interpretation="Simulated moderate alignment (not live measurement).",
        limitations=["Simulated sync metrics."],
        latency_ms=5.0,
    )
    risk = assess_risk(video, audio, sync)
    file_details = {
        "filename": "sample_genuine_demo.mp4",
        "size_bytes": 0,
        "note": SIMULATION_BANNER,
    }
    report = build_report(
        file_details=file_details,
        video=video,
        audio=audio,
        sync=sync,
        risk=risk,
        session_id=session_id,
        simulated=True,
    )
    return {
        "banner": SIMULATION_BANNER,
        "video": video,
        "audio": audio,
        "sync": sync,
        "risk": risk,
        "report": report,
        "label": "Genuine-looking sample (simulated)",
    }


def simulated_manipulated_bundle(session_id: str = "demo-manipulated") -> Dict[str, Any]:
    video = VideoDetectionResult(
        status="success",
        model_id="(simulated)",
        model_loaded=False,
        labels_map={"Real": "real", "Fake": "fake"},
        frame_predictions=_frames([0.78, 0.82, 0.74, 0.88, 0.80]),
        aggregate_label="likely_synthetic",
        mean_fake_score=0.804,
        max_fake_score=0.88,
        mean_real_score=0.196,
        frames_analyzed=5,
        latency_ms=45.0,
        limitations=["Simulated scores for offline demonstration only."],
        demo_mode=True,
        metadata={"note": SIMULATION_BANNER},
    )
    audio = AudioDetectionResult(
        status="unavailable",
        model_id="(not configured)",
        model_loaded=False,
        notes=["Audio module unavailable in demo simulation."],
    )
    sync = SyncAnalysisResult(
        status="success",
        method="simulated mouth-motion vs audio-RMS",
        correlation=0.08,
        lag_estimate_sec=0.3,
        samples_compared=40,
        interpretation="Simulated low alignment — informational only, not a fake verdict.",
        limitations=["Simulated sync metrics."],
        latency_ms=5.0,
    )
    risk = assess_risk(video, audio, sync)
    file_details = {
        "filename": "sample_manipulated_demo.mp4",
        "size_bytes": 0,
        "note": SIMULATION_BANNER,
    }
    report = build_report(
        file_details=file_details,
        video=video,
        audio=audio,
        sync=sync,
        risk=risk,
        session_id=session_id,
        simulated=True,
    )
    return {
        "banner": SIMULATION_BANNER,
        "video": video,
        "audio": audio,
        "sync": sync,
        "risk": risk,
        "report": report,
        "label": "Manipulated sample (simulated)",
    }


def comparison_rows(genuine: Dict[str, Any], manipulated: Dict[str, Any]) -> List[Dict[str, Any]]:
    def row(bundle: Dict[str, Any], name: str) -> Dict[str, Any]:
        v = bundle["video"]
        r = bundle["risk"]
        return {
            "sample": name,
            "risk": r.category,
            "video_aggregate": v.aggregate_label,
            "mean_fake": v.mean_fake_score,
            "max_fake": v.max_fake_score,
            "sync_corr": bundle["sync"].correlation,
            "simulated": True,
        }

    return [
        row(genuine, "Genuine-looking"),
        row(manipulated, "Manipulated"),
    ]


def _frames(fake_scores: List[float]) -> List[FramePrediction]:
    out = []
    for i, fs in enumerate(fake_scores):
        out.append(
            FramePrediction(
                timestamp_sec=float(i),
                label="likely_synthetic" if fs >= 0.55 else "likely_authentic_media",
                scores={"Fake": fs, "Real": 1.0 - fs},
                fake_score=fs,
                real_score=1.0 - fs,
                raw_top_label="Fake" if fs >= 0.5 else "Real",
                raw_top_score=max(fs, 1.0 - fs),
            )
        )
    return out


def explain_verification_need() -> List[str]:
    return [
        "Deepfake detection estimates whether media looks synthetic — it does not verify legal identity.",
        "When results are SUSPICIOUS or INCONCLUSIVE, confirm sensitive requests out-of-band.",
        "Call a known-good phone number, require step-up authentication, and escalate high-stakes interviews.",
        "Lower-risk model scores still do not authorize high-value transfers without normal controls.",
    ]
