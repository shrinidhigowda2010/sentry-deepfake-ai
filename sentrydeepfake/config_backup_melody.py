"""Central configuration for SentryDeepfake AI."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
PACKAGE_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = PACKAGE_DIR / "samples"
ASSETS_DIR = PACKAGE_DIR / "assets"
TEMP_DIR = Path(os.getenv("SENTRY_TEMP_DIR", ROOT_DIR / ".tmp"))
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Video constraints
MAX_VIDEO_BYTES = int(os.getenv("SENTRY_MAX_VIDEO_MB", "100")) * 1024 * 1024
MAX_VIDEO_DURATION_SEC = float(os.getenv("SENTRY_MAX_DURATION_SEC", "120"))
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
ALLOWED_VIDEO_MIME_HINTS = {
    "video/mp4",
    "video/x-msvideo",
    "video/quicktime",
    "video/x-matroska",
    "video/webm",
}

# Frame sampling
MAX_FRAMES_TO_ANALYZE = int(os.getenv("SENTRY_MAX_FRAMES", "12"))
FRAME_SAMPLE_STRATEGY = os.getenv("SENTRY_FRAME_STRATEGY", "uniform")  # uniform | interval
FRAME_INTERVAL_SEC = float(os.getenv("SENTRY_FRAME_INTERVAL_SEC", "1.0"))

# Model — ViT image classifier trained on real vs deepfake faces
VIDEO_MODEL_ID = os.getenv(
    "SENTRY_VIDEO_MODEL_ID",
    "dima806/deepfake_vs_real_image_detection",
)
VIDEO_MODEL_DEVICE = os.getenv("SENTRY_DEVICE", "cpu")
FORCE_DEMO_MODE = os.getenv("SENTRY_FORCE_DEMO_MODE", "0") == "1"

# Audio
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
MAX_AUDIO_BYTES = int(os.getenv("SENTRY_MAX_AUDIO_MB", "30")) * 1024 * 1024
AUDIO_MODEL_ID = os.getenv("SENTRY_AUDIO_MODEL_ID", "MelodyMachine/Deepfake-audio-detection-V2")
AUDIO_ENABLED = os.getenv("SENTRY_AUDIO_ENABLED", "1") == "1"

# Risk engine thresholds (on fake-class probability aggregation)
RISK_FAKE_MEAN_SUSPICIOUS = float(os.getenv("SENTRY_RISK_FAKE_MEAN", "0.55"))
RISK_FAKE_MAX_SUSPICIOUS = float(os.getenv("SENTRY_RISK_FAKE_MAX", "0.75"))
RISK_UNCERTAIN_BAND = float(os.getenv("SENTRY_RISK_UNCERTAIN_BAND", "0.12"))

# Live sampling
LIVE_SAMPLE_INTERVAL_SEC = float(os.getenv("SENTRY_LIVE_INTERVAL_SEC", "3.0"))

# Branding / UI
APP_NAME = "SentryDeepfake AI"
APP_TAGLINE = "AI-powered deepfake & synthetic media risk detection"

# Privacy
STORE_UPLOADS = os.getenv("SENTRY_STORE_UPLOADS", "0") == "1"
EXTERNAL_PROCESSING = False  # all inference local unless model download
