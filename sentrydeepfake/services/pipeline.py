"""End-to-end analysis orchestration."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from sentrydeepfake.services.audio_detector import AudioDetectionResult, get_audio_detector
from sentrydeepfake.services.report_generator import build_report
from sentrydeepfake.services.risk_engine import RiskAssessment, assess_risk
from sentrydeepfake.services.sync_analyzer import SyncAnalysisResult, analyze_av_sync
from sentrydeepfake.services.video_detector import VideoDetectionResult, get_video_detector
from sentrydeepfake.utils.logging_config import get_logger
from sentrydeepfake.utils.validation import (
    validate_duration,
    validate_video_bytes,
)

logger = get_logger(__name__)

ProgressCallback = Optional[Callable[[float, str], None]]


@dataclass
class AnalysisBundle:
    session_id: str
    file_details: Dict[str, Any]
    video: VideoDetectionResult
    audio: AudioDetectionResult
    sync: SyncAnalysisResult
    risk: RiskAssessment
    report: Dict[str, Any]
    total_latency_ms: float
    history_entry: Dict[str, Any] = field(default_factory=dict)


def run_video_analysis(
    *,
    filename: str,
    data: bytes,
    temp_path: Path,
    run_sync: bool = True,
    run_audio: bool = True,
    progress: ProgressCallback = None,
) -> AnalysisBundle:
    """Validate, analyze, fuse risk, and build a report for an uploaded video."""
    t0 = time.perf_counter()
    session_id = uuid.uuid4().hex[:12]

    validation = validate_video_bytes(filename, data)
    if not validation.ok:
        video = VideoDetectionResult(
            status="failed",
            model_id=get_video_detector().model_id,
            model_loaded=False,
            error=validation.error,
        )
        audio = AudioDetectionResult(
            status="skipped", model_id="(n/a)", model_loaded=False, error="Skipped due to validation failure"
        )
        sync = SyncAnalysisResult(
            status="skipped", method="n/a", error="Skipped due to validation failure"
        )
        risk = assess_risk(video, audio, sync)
        file_details = {
            "filename": filename,
            "size_bytes": len(data),
            "error": validation.error,
        }
        report = build_report(
            file_details=file_details,
            video=video,
            audio=audio,
            sync=sync,
            risk=risk,
            session_id=session_id,
        )
        return AnalysisBundle(
            session_id=session_id,
            file_details=file_details,
            video=video,
            audio=audio,
            sync=sync,
            risk=risk,
            report=report,
            total_latency_ms=(time.perf_counter() - t0) * 1000,
            history_entry=_history(session_id, filename, risk, video),
        )

    if progress:
        progress(0.05, "Probing video metadata")

    from sentrydeepfake.services.frame_extractor import probe_video

    meta = probe_video(temp_path)
    dur_check = validate_duration(meta.duration_sec if meta.has_video else None)
    file_details = {
        "filename": filename,
        "size_bytes": len(data),
        "extension": validation.extension,
        "width": meta.width,
        "height": meta.height,
        "fps": meta.fps,
        "duration_sec": meta.duration_sec,
        "frame_count": meta.frame_count,
        "codec": meta.codec,
        "has_video_stream": meta.has_video,
    }

    if not dur_check.ok:
        video = VideoDetectionResult(
            status="failed",
            model_id=get_video_detector().model_id,
            model_loaded=False,
            error=dur_check.error,
            metadata=file_details,
        )
        audio = AudioDetectionResult(
            status="skipped", model_id="(n/a)", model_loaded=False, error=dur_check.error
        )
        sync = SyncAnalysisResult(status="skipped", method="n/a", error=dur_check.error)
        risk = assess_risk(video, audio, sync)
        report = build_report(
            file_details=file_details,
            video=video,
            audio=audio,
            sync=sync,
            risk=risk,
            session_id=session_id,
        )
        return AnalysisBundle(
            session_id=session_id,
            file_details=file_details,
            video=video,
            audio=audio,
            sync=sync,
            risk=risk,
            report=report,
            total_latency_ms=(time.perf_counter() - t0) * 1000,
            history_entry=_history(session_id, filename, risk, video),
        )

    def video_progress(p: float, msg: str) -> None:
        if progress:
            progress(0.1 + 0.55 * p, msg)

    if progress:
        progress(0.1, "Running video deepfake detection")
    video = get_video_detector().analyze_video_path(temp_path, progress=video_progress)

    if run_audio:
        if progress:
            progress(0.7, "Checking audio detector availability")
        audio = get_audio_detector().analyze_audio_path(temp_path)
    else:
        audio = AudioDetectionResult(
            status="skipped",
            model_id=get_audio_detector().model_id,
            model_loaded=False,
            notes=["Audio analysis skipped by caller."],
        )

    if run_sync:
        if progress:
            progress(0.82, "Running A/V synchronization heuristic")
        sync = analyze_av_sync(temp_path)
    else:
        sync = SyncAnalysisResult(
            status="skipped",
            method="n/a",
            interpretation="Sync analysis skipped by caller.",
        )

    if progress:
        progress(0.93, "Combining risk assessment")
    risk = assess_risk(video, audio, sync)
    report = build_report(
        file_details=file_details,
        video=video,
        audio=audio,
        sync=sync,
        risk=risk,
        session_id=session_id,
    )
    if progress:
        progress(1.0, "Complete")

    logger.info(
        "analysis_complete session=%s risk=%s video_status=%s",
        session_id,
        risk.category,
        video.status,
    )
    return AnalysisBundle(
        session_id=session_id,
        file_details=file_details,
        video=video,
        audio=audio,
        sync=sync,
        risk=risk,
        report=report,
        total_latency_ms=(time.perf_counter() - t0) * 1000,
        history_entry=_history(session_id, filename, risk, video),
    )


def _history(
    session_id: str,
    filename: str,
    risk: RiskAssessment,
    video: VideoDetectionResult,
) -> Dict[str, Any]:
    return {
        "session_id": session_id,
        "filename": filename,
        "risk_category": risk.category,
        "video_status": video.status,
        "mean_fake_score": video.mean_fake_score,
        "frames_analyzed": video.frames_analyzed,
        "latency_ms": video.latency_ms,
    }
