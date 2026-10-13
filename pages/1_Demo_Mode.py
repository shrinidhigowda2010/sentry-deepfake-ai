"""Dedicated demonstration page for the ideathon."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from sentrydeepfake.config import APP_NAME
from sentrydeepfake.services.demo_data import (
    SIMULATION_BANNER,
    comparison_rows,
    explain_verification_need,
    simulated_genuine_bundle,
    simulated_manipulated_bundle,
)
from sentrydeepfake.services.pipeline import run_video_analysis
from sentrydeepfake.services.report_generator import report_to_json
from sentrydeepfake.services.sample_media import ensure_sample_videos
from sentrydeepfake.services.video_detector import get_video_detector
from sentrydeepfake.ui.components import (
    render_brand,
    render_evidence,
    render_frame_table,
    render_module_cards,
    render_report_downloads,
    render_risk,
    render_verification_panel,
    render_video_metrics,
)
from sentrydeepfake.ui.styles import inject_styles

st.set_page_config(page_title=f"Demo · {APP_NAME}", layout="wide")
st.markdown(inject_styles(), unsafe_allow_html=True)

render_brand()
st.markdown("### Demonstration mode")
st.caption(
    "Compare a genuine-role sample and a manipulated-role sample. "
    "When the live model is available, analysis uses real inference on local procedural clips. "
    "Otherwise results are shown as simulated demo data."
)

detector = get_video_detector()
live_ok = detector.is_available

if live_ok:
    st.success(f"Live model available: `{detector.model_id}` — demo will run real inference on sample clips.")
else:
    st.markdown(f'<div class="sim-banner">{SIMULATION_BANNER}</div>', unsafe_allow_html=True)
    st.warning(
        "Model inference is unavailable in this environment. "
        "Showing clearly labeled simulated outputs so the demo remains offline-resilient."
    )
    if detector.load_error:
        st.caption(f"Load error: {detector.load_error}")

mode = st.radio(
    "Demo path",
    options=[
        "Live inference on local samples" if live_ok else "Live inference (unavailable)",
        "Simulated comparison (always works offline)",
    ],
    index=0 if live_ok else 1,
)

genuine_path, manipulated_path = ensure_sample_videos()

c1, c2 = st.columns(2)
with c1:
    st.markdown("#### Genuine-role sample")
    st.caption("Procedural local asset · labeled for demo · not a real person")
    st.video(str(genuine_path))
with c2:
    st.markdown("#### Manipulated-role sample")
    st.caption("Procedural local asset · labeled for demo · not a real person")
    st.video(str(manipulated_path))

run = st.button("Re-run demonstration analysis", type="primary", use_container_width=True)

if "demo_genuine" not in st.session_state:
    st.session_state.demo_genuine = None
    st.session_state.demo_manipulated = None
    st.session_state.demo_simulated = None


def _live_bundle(path: Path):
    data = path.read_bytes()
    return run_video_analysis(
        filename=path.name,
        data=data,
        temp_path=path,
        run_sync=True,
        run_audio=True,
    )


if run:
    if mode.startswith("Live") and live_ok:
        with st.spinner("Running live inference on genuine-role sample…"):
            g = _live_bundle(genuine_path)
        with st.spinner("Running live inference on manipulated-role sample…"):
            m = _live_bundle(manipulated_path)
        st.session_state.demo_genuine = g
        st.session_state.demo_manipulated = m
        st.session_state.demo_simulated = False
    else:
        st.session_state.demo_genuine = simulated_genuine_bundle()
        st.session_state.demo_manipulated = simulated_manipulated_bundle()
        st.session_state.demo_simulated = True

g = st.session_state.demo_genuine
m = st.session_state.demo_manipulated

if g is None or m is None:
    st.info("Click **Re-run demonstration analysis** to generate comparable results.")
    st.stop()

if st.session_state.demo_simulated:
    st.markdown(f'<div class="sim-banner">{SIMULATION_BANNER}</div>', unsafe_allow_html=True)
    # Simulated bundles are dicts
    st.markdown("### Comparison")
    st.dataframe(comparison_rows(g, m), use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        st.markdown("#### Genuine-looking (simulated)")
        render_risk(g["risk"])
        render_video_metrics(g["video"])
        render_module_cards(g["video"], g["audio"], g["sync"])
        render_frame_table(g["video"])
        render_report_downloads(g["report"])
    with right:
        st.markdown("#### Manipulated (simulated)")
        render_risk(m["risk"])
        render_video_metrics(m["video"])
        render_module_cards(m["video"], m["audio"], m["sync"])
        render_frame_table(m["video"])
        render_report_downloads(m["report"])
else:
    st.markdown("### Live model comparison")
    st.dataframe(
        [
            {
                "sample": "Genuine-role",
                "risk": g.risk.category,
                "video_status": g.video.status,
                "aggregate": g.video.aggregate_label,
                "mean_fake": g.video.mean_fake_score,
                "max_fake": g.video.max_fake_score,
                "sync_corr": g.sync.correlation,
                "simulated": False,
            },
            {
                "sample": "Manipulated-role",
                "risk": m.risk.category,
                "video_status": m.video.status,
                "aggregate": m.video.aggregate_label,
                "mean_fake": m.video.mean_fake_score,
                "max_fake": m.video.max_fake_score,
                "sync_corr": m.sync.correlation,
                "simulated": False,
            },
        ],
        use_container_width=True,
        hide_index=True,
    )
    left, right = st.columns(2)
    with left:
        st.markdown("#### Genuine-role · live outputs")
        render_risk(g.risk)
        render_video_metrics(g.video, g.total_latency_ms)
        render_module_cards(g.video, g.audio, g.sync)
        render_frame_table(g.video)
        render_evidence(g.risk)
        render_report_downloads(g.report)
    with right:
        st.markdown("#### Manipulated-role · live outputs")
        render_risk(m.risk)
        render_video_metrics(m.video, m.total_latency_ms)
        render_module_cards(m.video, m.audio, m.sync)
        render_frame_table(m.video)
        render_evidence(m.risk)
        render_report_downloads(m.report)

st.markdown("### Why additional verification may be necessary")
for item in explain_verification_need():
    st.markdown(f"- {item}")

# Attach verification panel using the higher-risk of the two when possible
if st.session_state.demo_simulated:
    render_verification_panel(m["risk"])
else:
    render_verification_panel(m.risk)
