"""Audio deepfake / synthetic-speech detection (Hugging Face model).

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
    """AI-voice / spoofed-speech detector using a Hugging Face audio-classification model."""

    SR = 16000
    CHUNK_SEC = 6.0
    MAX_SEC = 60.0

    def __init__(self, model_id: Optional[str] = None):
        self.model_id = model_id or AUDIO_MODEL_ID or "(not configured)"
        self._loaded = False
        self._available = False
        self._pipe = None
        self._load_error = "Audio detection disabled (SENTRY_AUDIO_ENABLED=0 or no model id)."

    @property
    def is_available(self) -> bool:
        if not AUDIO_ENABLED or not AUDIO_MODEL_ID:
            return False
        self._ensure_loaded()
        return self._available

    @property
    def status_message(self) -> str:
        if self.is_available:
            return f"Audio model ready: {self.model_id}"
        return self._load_error

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        try:
            from transformers import pipeline
            self._pipe = pipeline("audio-classification", model=self.model_id, device=-1)
            labels = {str(v).lower() for v in self._pipe.model.config.id2label.values()}
            if not ({"fake", "spoof"} & labels):
                raise ValueError(f"Model labels {labels} do not include fake/spoof")
            self._available = True
        except Exception as exc:  # noqa: BLE001
            self._available = False
            self._load_error = f"{type(exc).__name__}: {exc}"
            logger.warning("audio_model_unavailable err=%s", self._load_error)

    def analyze_audio_path(self, path: Optional[Path]) -> AudioDetectionResult:
        started = time.perf_counter()
        limitations = list(DEFAULT_AUDIO_LIMITATIONS)

        def done(**kw):
            return AudioDetectionResult(model_id=self.model_id, limitations=limitations,
                                        latency_ms=(time.perf_counter() - started) * 1000, **kw)

        if path is None:
            return done(status="skipped", model_loaded=False, error="No audio file provided.")
        if not self.is_available:
            return done(status="unavailable", model_loaded=False, error=self.status_message)
        try:
            from sentrydeepfake.utils.audio_io import load_audio
            y, sr = load_audio(Path(path), sr=self.SR, max_sec=self.MAX_SEC)
        except Exception as exc:  # noqa: BLE001
            return done(status="failed", model_loaded=True, error=f"Could not read audio: {exc}")
        import numpy as np
        duration = len(y) / sr
        if duration < 0.5 or float(np.sqrt(np.mean(y ** 2))) < 1e-4:
            return done(status="failed", model_loaded=True,
                        error="Audio is too short or silent to analyse.",
                        metadata={"duration_sec": duration})
        try:
            n = int(self.CHUNK_SEC * sr)
            chunks = [y[i:i + n] for i in range(0, len(y), n)]
            chunks = [c for c in chunks if len(c) >= sr] or [y]
            fakes = []
            for c in chunks:
                out = self._pipe({"raw": c, "sampling_rate": sr}, top_k=None)
                sc = {d["label"].lower(): float(d["score"]) for d in out}
                fake = sc.get("fake", sc.get("spoof"))
                real = sc.get("real", sc.get("bonafide", sc.get("bona-fide")))
                if fake is None and real is not None:
                    fake = 1 - real
                fakes.append(fake)
            spoof = float(sum(fakes) / len(fakes))
        except Exception as exc:  # noqa: BLE001
            return done(status="failed", model_loaded=True, error=f"{type(exc).__name__}: {exc}")
        label = "SPOOF" if spoof >= 0.6 else ("BONA_FIDE" if spoof < 0.4 else "UNCERTAIN")
        return done(status="success", model_loaded=True, spoof_score=round(spoof, 4),
                    bona_fide_score=round(1 - spoof, 4), aggregate_label=label,
                    notes=[f"{len(fakes)} segment(s) analysed, {duration:.1f}s of audio."],
                    metadata={"duration_sec": duration, "segment_scores": [round(f, 4) for f in fakes]})


_AUDIO: Optional[AudioDeepfakeDetector] = None


def get_audio_detector() -> AudioDeepfakeDetector:
    global _AUDIO
    if _AUDIO is None:
        _AUDIO = AudioDeepfakeDetector()
    return _AUDIO
