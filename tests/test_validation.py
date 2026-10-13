"""Tests for upload validation."""

from sentrydeepfake.config import MAX_VIDEO_BYTES
from sentrydeepfake.utils.validation import (
    validate_audio_bytes,
    validate_duration,
    validate_video_bytes,
)


def test_valid_video_upload():
    result = validate_video_bytes("clip.mp4", b"fakebytes")
    assert result.ok
    assert result.extension == ".mp4"


def test_invalid_video_extension():
    result = validate_video_bytes("notes.txt", b"hello")
    assert not result.ok
    assert "Unsupported" in (result.error or "")


def test_empty_video():
    result = validate_video_bytes("clip.mp4", b"")
    assert not result.ok


def test_oversized_video():
    data = b"x" * (MAX_VIDEO_BYTES + 1)
    result = validate_video_bytes("clip.mp4", data)
    assert not result.ok
    assert "maximum size" in (result.error or "")


def test_duration_limits():
    assert validate_duration(10.0).ok
    assert not validate_duration(0).ok
    assert not validate_duration(None).ok
    assert not validate_duration(10_000).ok


def test_audio_validation():
    assert validate_audio_bytes("a.wav", b"abc").ok
    assert not validate_audio_bytes("a.txt", b"abc").ok
