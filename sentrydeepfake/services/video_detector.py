"""Video deepfake detection via pretrained Hugging Face image classifier."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from PIL import Image

from sentrydeepfake.config import FORCE_DEMO_MODE, VIDEO_MODEL_DEVICE, VIDEO_MODEL_ID
from sentrydeepfake.services.frame_extractor import ExtractedFrames, extract_frames
from sentrydeepfake.utils.logging_config import get_logger

logger = get_logger(__name__)

ProgressCallback = Optional[Callable[[float, str], None]]


@dataclass
class FramePrediction:
    timestamp_sec: float
    label: str
    scores: Dict[str, float]
    fake_score: Optional[float]
    real_score: Optional[float]
    raw_top_label: str
    raw_top_score: float


@dataclass
class VideoDetectionResult:
    status: str  # success | failed | demo | unavailable
    model_id: str
    model_loaded: bool
    labels_map: Dict[str, str] = field(default_factory=dict)
    frame_predictions: List[FramePrediction] = field(default_factory=list)
    aggregate_label: Optional[str] = None
    mean_fake_score: Optional[float] = None
    max_fake_score: Optional[float] = None
    mean_real_score: Optional[float] = None
    frames_analyzed: int = 0
    latency_ms: float = 0.0
    error: Optional[str] = None
    limitations: List[str] = field(default_factory=list)
    demo_mode: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "model_id": self.model_id,
            "model_loaded": self.model_loaded,
            "labels_map": self.labels_map,
            "aggregate_label": self.aggregate_label,
            "mean_fake_score": self.mean_fake_score,
            "max_fake_score": self.max_fake_score,
            "mean_real_score": self.mean_real_score,
            "frames_analyzed": self.frames_analyzed,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "limitations": self.limitations,
            "demo_mode": self.demo_mode,
            "metadata": self.metadata,
            "frame_predictions": [
                {
                    "timestamp_sec": fp.timestamp_sec,
                    "label": fp.label,
                    "scores": fp.scores,
                    "fake_score": fp.fake_score,
                    "real_score": fp.real_score,
                    "raw_top_label": fp.raw_top_label,
                    "raw_top_score": fp.raw_top_score,
                }
                for fp in self.frame_predictions
            ],
        }


DEFAULT_LIMITATIONS = [
    "Frame-level image classifiers are not calibrated fraud probabilities.",
    "Compression, low resolution, makeup, filters, and unusual lighting can shift scores.",
    "Absence of a 'fake' signal does not prove legal identity or authenticity of intent.",
    "Results apply only to sampled frames, not every pixel of the video.",
]


class VideoDeepfakeDetector:
    """Lazy-loads a HF image-classification model and scores video frames."""

    def __init__(self, model_id: Optional[str] = None, device: Optional[str] = None):
        self.model_id = model_id or VIDEO_MODEL_ID
        self.device = device or VIDEO_MODEL_DEVICE
        self._pipe = None
        self._id2label: Dict[int, str] = {}
        self._label_roles: Dict[str, str] = {}  # model_label -> real|fake|unknown
        self._load_error: Optional[str] = None
        self._loaded = False

    @property
    def is_available(self) -> bool:
        if FORCE_DEMO_MODE:
            return False
        if self._loaded:
            return self._pipe is not None
        self._ensure_loaded()
        return self._pipe is not None

    @property
    def load_error(self) -> Optional[str]:
        if FORCE_DEMO_MODE:
            return "Demo mode forced via SENTRY_FORCE_DEMO_MODE=1"
        self._ensure_loaded()
        return self._load_error

    def _ensure_loaded(self) -> None:
        if self._loaded or FORCE_DEMO_MODE:
            if FORCE_DEMO_MODE:
                self._loaded = True
                self._load_error = "Demo mode forced via SENTRY_FORCE_DEMO_MODE=1"
            return
        self._loaded = True
        try:
            import torch
            from transformers import AutoImageProcessor, AutoModelForImageClassification
            from transformers import pipeline as hf_pipeline

            logger.info("loading_video_model id=%s device=%s", self.model_id, self.device)
            processor = AutoImageProcessor.from_pretrained(self.model_id)
            model = AutoModelForImageClassification.from_pretrained(self.model_id)
            model.eval()
            self._id2label = {int(k): str(v) for k, v in model.config.id2label.items()}
            self._label_roles = _infer_label_roles(self._id2label)
            device_idx = 0 if self.device.startswith("cuda") and torch.cuda.is_available() else -1
            self._pipe = hf_pipeline(
                task="image-classification",
                model=model,
                image_processor=processor,
                device=device_idx,
                top_k=None,
            )
            logger.info(
                "video_model_ready labels=%s roles=%s",
                list(self._id2label.values()),
                self._label_roles,
            )
        except Exception as exc:  # noqa: BLE001
            self._pipe = None
            self._load_error = f"{type(exc).__name__}: {exc}"
            logger.error("video_model_load_failed err=%s", self._load_error)

    def analyze_frames(
        self,
        extracted: ExtractedFrames,
        progress: ProgressCallback = None,
    ) -> VideoDetectionResult:
        started = time.perf_counter()
        limitations = list(DEFAULT_LIMITATIONS)

        if not extracted.ok:
            return VideoDetectionResult(
                status="failed",
                model_id=self.model_id,
                model_loaded=False,
                error=extracted.error or "Frame extraction failed",
                limitations=limitations,
                latency_ms=(time.perf_counter() - started) * 1000,
            )

        if FORCE_DEMO_MODE or not self.is_available:
            err = self.load_error or "Model unavailable"
            return VideoDetectionResult(
                status="unavailable",
                model_id=self.model_id,
                model_loaded=False,
                error=err,
                limitations=limitations
                + ["Live model inference unavailable — use Demo Mode for simulated walkthrough."],
                demo_mode=False,
                latency_ms=(time.perf_counter() - started) * 1000,
                metadata={"frames_available": len(extracted.frames)},
            )

        predictions: List[FramePrediction] = []
        total = len(extracted.frames)
        try:
            for i, (frame, ts) in enumerate(zip(extracted.frames, extracted.timestamps_sec)):
                if progress:
                    progress((i / max(total, 1)), f"Scoring frame {i + 1}/{total}")
                image = Image.fromarray(frame.astype(np.uint8))
                outputs = self._pipe(image)
                # outputs: list[{label, score}]
                scores = {str(item["label"]): float(item["score"]) for item in outputs}
                top = max(outputs, key=lambda x: float(x["score"]))
                mapped = _map_prediction(scores, self._label_roles)
                predictions.append(
                    FramePrediction(
                        timestamp_sec=float(ts),
                        label=mapped["normalized_label"],
                        scores=scores,
                        fake_score=mapped["fake_score"],
                        real_score=mapped["real_score"],
                        raw_top_label=str(top["label"]),
                        raw_top_score=float(top["score"]),
                    )
                )
            if progress:
                progress(1.0, "Aggregation complete")
        except Exception as exc:  # noqa: BLE001
            logger.exception("video_inference_failed")
            return VideoDetectionResult(
                status="failed",
                model_id=self.model_id,
                model_loaded=True,
                labels_map=dict(self._label_roles),
                error=f"Inference failed: {type(exc).__name__}: {exc}",
                limitations=limitations,
                latency_ms=(time.perf_counter() - started) * 1000,
            )

        fake_scores = [p.fake_score for p in predictions if p.fake_score is not None]
        real_scores = [p.real_score for p in predictions if p.real_score is not None]
        mean_fake = float(np.mean(fake_scores)) if fake_scores else None
        max_fake = float(np.max(fake_scores)) if fake_scores else None
        mean_real = float(np.mean(real_scores)) if real_scores else None

        if mean_fake is None:
            aggregate = "unknown"
        elif mean_fake >= 0.55:
            aggregate = "likely_synthetic"
        elif mean_fake <= 0.45:
            aggregate = "likely_authentic_media"
        else:
            aggregate = "uncertain"

        meta = {}
        if extracted.metadata:
            meta = {
                "width": extracted.metadata.width,
                "height": extracted.metadata.height,
                "fps": extracted.metadata.fps,
                "duration_sec": extracted.metadata.duration_sec,
                "frame_count": extracted.metadata.frame_count,
                "codec": extracted.metadata.codec,
            }

        return VideoDetectionResult(
            status="success",
            model_id=self.model_id,
            model_loaded=True,
            labels_map=dict(self._label_roles),
            frame_predictions=predictions,
            aggregate_label=aggregate,
            mean_fake_score=mean_fake,
            max_fake_score=max_fake,
            mean_real_score=mean_real,
            frames_analyzed=len(predictions),
            latency_ms=(time.perf_counter() - started) * 1000,
            limitations=limitations,
            metadata=meta,
        )

    def analyze_video_path(
        self,
        path: Path,
        progress: ProgressCallback = None,
    ) -> VideoDetectionResult:
        if progress:
            progress(0.05, "Extracting frames")
        extracted = extract_frames(path)
        if progress:
            progress(0.2, "Running model inference")
        return self.analyze_frames(extracted, progress=progress)


def _infer_label_roles(id2label: Dict[int, str]) -> Dict[str, str]:
    """Map model label strings to semantic roles without assuming fixed names."""
    roles: Dict[str, str] = {}
    for label in id2label.values():
        key = label.lower().strip()
        if key in {"fake", "deepfake", "spoof", "synthetic", "manipulated", "forged"}:
            roles[label] = "fake"
        elif key in {"real", "bonafide", "bona-fide", "genuine", "authentic"}:
            roles[label] = "real"
        elif "fake" in key or "deepfake" in key or "spoof" in key:
            roles[label] = "fake"
        elif "real" in key or "genuine" in key or "authentic" in key:
            roles[label] = "real"
        else:
            roles[label] = "unknown"
    return roles


def _map_prediction(scores: Dict[str, float], roles: Dict[str, str]) -> Dict[str, Any]:
    fake_score = None
    real_score = None
    for label, score in scores.items():
        role = roles.get(label, "unknown")
        if role == "fake":
            fake_score = score if fake_score is None else max(fake_score, score)
        elif role == "real":
            real_score = score if real_score is None else max(real_score, score)

    if fake_score is None and real_score is not None:
        fake_score = 1.0 - real_score
    if real_score is None and fake_score is not None:
        real_score = 1.0 - fake_score

    if fake_score is None:
        normalized = "unknown"
    elif fake_score >= 0.55:
        normalized = "likely_synthetic"
    elif fake_score <= 0.45:
        normalized = "likely_authentic_media"
    else:
        normalized = "uncertain"

    return {
        "normalized_label": normalized,
        "fake_score": fake_score,
        "real_score": real_score,
    }


# Process-wide singleton for Streamlit caching friendliness
_DETECTOR: Optional[VideoDeepfakeDetector] = None


def get_video_detector() -> VideoDeepfakeDetector:
    global _DETECTOR
    if _DETECTOR is None:
        _DETECTOR = VideoDeepfakeDetector()
    return _DETECTOR
