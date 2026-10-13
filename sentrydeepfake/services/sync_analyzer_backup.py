"""Audio–video synchronization heuristic.

Uses OpenCV face-mouth region motion energy correlated with audio RMS energy
when an audio track can be decoded. This is NOT a deepfake classifier and must
not alone label media as fake (dubbing, lag, and compression cause mismatches).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from sentrydeepfake.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SyncAnalysisResult:
    status: str  # success | failed | unavailable | skipped
    method: str
    correlation: Optional[float] = None
    lag_estimate_sec: Optional[float] = None
    samples_compared: int = 0
    interpretation: str = ""
    limitations: List[str] = field(default_factory=list)
    error: Optional[str] = None
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "method": self.method,
            "correlation": self.correlation,
            "lag_estimate_sec": self.lag_estimate_sec,
            "samples_compared": self.samples_compared,
            "interpretation": self.interpretation,
            "limitations": self.limitations,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
        }


LIMITATIONS = [
    "Synchronization mismatch alone does not prove a deepfake.",
    "Dubbing, translation overlays, network delay, and compression can desynchronize A/V.",
    "Heuristic uses mouth-region motion vs audio energy — not phoneme-level lip reading.",
    "Requires a detectable frontal face and a decodable audio track.",
]


def _extract_audio_rms(path: Path, hop_sec: float = 0.1) -> Optional[Tuple[np.ndarray, float]]:
    try:
        import librosa
    except ImportError:
        return None
    try:
        y, sr = librosa.load(str(path), sr=16000, mono=True)
        if y.size == 0:
            return None
        hop = max(1, int(sr * hop_sec))
        rms = []
        for i in range(0, len(y), hop):
            chunk = y[i : i + hop]
            rms.append(float(np.sqrt(np.mean(chunk**2) + 1e-12)))
        return np.asarray(rms, dtype=np.float64), hop_sec
    except Exception as exc:  # noqa: BLE001
        logger.info("audio_rms_failed err=%s", type(exc).__name__)
        return None


def _mouth_motion_series(path: Path, hop_sec: float = 0.1, max_sec: float = 60.0) -> Optional[np.ndarray]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return None
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    if fps <= 0:
        cap.release()
        return None
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    frame_interval = max(1, int(round(fps * hop_sec)))
    motions: List[float] = []
    prev_mouth = None
    idx = 0
    max_frames = int(fps * max_sec)
    while idx < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % frame_interval == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(60, 60))
            if len(faces) == 0:
                motions.append(0.0)
                prev_mouth = None
            else:
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                my, mh = y + int(h * 0.55), int(h * 0.45)
                mouth = gray[my : y + h, x : x + w]
                mouth = cv2.resize(mouth, (64, 32))
                if prev_mouth is None:
                    motions.append(0.0)
                else:
                    diff = np.mean(np.abs(mouth.astype(np.float32) - prev_mouth.astype(np.float32)))
                    motions.append(float(diff))
                prev_mouth = mouth
        idx += 1
    cap.release()
    if len(motions) < 5:
        return None
    return np.asarray(motions, dtype=np.float64)


def _best_lag_corr(a: np.ndarray, b: np.ndarray, max_lag: int = 8) -> Tuple[float, int]:
    n = min(len(a), len(b))
    a = a[:n]
    b = b[:n]
    a = (a - a.mean()) / (a.std() + 1e-9)
    b = (b - b.mean()) / (b.std() + 1e-9)
    best_corr = -2.0
    best_lag = 0
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            aa, bb = a[-lag:], b[: n + lag]
        elif lag > 0:
            aa, bb = a[: n - lag], b[lag:]
        else:
            aa, bb = a, b
        if len(aa) < 5:
            continue
        corr = float(np.mean(aa * bb))
        if corr > best_corr:
            best_corr = corr
            best_lag = lag
    return best_corr, best_lag


def analyze_av_sync(video_path: Path) -> SyncAnalysisResult:
    started = time.perf_counter()
    method = "mouth-motion vs audio-RMS cross-correlation"

    audio = _extract_audio_rms(video_path)
    if audio is None:
        return SyncAnalysisResult(
            status="unavailable",
            method=method,
            interpretation="Could not decode audio or librosa is unavailable.",
            limitations=list(LIMITATIONS),
            error="Audio track unavailable for synchronization analysis.",
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    audio_rms, hop = audio
    motion = _mouth_motion_series(video_path, hop_sec=hop)
    if motion is None:
        return SyncAnalysisResult(
            status="failed",
            method=method,
            interpretation="Insufficient face/mouth detections for motion series.",
            limitations=list(LIMITATIONS),
            error="Mouth-motion series could not be built.",
            latency_ms=(time.perf_counter() - started) * 1000,
            metadata={"audio_samples": int(len(audio_rms))},
        )

    corr, lag = _best_lag_corr(motion, audio_rms)
    lag_sec = lag * hop

    if corr >= 0.35:
        interpretation = (
            "Moderate-to-strong alignment between mouth motion and speech energy. "
            "This is not proof of authenticity."
        )
    elif corr >= 0.15:
        interpretation = (
            "Weak alignment — could be natural variation, compression, or mild desync. "
            "Do not treat as a deepfake verdict."
        )
    else:
        interpretation = (
            "Low alignment between mouth motion and speech energy. "
            "Possible desync, dubbing, or detection noise — escalate for human review if needed."
        )

    return SyncAnalysisResult(
        status="success",
        method=method,
        correlation=float(corr),
        lag_estimate_sec=float(lag_sec),
        samples_compared=int(min(len(motion), len(audio_rms))),
        interpretation=interpretation,
        limitations=list(LIMITATIONS),
        latency_ms=(time.perf_counter() - started) * 1000,
        metadata={"hop_sec": hop},
    )
