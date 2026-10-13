"""Audio deepfake / synthetic-speech detection interface.

A compatible lightweight pretrained spoofing model is not bundled for this
CPU-first MVP. The module exposes a clear integration contract and reports
status as unavailable unless AUDIO_ENABLED and a model id are configured and
load successfully.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from sentrydeepfake.config import AUDIO_ENABLED, AUDIO_MODEL_ID
from sentrydeepfake.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AudioDetectionResult:
    status: str  # success | failed | unavailable | skipped
    model_id: str
    model_loaded: bool
    spoof_score: Optional[float] = None
    bona_fide_score: Optional[float] = None
    aggregate_label: Optional[str] = None
    latency_ms: float = 0.0
    error: Optional[str] = None
    limitations: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "model_id": self.model_id,
            "model_loaded": self.model_loaded,
            "spoof_score": self.spoof_score,
            "bona_fide_score": self.bona_fide_score,
            "aggregate_label": self.aggregate_label,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "limitations": self.limitations,
            "notes": self.notes,
            "metadata": self.metadata,
        }


DEFAULT_AUDIO_LIMITATIONS = [
    "Voice authenticity analysis is not speaker identity verification.",
    "A genuine-sounding clip does not prove the speaker is who they claim to be.",
    "Codec artifacts and short utterances reduce reliability of spoof detectors.",
]


class AudioDeepfakeDetector:
    """Optional audio spoof detector. Defaults to unavailable in this MVP."""

    def __init__(self, model_id: Optional[str] = None):
        self.model_id = model_id or AUDIO_MODEL_ID or "(not configured)"
        self._loaded = False
        self._available = False
        self._load_error = (
            "Audio deepfake detection is not enabled in this environment. "
            "Set SENTRY_AUDIO_ENABLED=1 and SENTRY_AUDIO_MODEL_ID to a compatible "
            "pretrained spoofing model to activate."
        )

    @property
    def is_available(self) -> bool:
        if not AUDIO_ENABLED or not AUDIO_MODEL_ID:
            return False
        self._ensure_loaded()
        return self._available

    @property
    def status_message(self) -> str:
        if not AUDIO_ENABLED or not AUDIO_MODEL_ID:
            return (
                "Planned / unavailable — no audio spoofing model configured. "
                "Upload path and risk engine already accept audio results when available."
            )
        self._ensure_loaded()
        if self._available:
            return f"Audio model ready: {self.model_id}"
        return self._load_error or "Audio model unavailable"

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not AUDIO_ENABLED or not AUDIO_MODEL_ID:
            self._available = False
            return
        # Extension point: load a HF / SpeechBrain spoofing model here.
        # Intentionally not fabricating scores when the model cannot load.
        try:
            # Placeholder for future integration — refuse silent fake success.
            raise NotImplementedError(
                f"No concrete audio model loader implemented for '{AUDIO_MODEL_ID}'."
            )
        except Exception as exc:  # noqa: BLE001
            self._available = False
            self._load_error = f"{type(exc).__name__}: {exc}"
            logger.warning("audio_model_unavailable err=%s", self._load_error)

    def analyze_audio_path(self, path: Optional[Path]) -> AudioDetectionResult:
        started = time.perf_counter()
        limitations = list(DEFAULT_AUDIO_LIMITATIONS)
        if path is None:
            return AudioDetectionResult(
                status="skipped",
                model_id=self.model_id,
                model_loaded=False,
                error="No audio file provided.",
                limitations=limitations,
                notes=["Audio module skipped — no separate audio upload."],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        if not self.is_available:
            return AudioDetectionResult(
                status="unavailable",
                model_id=self.model_id,
                model_loaded=False,
                error=self.status_message,
                limitations=limitations,
                notes=[
                    "Integration interface ready; inference disabled until a model is configured."
                ],
                latency_ms=(time.perf_counter() - started) * 1000,
                metadata={"path_suffix": path.suffix},
            )
        # Unreachable until a loader is implemented
        return AudioDetectionResult(
            status="failed",
            model_id=self.model_id,
            model_loaded=False,
            error="Audio model reported available but no inference path is implemented.",
            limitations=limitations,
            latency_ms=(time.perf_counter() - started) * 1000,
        )


_AUDIO: Optional[AudioDeepfakeDetector] = None


def get_audio_detector() -> AudioDeepfakeDetector:
    global _AUDIO
    if _AUDIO is None:
        _AUDIO = AudioDeepfakeDetector()
    return _AUDIO
