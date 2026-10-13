"""Live / near-live frame sampling mode.

This mode samples occasional webcam frames or analyzes a short recorded clip.
It is NOT continuous real-time deepfake detection unless explicitly stated.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from sentrydeepfake.config import APP_NAME, LIVE_SAMPLE_INTERVAL_SEC
from sentrydeepfake.services.frame_extractor import ExtractedFrames, VideoMetadata
from sentrydeepfake.services.risk_engine import assess_risk
from sentrydeepfake.services.audio_detector import AudioDetectionResult
from sentrydeepfake.services.sync_analyzer import SyncAnalysisResult
from sentrydeepfake.services.video_detector import get_video_detector
from sentrydeepfake.ui.components import render_brand, render_risk, render_video_metrics
from sentrydeepfake.ui.styles import inject_styles

st.set_page_config(page_title=f"Live · {APP_NAME}", layout="wide")
st.markdown(inject_styles(), unsafe_allow_html=True)

render_brand()
st.markdown("### Live analysis mode")
st.info(
    "This mode performs **periodic frame sampling**, not continuous real-time deepfake detection. "
    "There is no Zoom / Meet / phone-call integration in this MVP."
)

detector = get_video_detector()
if not detector.is_available:
    st.warning(
        "Video model unavailable — live scoring cannot run. "
        f"{detector.load_error or ''} "
        "Use recorded-video analysis on the Dashboard, or Demo Mode for a simulated walkthrough."
    )
    st.markdown(
        """
        #### Future extension
        - Continuous streaming inference with GPU acceleration
        - Meeting-client plugins (Zoom / Meet) after proper SDK integration and testing
        - On-device edge models for lower latency
        """
    )
    st.stop()

st.caption(
    f"Configured sample interval: **{LIVE_SAMPLE_INTERVAL_SEC:.1f}s** · "
    f"Model: `{detector.model_id}`"
)

mode = st.radio(
    "Capture method",
    options=["Webcam snapshot sampling", "Recorded short clip (recommended if webcam blocked)"],
    index=1,
)

if "live_history" not in st.session_state:
    st.session_state.live_history = []
if "last_live_ts" not in st.session_state:
    st.session_state.last_live_ts = None
if "last_live_result" not in st.session_state:
    st.session_state.last_live_result = None


def score_rgb_frames(frames: list[np.ndarray]) -> None:
    meta = VideoMetadata(
        path="live",
        width=frames[0].shape[1],
        height=frames[0].shape[0],
        fps=0.0,
        frame_count=len(frames),
        duration_sec=0.0,
        has_video=True,
    )
    extracted = ExtractedFrames(
        frames=frames,
        timestamps_sec=[float(i) for i in range(len(frames))],
        metadata=meta,
    )
    t0 = time.perf_counter()
    video = detector.analyze_frames(extracted)
    latency = (time.perf_counter() - t0) * 1000
    audio = AudioDetectionResult(
        status="skipped",
        model_id="(n/a)",
        model_loaded=False,
        notes=["Live mode does not run audio spoof detection."],
    )
    sync = SyncAnalysisResult(
        status="skipped",
        method="n/a",
        interpretation="Sync analysis requires a full A/V file.",
    )
    risk = assess_risk(video, audio, sync)
    st.session_state.last_live_result = {
        "video": video,
        "risk": risk,
        "latency_ms": latency,
    }
    st.session_state.last_live_ts = datetime.now(timezone.utc).isoformat()
    st.session_state.live_history.append(
        {
            "timestamp_utc": st.session_state.last_live_ts,
            "risk": risk.category,
            "mean_fake": video.mean_fake_score,
            "frames": video.frames_analyzed,
            "latency_ms": round(latency, 1),
            "status": video.status,
        }
    )


if mode.startswith("Webcam"):
    st.caption("Uses the browser/OS camera once per sample. Grant permission if prompted.")
    cam = st.camera_input("Capture a frame for analysis")
    if cam is not None:
        image = Image.open(cam).convert("RGB")
        frame = np.array(image)
        st.image(frame, caption="Captured frame", width=420)
        if st.button("Analyze captured frame", type="primary"):
            with st.spinner("Running model on captured frame…"):
                score_rgb_frames([frame])
else:
    clip = st.file_uploader("Upload a short recorded clip", type=["mp4", "webm", "mov", "avi"])
    if clip is not None:
        st.video(clip.getvalue())
        if st.button("Sample frames & analyze", type="primary"):
            tmp = ROOT / ".tmp" / f"live_{int(time.time())}.mp4"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(clip.getvalue())
            try:
                cap = cv2.VideoCapture(str(tmp))
                frames = []
                count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
                # Sample up to 6 frames
                indices = [0]
                if count > 1:
                    import numpy as _np

                    indices = sorted({int(x) for x in _np.linspace(0, count - 1, num=min(6, count))})
                idx_set = set(indices)
                i = 0
                while True:
                    ok, bgr = cap.read()
                    if not ok:
                        break
                    if i in idx_set:
                        frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
                    i += 1
                cap.release()
                if not frames:
                    st.error("Could not decode frames from the clip.")
                else:
                    with st.spinner(f"Analyzing {len(frames)} sampled frames…"):
                        score_rgb_frames(frames)
            finally:
                tmp.unlink(missing_ok=True)

result = st.session_state.last_live_result
if result is None:
    st.caption("No live sample analyzed yet.")
else:
    st.markdown(
        f"**Last analysis:** `{st.session_state.last_live_ts}` · "
        f"latency `{result['latency_ms']:.0f} ms`"
    )
    render_risk(result["risk"])
    render_video_metrics(result["video"], total_latency_ms=result["latency_ms"])

st.markdown("#### Live session samples")
if st.session_state.live_history:
    st.dataframe(st.session_state.live_history[::-1], use_container_width=True, hide_index=True)
else:
    st.caption("History will appear after each sample.")
