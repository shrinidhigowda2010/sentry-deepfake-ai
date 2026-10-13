"""Optional FastAPI service exposing the multimodal risk engine and analysis."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sentrydeepfake import __version__
from sentrydeepfake.config import APP_NAME
from sentrydeepfake.services.audio_detector import AudioDetectionResult
from sentrydeepfake.services.pipeline import run_video_analysis
from sentrydeepfake.services.risk_engine import assess_risk
from sentrydeepfake.services.sync_analyzer import SyncAnalysisResult
from sentrydeepfake.services.video_detector import VideoDetectionResult, get_video_detector
from sentrydeepfake.utils.tempfiles import cleanup_path

app = FastAPI(
    title=APP_NAME,
    version=__version__,
    description="Multimodal deepfake risk assessment API for SentryDeepfake AI",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class VideoResultIn(BaseModel):
    status: str
    model_id: str = ""
    model_loaded: bool = False
    mean_fake_score: Optional[float] = None
    max_fake_score: Optional[float] = None
    mean_real_score: Optional[float] = None
    aggregate_label: Optional[str] = None
    frames_analyzed: int = 0
    error: Optional[str] = None


class AudioResultIn(BaseModel):
    status: str = "unavailable"
    model_id: str = ""
    model_loaded: bool = False
    spoof_score: Optional[float] = None
    bona_fide_score: Optional[float] = None
    aggregate_label: Optional[str] = None
    error: Optional[str] = None


class SyncResultIn(BaseModel):
    status: str = "unavailable"
    method: str = ""
    correlation: Optional[float] = None
    lag_estimate_sec: Optional[float] = None
    interpretation: str = ""
    error: Optional[str] = None


class RiskRequest(BaseModel):
    video: Optional[VideoResultIn] = None
    audio: Optional[AudioResultIn] = None
    sync: Optional[SyncResultIn] = None


@app.get("/health")
def health() -> Dict[str, Any]:
    detector = get_video_detector()
    return {
        "status": "ok",
        "product": APP_NAME,
        "version": __version__,
        "video_model_id": detector.model_id,
        "video_model_available": detector.is_available,
        "video_model_error": detector.load_error,
    }


@app.post("/risk/assess")
def risk_assess(body: RiskRequest) -> Dict[str, Any]:
    """Combine detector outputs into an explainable risk assessment."""
    video = None
    if body.video is not None:
        video = VideoDetectionResult(
            status=body.video.status,
            model_id=body.video.model_id,
            model_loaded=body.video.model_loaded,
            mean_fake_score=body.video.mean_fake_score,
            max_fake_score=body.video.max_fake_score,
            mean_real_score=body.video.mean_real_score,
            aggregate_label=body.video.aggregate_label,
            frames_analyzed=body.video.frames_analyzed,
            error=body.video.error,
        )
    audio = None
    if body.audio is not None:
        audio = AudioDetectionResult(
            status=body.audio.status,
            model_id=body.audio.model_id,
            model_loaded=body.audio.model_loaded,
            spoof_score=body.audio.spoof_score,
            bona_fide_score=body.audio.bona_fide_score,
            aggregate_label=body.audio.aggregate_label,
            error=body.audio.error,
        )
    sync = None
    if body.sync is not None:
        sync = SyncAnalysisResult(
            status=body.sync.status,
            method=body.sync.method,
            correlation=body.sync.correlation,
            lag_estimate_sec=body.sync.lag_estimate_sec,
            interpretation=body.sync.interpretation,
            error=body.sync.error,
        )
    assessment = assess_risk(video, audio, sync)
    return assessment.to_dict()


@app.post("/analyze/video")
async def analyze_video(
    file: UploadFile = File(...),
    run_sync: bool = True,
) -> Dict[str, Any]:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload")
    suffix = Path(file.filename or "upload.mp4").suffix or ".mp4"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = Path(tmp.name)
    try:
        tmp.write(data)
        tmp.close()
        bundle = run_video_analysis(
            filename=file.filename or "upload.mp4",
            data=data,
            temp_path=tmp_path,
            run_sync=run_sync,
            run_audio=True,
        )
        return {
            "session_id": bundle.session_id,
            "file_details": bundle.file_details,
            "video": bundle.video.to_dict(),
            "audio": bundle.audio.to_dict(),
            "sync": bundle.sync.to_dict(),
            "risk": bundle.risk.to_dict(),
            "report": bundle.report,
            "total_latency_ms": bundle.total_latency_ms,
        }
    finally:
        cleanup_path(tmp_path)
