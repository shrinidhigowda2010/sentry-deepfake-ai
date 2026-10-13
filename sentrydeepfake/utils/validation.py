"""Input validation for media uploads."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from sentrydeepfake.config import (
    ALLOWED_AUDIO_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_AUDIO_BYTES,
    MAX_VIDEO_BYTES,
    MAX_VIDEO_DURATION_SEC,
)


@dataclass
class ValidationResult:
    ok: bool
    error: Optional[str] = None
    extension: Optional[str] = None
    size_bytes: Optional[int] = None


def validate_video_bytes(filename: str, data: bytes) -> ValidationResult:
    if not filename:
        return ValidationResult(ok=False, error="Filename is required.")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        return ValidationResult(
            ok=False,
            error=f"Unsupported video type '{ext}'. Allowed: {sorted(ALLOWED_VIDEO_EXTENSIONS)}",
            extension=ext,
            size_bytes=len(data),
        )
    if len(data) == 0:
        return ValidationResult(ok=False, error="Uploaded file is empty.", extension=ext, size_bytes=0)
    if len(data) > MAX_VIDEO_BYTES:
        mb = MAX_VIDEO_BYTES / (1024 * 1024)
        return ValidationResult(
            ok=False,
            error=f"File exceeds maximum size of {mb:.0f} MB.",
            extension=ext,
            size_bytes=len(data),
        )
    return ValidationResult(ok=True, extension=ext, size_bytes=len(data))


def validate_audio_bytes(filename: str, data: bytes) -> ValidationResult:
    if not filename:
        return ValidationResult(ok=False, error="Filename is required.")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return ValidationResult(
            ok=False,
            error=f"Unsupported audio type '{ext}'. Allowed: {sorted(ALLOWED_AUDIO_EXTENSIONS)}",
            extension=ext,
            size_bytes=len(data),
        )
    if len(data) == 0:
        return ValidationResult(ok=False, error="Uploaded file is empty.", extension=ext, size_bytes=0)
    if len(data) > MAX_AUDIO_BYTES:
        mb = MAX_AUDIO_BYTES / (1024 * 1024)
        return ValidationResult(
            ok=False,
            error=f"File exceeds maximum size of {mb:.0f} MB.",
            extension=ext,
            size_bytes=len(data),
        )
    return ValidationResult(ok=True, extension=ext, size_bytes=len(data))


def validate_duration(duration_sec: Optional[float]) -> ValidationResult:
    if duration_sec is None:
        return ValidationResult(ok=False, error="Could not determine video duration.")
    if duration_sec <= 0:
        return ValidationResult(ok=False, error="Video duration must be greater than zero.")
    if duration_sec > MAX_VIDEO_DURATION_SEC:
        return ValidationResult(
            ok=False,
            error=f"Video exceeds maximum duration of {MAX_VIDEO_DURATION_SEC:.0f} seconds.",
        )
    return ValidationResult(ok=True)
