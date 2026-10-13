"""Generate properly labeled local sample videos for offline demos."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import cv2
import numpy as np

from sentrydeepfake.config import SAMPLES_DIR


def ensure_sample_videos() -> Tuple[Path, Path]:
    """Create short labeled sample clips if missing. Returns (genuine_path, manipulated_path)."""
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    genuine = SAMPLES_DIR / "sample_genuine_labeled.mp4"
    manipulated = SAMPLES_DIR / "sample_manipulated_labeled.mp4"
    readme = SAMPLES_DIR / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Sample media\n\n"
            "These clips are **synthetic procedural videos generated locally** for UI and pipeline testing.\n"
            "They are **not** real deepfake datasets and carry no claim of depicting real persons.\n"
            "Labels indicate intended demo roles only.\n",
            encoding="utf-8",
        )
    if not genuine.exists():
        _write_clip(genuine, kind="genuine")
    if not manipulated.exists():
        _write_clip(manipulated, kind="manipulated")
    return genuine, manipulated


def _write_clip(path: Path, kind: str, seconds: float = 3.0, fps: int = 10) -> None:
    w, h = 320, 240
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (w, h))
    n = int(seconds * fps)
    rng = np.random.default_rng(42 if kind == "genuine" else 99)
    for i in range(n):
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        if kind == "genuine":
            # Stable "face-like" oval with subtle natural motion
            frame[:] = (30, 40, 55)
            cx, cy = 160 + int(3 * np.sin(i / 5)), 110
            cv2.ellipse(frame, (cx, cy), (55, 70), 0, 0, 360, (190, 160, 140), -1)
            cv2.circle(frame, (cx - 18, cy - 15), 6, (40, 40, 40), -1)
            cv2.circle(frame, (cx + 18, cy - 15), 6, (40, 40, 40), -1)
            mouth_open = 3 + int(2 * abs(np.sin(i / 3)))
            cv2.ellipse(frame, (cx, cy + 25), (18, mouth_open), 0, 0, 360, (80, 50, 50), -1)
            label = "LABEL: GENUINE-ROLE SAMPLE (procedural)"
            color = (80, 200, 120)
        else:
            # High-frequency flicker / color shifts to stress-test classifiers
            frame[:] = (
                int(40 + 80 * abs(np.sin(i / 2))),
                int(20 + 60 * abs(np.cos(i / 3))),
                int(90 + 50 * abs(np.sin(i / 1.5))),
            )
            cx, cy = 160 + int(10 * np.sin(i)), 110 + int(6 * np.cos(i / 2))
            cv2.ellipse(frame, (cx, cy), (55, 70), 0, 0, 360, (170, 140, 200), -1)
            # Asymmetric / jittery facial features
            cv2.circle(frame, (cx - 18 + int(rng.integers(-2, 3)), cy - 15), 6, (10, 10, 10), -1)
            cv2.circle(frame, (cx + 22, cy - 12), 8, (10, 10, 10), -1)
            cv2.ellipse(
                frame,
                (cx, cy + 28),
                (20, 2 + (i % 7)),
                float(i * 5),
                0,
                360,
                (20, 20, 80),
                -1,
            )
            noise = rng.integers(0, 40, size=frame.shape, dtype=np.uint8)
            frame = cv2.add(frame, noise)
            label = "LABEL: MANIPULATED-ROLE SAMPLE (procedural)"
            color = (60, 60, 220)
        cv2.putText(frame, label, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1, cv2.LINE_AA)
        cv2.putText(
            frame,
            "Not a real person | local test asset",
            (8, h - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (200, 200, 200),
            1,
            cv2.LINE_AA,
        )
        writer.write(frame)
    writer.release()
