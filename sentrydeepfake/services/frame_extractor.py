"""Extract frames from video files using OpenCV."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from sentrydeepfake.config import (
    FRAME_INTERVAL_SEC,
    FRAME_SAMPLE_STRATEGY,
    MAX_FRAMES_TO_ANALYZE,
)
from sentrydeepfake.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class VideoMetadata:
    path: str
    width: int
    height: int
    fps: float
    frame_count: int
    duration_sec: float
    has_video: bool
    codec: str = ""


@dataclass
class ExtractedFrames:
    frames: List[np.ndarray] = field(default_factory=list)
    timestamps_sec: List[float] = field(default_factory=list)
    metadata: Optional[VideoMetadata] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and len(self.frames) > 0


def probe_video(path: Path) -> VideoMetadata:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        cap.release()
        return VideoMetadata(
            path=str(path),
            width=0,
            height=0,
            fps=0.0,
            frame_count=0,
            duration_sec=0.0,
            has_video=False,
        )
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC) or 0)
    codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)]).strip()
    duration = (frame_count / fps) if fps > 0 else 0.0
    cap.release()
    return VideoMetadata(
        path=str(path),
        width=width,
        height=height,
        fps=fps,
        frame_count=frame_count,
        duration_sec=duration,
        has_video=width > 0 and height > 0 and frame_count > 0,
        codec=codec,
    )


def extract_frames(path: Path, max_frames: Optional[int] = None) -> ExtractedFrames:
    """Decode video and return RGB frames for analysis."""
    meta = probe_video(path)
    if not meta.has_video:
        return ExtractedFrames(metadata=meta, error="No readable video stream found.")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return ExtractedFrames(metadata=meta, error="OpenCV could not open the video file.")

    limit = max_frames or MAX_FRAMES_TO_ANALYZE
    try:
        frame_count = meta.frame_count
        fps = meta.fps
        if frame_count <= 0:
            cap.release()
            return ExtractedFrames(metadata=meta, error="Video reports zero frames.")

        if frame_count <= limit:
            indices = list(range(frame_count))
        elif FRAME_SAMPLE_STRATEGY == "interval" and fps > 0:
            step = max(1, int(round(fps * FRAME_INTERVAL_SEC)))
            indices = list(range(0, frame_count, step))[:limit]
        else:
            positions = np.linspace(0, frame_count - 1, num=limit)
            indices = sorted({int(round(p)) for p in positions})

        frames: List[np.ndarray] = []
        timestamps: List[float] = []
        index_set = set(indices)
        current = 0
        while True:
            ok, bgr = cap.read()
            if not ok:
                break
            if current in index_set:
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                frames.append(rgb)
                ts = (current / fps) if fps > 0 else float(current)
                timestamps.append(float(ts))
                if len(frames) >= len(indices):
                    break
            current += 1
        cap.release()

        if not frames:
            return ExtractedFrames(metadata=meta, error="Failed to decode any frames.")

        logger.info(
            "extracted_frames count=%s duration=%.2f path_suffix=%s",
            len(frames),
            meta.duration_sec,
            path.suffix,
        )
        return ExtractedFrames(frames=frames, timestamps_sec=timestamps, metadata=meta)
    except Exception as exc:  # noqa: BLE001
        cap.release()
        logger.exception("frame_extraction_failed")
        return ExtractedFrames(metadata=meta, error=f"Frame extraction failed: {type(exc).__name__}")


def frame_to_jpeg_bytes(frame: np.ndarray, quality: int = 85) -> bytes:
    bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("JPEG encode failed")
    return buf.tobytes()


def resize_for_preview(frame: np.ndarray, max_width: int = 480) -> np.ndarray:
    h, w = frame.shape[:2]
    if w <= max_width:
        return frame
    scale = max_width / w
    return cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
