"""Generate downloadable JSON/CSV analysis reports."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sentrydeepfake import __version__
from sentrydeepfake.services.audio_detector import AudioDetectionResult
from sentrydeepfake.services.risk_engine import RiskAssessment
from sentrydeepfake.services.sync_analyzer import SyncAnalysisResult
from sentrydeepfake.services.video_detector import VideoDetectionResult


def build_report(
    *,
    file_details: Dict[str, Any],
    video: Optional[VideoDetectionResult],
    audio: Optional[AudioDetectionResult],
    sync: Optional[SyncAnalysisResult],
    risk: RiskAssessment,
    session_id: str,
    simulated: bool = False,
) -> Dict[str, Any]:
    ts = datetime.now(timezone.utc).isoformat()
    models_used: List[str] = []
    module_status: Dict[str, str] = {}

    if video is not None:
        module_status["video"] = video.status
        if video.model_loaded and video.status == "success":
            models_used.append(video.model_id)
    else:
        module_status["video"] = "not_provided"

    if audio is not None:
        module_status["audio"] = audio.status
        if audio.model_loaded and audio.status == "success":
            models_used.append(audio.model_id)
    else:
        module_status["audio"] = "not_provided"

    if sync is not None:
        module_status["sync"] = sync.status
    else:
        module_status["sync"] = "not_provided"

    report: Dict[str, Any] = {
        "product": "SentryDeepfake AI",
        "version": __version__,
        "session_id": session_id,
        "analysis_timestamp_utc": ts,
        "simulated_demo_data": simulated,
        "disclaimer": (
            "This report is a triage aid for synthetic media risk. It does not verify "
            "legal identity and must not be treated as forensic proof of fraud."
        ),
        "file_details": file_details,
        "models_used": models_used,
        "module_status": module_status,
        "video_detection": video.to_dict() if video else None,
        "audio_detection": audio.to_dict() if audio else None,
        "sync_analysis": sync.to_dict() if sync else None,
        "risk_assessment": risk.to_dict(),
        "recommended_next_steps": _next_steps(risk),
        "known_limitations": _collect_limitations(video, audio, sync, risk),
    }
    if simulated:
        report["simulation_banner"] = "SIMULATED DEMO DATA — NOT LIVE AI DETECTION"
    return report


def report_to_json(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=False)


def report_to_csv(report: Dict[str, Any]) -> str:
    """Flatten key fields into a single-row CSV for quick export."""
    risk = report.get("risk_assessment") or {}
    video = report.get("video_detection") or {}
    audio = report.get("audio_detection") or {}
    sync = report.get("sync_analysis") or {}
    file_details = report.get("file_details") or {}

    row = {
        "analysis_timestamp_utc": report.get("analysis_timestamp_utc"),
        "session_id": report.get("session_id"),
        "filename": file_details.get("filename"),
        "size_bytes": file_details.get("size_bytes"),
        "duration_sec": file_details.get("duration_sec"),
        "risk_category": risk.get("category"),
        "risk_summary": risk.get("summary"),
        "video_status": video.get("status"),
        "video_model": video.get("model_id"),
        "video_aggregate_label": video.get("aggregate_label"),
        "video_mean_fake_score": video.get("mean_fake_score"),
        "video_max_fake_score": video.get("max_fake_score"),
        "video_frames_analyzed": video.get("frames_analyzed"),
        "video_latency_ms": video.get("latency_ms"),
        "audio_status": audio.get("status"),
        "audio_spoof_score": audio.get("spoof_score"),
        "sync_status": sync.get("status"),
        "sync_correlation": sync.get("correlation"),
        "simulated_demo_data": report.get("simulated_demo_data"),
        "models_used": "|".join(report.get("models_used") or []),
    }

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(row.keys()))
    writer.writeheader()
    writer.writerow(row)
    return buf.getvalue()


def _next_steps(risk: RiskAssessment) -> List[str]:
    base = [
        "Treat detector outputs as risk signals, not identity verification.",
        "For high-value actions, confirm via an independent channel.",
    ]
    if risk.category == "SUSPICIOUS":
        return [
            "Contact the person using a previously verified phone number.",
            "Confirm sensitive requests through an independent channel (not the same call/chat).",
            "Require an additional authentication step before any high-value transfer.",
            "Escalate remote interviews or onboarding sessions for manual verification.",
            *base,
        ]
    if risk.category == "INCONCLUSIVE":
        return [
            "Do not proceed with high-risk actions based solely on this analysis.",
            "Request a clearer recording or alternate media if quality is poor.",
            "Use out-of-band verification when stakes are material.",
            *base,
        ]
    return [
        "Available checks did not raise strong alarms; continue standard security controls.",
        *base,
    ]


def _collect_limitations(
    video: Optional[VideoDetectionResult],
    audio: Optional[AudioDetectionResult],
    sync: Optional[SyncAnalysisResult],
    risk: RiskAssessment,
) -> List[str]:
    items: List[str] = []
    for src in (video, audio, sync):
        if src is not None and getattr(src, "limitations", None):
            items.extend(list(src.limitations))
    items.extend(risk.caveats)
    # Dedupe preserving order
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
