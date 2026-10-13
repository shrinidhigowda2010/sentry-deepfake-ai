"""SentryDeepfake AI — main Streamlit application."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from sentrydeepfake.config import (
    ALLOWED_VIDEO_EXTENSIONS,
    APP_NAME,
    MAX_VIDEO_BYTES,
    MAX_VIDEO_DURATION_SEC,
)
from sentrydeepfake.services.pipeline import run_video_analysis
from sentrydeepfake.services.report_generator import report_to_json
from sentrydeepfake.services.sample_media import ensure_sample_videos
from sentrydeepfake.ui.components import (
    render_brand,
    render_evidence,
    render_frame_table,
    render_history,
    render_module_cards,
    render_privacy_status,
    render_report_downloads,
    render_risk,
    render_verification_panel,
    render_video_metrics,
)
from sentrydeepfake.ui.styles import inject_styles
from sentrydeepfake.utils.tempfiles import cleanup_path, new_session_dir

st.set_page_config(
    page_title=APP_NAME,
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(inject_styles(), unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []
if "last_bundle" not in st.session_state:
    st.session_state.last_bundle = None


def main() -> None:
    with st.sidebar:
        st.markdown(f"### {APP_NAME}")
        st.caption("Upload → analyze frames → explainable risk → verify")
        st.markdown("---")
        st.markdown("**Navigation**")
        st.page_link("app.py", label="Dashboard")
        st.page_link("pages/1_Demo_Mode.py", label="Demo Mode")
        st.page_link("pages/2_Live_Analysis.py", label="Live Analysis")
        st.markdown("---")
        st.caption(
            f"Max video: {MAX_VIDEO_BYTES // (1024*1024)} MB · "
            f"{MAX_VIDEO_DURATION_SEC:.0f}s · "
            f"Types: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}"
        )

    render_brand()
    render_privacy_status()

    st.markdown("### Analysis workspace")
    st.caption(
        "Upload a video for frame-level deepfake scoring. "
        "All metrics below come from actual computation unless marked as demo/simulated."
    )

    uploaded = st.file_uploader(
        "Video upload",
        type=[ext.lstrip(".") for ext in sorted(ALLOWED_VIDEO_EXTENSIONS)],
        help="Media is written to a temporary file, analyzed locally, then deleted.",
    )

    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        run_sync = st.checkbox("Run A/V sync heuristic", value=True)
    with col_b:
        use_sample = st.selectbox(
            "Or analyze labeled local sample",
            options=["—", "Genuine-role sample", "Manipulated-role sample"],
        )
    with col_c:
        analyze = st.button("Analyze video", type="primary", use_container_width=True)

    if uploaded is not None:
        st.video(uploaded.getvalue())

    if analyze:
        _run_analysis(uploaded, use_sample, run_sync)

    bundle = st.session_state.last_bundle
    if bundle is None:
        st.markdown(
            """
            <div class="panel">
              <h3>Session overview</h3>
              <p class="muted">No analysis yet. Upload a video or open Demo Mode for a guided walkthrough.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_history(st.session_state.history)
        return

    st.markdown("### Current analysis session")
    render_risk(bundle.risk)
    st.write("")
    render_video_metrics(bundle.video, total_latency_ms=bundle.total_latency_ms)
    st.write("")
    render_module_cards(bundle.video, bundle.audio, bundle.sync)
    render_frame_table(bundle.video)
    render_evidence(bundle.risk)
    render_verification_panel(bundle.risk)

    st.markdown("#### Detailed analysis report")
    with st.expander("View full report JSON", expanded=False):
        st.code(report_to_json(bundle.report), language="json")
    render_report_downloads(bundle.report)

    if bundle.video.limitations:
        with st.expander("Model limitations"):
            for lim in bundle.video.limitations:
                st.markdown(f"- {lim}")

    render_history(st.session_state.history)

    if st.button("Analyze another video"):
        st.session_state.last_bundle = None
        st.rerun()


def _run_analysis(uploaded, use_sample: str, run_sync: bool) -> None:
    progress = st.progress(0.0, text="Starting…")
    status = st.empty()

    def on_progress(p: float, msg: str) -> None:
        progress.progress(min(max(p, 0.0), 1.0), text=msg)
        status.caption(msg)

    session_dir = new_session_dir("ui")
    temp_path = None
    try:
        if use_sample != "—":
            genuine, manipulated = ensure_sample_videos()
            path = genuine if "Genuine" in use_sample else manipulated
            data = path.read_bytes()
            filename = path.name
            temp_path = path  # sample files are kept
            keep_temp = True
        elif uploaded is not None:
            data = uploaded.getvalue()
            filename = uploaded.name
            temp_path = session_dir / filename
            temp_path.write_bytes(data)
            keep_temp = False
        else:
            st.error("Provide an upload or choose a local sample.")
            return

        bundle = run_video_analysis(
            filename=filename,
            data=data,
            temp_path=temp_path,
            run_sync=run_sync,
            run_audio=True,
            progress=on_progress,
        )
        st.session_state.last_bundle = bundle
        st.session_state.history.append(bundle.history_entry)
        progress.progress(1.0, text="Complete")
        if bundle.video.status == "unavailable":
            st.warning(
                "Video model is unavailable. Open **Demo Mode** for a clearly labeled "
                "simulated walkthrough, or fix model download / dependencies."
            )
        elif bundle.video.status == "failed":
            st.error(bundle.video.error or "Analysis failed")
        else:
            st.success(f"Analysis complete — risk category: {bundle.risk.category}")
    finally:
        if temp_path is not None and use_sample == "—":
            cleanup_path(temp_path)
        cleanup_path(session_dir)


main()
