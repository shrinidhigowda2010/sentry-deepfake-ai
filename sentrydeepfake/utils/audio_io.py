"""Decode audio from any audio/video file using a bundled ffmpeg (imageio-ffmpeg).
No system ffmpeg or sudo needed."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


def ffmpeg_exe() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def load_audio(path: Path, sr: int = 16000, max_sec: Optional[float] = None) -> Tuple[np.ndarray, int]:
    """Return mono float32 samples at `sr`. Raises RuntimeError if no audio track."""
    cmd = [ffmpeg_exe(), "-nostdin", "-v", "error", "-i", str(path), "-vn"]
    if max_sec:
        cmd += ["-t", str(max_sec)]
    cmd += ["-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    proc = subprocess.run(cmd, capture_output=True, timeout=120)
    err = proc.stderr.decode(errors="ignore")
    if proc.returncode != 0 and ("does not contain any stream" in err or "matches no streams" in err):
        raise RuntimeError("No audio track found in file.")
    if proc.returncode != 0:
        raise RuntimeError(err.strip()[-300:] or "ffmpeg failed")
    y = np.frombuffer(proc.stdout, dtype=np.float32).copy()
    if y.size == 0:
        raise RuntimeError("No audio track found in file.")
    return y, sr
