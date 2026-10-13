"""SentryDeepfake AI - simple deepfake check screen."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from sentrydeepfake.config import ALLOWED_AUDIO_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS, APP_NAME
from sentrydeepfake.services.audio_detector import get_audio_detector
from sentrydeepfake.services.pipeline import run_video_analysis
from sentrydeepfake.ui.styles import inject_styles
from sentrydeepfake.utils.tempfiles import cleanup_path, new_session_dir

st.set_page_config(page_title=APP_NAME, page_icon=":shield:", layout="centered",
                   initial_sidebar_state="collapsed")
st.markdown(inject_styles(), unsafe_allow_html=True)
st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarNav'],"
            "[data-testid='collapsedControl']{display:none;}</style>", unsafe_allow_html=True)

RED, GREEN, AMBER, GREY = "#B91C1C", "#15803D", "#B45309", "#475569"
RESULTS = {
    "SUSPICIOUS": ("AI-GENERATED / FAKE", RED),
    "LOWER RISK": ("LIKELY REAL", GREEN),
    "INCONCLUSIVE": ("NOT SURE", AMBER),
}


def level(score):
    if score is None:
        return "Not available", GREY
    if score >= 0.6:
        return f"Suspicious ({score*100:.0f}% AI)", RED
    if score >= 0.4:
        return f"Unclear ({score*100:.0f}% AI)", AMBER
    return f"Looks real ({score*100:.0f}% AI)", GREEN


def card(col, title, text, color):
    col.markdown(
        f"<div class='panel' style='border-top:5px solid {color};text-align:center'>"
        f"<h3>{title}</h3><p style='color:{color};font-weight:700;margin:0'>{text}</p></div>",
        unsafe_allow_html=True,
    )


st.title(APP_NAME)


def check_audio(up):
    session_dir = new_session_dir("ui")
    temp_path = session_dir / up.name
    try:
        temp_path.write_bytes(up.getvalue())
        with st.spinner("Checking voice..."):
            a = get_audio_detector().analyze_audio_path(temp_path)
    finally:
        cleanup_path(temp_path)
        cleanup_path(session_dir)
    if a.status != "success" or a.spoof_score is None:
        st.error(f"Could not check this audio. {a.error or ''}")
        return
    s = a.spoof_score
    if s >= 0.6:
        label, color = "AI-GENERATED VOICE", RED
        st.error("ALERT: This voice may be AI-generated or cloned. Do not share money, OTPs or "
                 "personal details. Call the person back on a number you trust.")
    elif s < 0.4:
        label, color = "LIKELY REAL VOICE", GREEN
    else:
        label, color = "NOT SURE", AMBER
        st.warning("Caution: we could not confirm this voice is real. Take extra precautions.")
    st.markdown(
        f"<div style='background:{color};padding:1.4rem;border-radius:12px;text-align:center'>"
        f"<div style='color:#FFFFFF;font-size:2rem;font-weight:800'>{label}</div>"
        f"<div style='color:#FFFFFF;font-size:1.1rem'>Risk score: {round(s*100)}/100</div></div>",
        unsafe_allow_html=True,
    )
    st.subheader("Why this result")
    segs = a.metadata.get("segment_scores", [])
    st.markdown(f"- AI voice model says **{s*100:.0f}%** chance the voice is AI-generated.")
    if len(segs) > 1:
        hi = sum(1 for x in segs if x >= 0.6)
        st.markdown(f"- {hi} of {len(segs)} parts of the clip sound AI-generated.")
    st.markdown(f"- {a.metadata.get('duration_sec', 0):.0f} seconds of audio checked. "
                "Short or noisy clips are less reliable.")


mode = st.radio("What do you want to check?", ["Video", "Audio"], horizontal=True)

if mode == "Audio":
    up = st.file_uploader("Upload an audio file",
                          type=[e.lstrip(".") for e in sorted(ALLOWED_AUDIO_EXTENSIONS)])
    if up is not None:
        st.audio(up.getvalue())
        if st.button("Check audio", type="primary", use_container_width=True):
            check_audio(up)
else:
    uploaded = st.file_uploader(
        "Upload a video",
        type=[ext.lstrip(".") for ext in sorted(ALLOWED_VIDEO_EXTENSIONS)],
    )

    if uploaded is not None:
        st.video(uploaded.getvalue())
        if st.button("Check video", type="primary", use_container_width=True):
            session_dir = new_session_dir("ui")
            temp_path = session_dir / uploaded.name
            try:
                data = uploaded.getvalue()
                temp_path.write_bytes(data)
                with st.spinner("Checking video, voice and lip-sync..."):
                    b = run_video_analysis(filename=uploaded.name, data=data, temp_path=temp_path,
                                           run_sync=True, run_audio=True, progress=None)
                if b.video.status in ("unavailable", "failed"):
                    st.error("Could not check this video. Please try another file.")
                    st.stop()

                # Instant alert
                if b.risk.category == "SUSPICIOUS":
                    st.error("ALERT: This video may be a deepfake. Do not share money, OTPs or personal "
                             "details. Verify the person through another trusted channel.")
                elif b.risk.category == "INCONCLUSIVE":
                    st.warning("Caution: we could not confirm this video is real. Take extra precautions.")

                # Overall result + risk score
                label, color = RESULTS.get(b.risk.category, ("NOT SURE", AMBER))
                scores = [s for s in (b.video.mean_fake_score,
                                      b.audio.spoof_score if b.audio else None) if s is not None]
                risk = round(max(scores) * 100) if scores else None
                score_txt = f"Risk score: {risk}/100" if risk is not None else ""
                st.markdown(
                    f"<div style='background:{color};padding:1.4rem;border-radius:12px;text-align:center'>"
                    f"<div style='color:#FFFFFF;font-size:2rem;font-weight:800'>{label}</div>"
                    f"<div style='color:#FFFFFF;font-size:1.1rem'>{score_txt}</div></div>",
                    unsafe_allow_html=True,
                )
                st.write("")

                # Three checks
                c1, c2, c3 = st.columns(3)
                card(c1, "Video Analysis", *level(b.video.mean_fake_score))
                card(c2, "Voice Analysis",
                     *level(b.audio.spoof_score if b.audio and b.audio.status == "success" else None))
                if b.sync and b.sync.status == "success" and b.sync.correlation is not None:
                    ok = b.sync.correlation >= 0.3
                    card(c3, "Audio-Video Match", "Lips match voice" if ok else "Lips do not match voice",
                         GREEN if ok else RED)
                else:
                    card(c3, "Audio-Video Match", "Not available", GREY)

                # Explainable warning indicators
                reasons = b.risk.evidence or b.risk.contributing_signals
                if reasons:
                    st.subheader("Why this result")
                    for r in reasons[:5]:
                        st.markdown(f"- {r}")
            finally:
                cleanup_path(temp_path)
                cleanup_path(session_dir)
