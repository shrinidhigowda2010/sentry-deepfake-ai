"""SentryDeepfake AI - simple deepfake check screen."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import streamlit.components.v1 as components

from sentrydeepfake.config import ALLOWED_AUDIO_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS, APP_NAME
from sentrydeepfake.services.audio_detector import get_audio_detector
from sentrydeepfake.services.pipeline import run_video_analysis
from sentrydeepfake.ui.styles import inject_styles
from sentrydeepfake.utils.tempfiles import cleanup_path, new_session_dir

st.set_page_config(page_title=APP_NAME, page_icon=":shield:", layout="centered",
                   initial_sidebar_state="expanded")
st.markdown(inject_styles(), unsafe_allow_html=True)
st.markdown("<style>[data-testid='stSidebarNav']{display:none;}</style>", unsafe_allow_html=True)

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


from sentrydeepfake.ui.hero3d import CSS_3D, HERO_HTML
st.markdown(CSS_3D, unsafe_allow_html=True)
components.html(HERO_HTML, height=260)


def check_audio(up):
    session_dir = new_session_dir("ui")
    temp_path = session_dir / up.name
    try:
        from sentrydeepfake.utils.validation import validate_audio_bytes
        data = up.getvalue()
        v = validate_audio_bytes(up.name, data)
        if not v.ok:
            st.error(f"Could not check this audio. {v.error}")
            return
        temp_path.write_bytes(data)
        with st.spinner("Checking voice..."):
            a = get_audio_detector().analyze_audio_path(temp_path)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not check this audio: {type(exc).__name__}: {exc}")
        return
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
        f"<div class='result3d' style='background-color:{color};padding:1.4rem;border-radius:12px;text-align:center'>"
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


from sentrydeepfake.ui.about import show_about
from sentrydeepfake.ui.screen_fill import AUDIO_CHECKS, AUDIO_SAMPLES, VIDEO_CHECKS, VIDEO_SAMPLES, sample_buttons, show_header
from sentrydeepfake.ui.examples import show_audio_examples, show_video_examples
st.markdown("""<style>
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1E3A8A,#0F172A) !important;min-width:230px !important;max-width:230px !important;}
[data-testid="stSidebar"] *{color:#FFFFFF !important;}
[data-testid="stSidebar"] div[role="radiogroup"]{display:flex !important;flex-direction:column;gap:16px;margin-top:10px;}
[data-testid="stSidebar"] div[role="radiogroup"] > label{aspect-ratio:1/1;width:100%;display:flex !important;align-items:center;justify-content:center !important;
 background:linear-gradient(145deg,#2563EB,#1E40AF) !important;border:2px solid #60A5FA !important;border-radius:18px !important;margin:0 !important;
 box-shadow:0 7px 0 #172554,0 12px 22px rgba(0,0,0,.35);cursor:pointer;transition:transform .15s,box-shadow .15s;}
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover{transform:translateY(-3px) scale(1.03);}
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child{display:none !important;}
[data-testid="stSidebar"] div[role="radiogroup"] > label p{font-size:1.35rem !important;font-weight:800 !important;text-align:center;white-space:pre-line;line-height:1.5;}
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked){background:linear-gradient(145deg,#22D3EE,#0EA5E9) !important;border-color:#FFFFFF !important;transform:translateY(3px);box-shadow:0 3px 0 #0C4A6E;}
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p{color:#0F172A !important;}
[data-testid="stSidebarCollapseButton"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"],[data-testid="stSidebarHeader"] button{display:none !important;}
[data-testid="stSidebar"]{transform:none !important;visibility:visible !important;position:relative !important;}
[data-testid="stSidebar"][aria-expanded="false"]{margin-left:0 !important;width:230px !important;}
[data-testid="stSidebar"] div[role="radiogroup"] > label p{font-size:1.75rem !important;font-weight:900 !important;letter-spacing:.06em;text-transform:uppercase;text-shadow:0 2px 6px rgba(0,0,0,.45);}
[data-testid="stSidebar"] h3{font-size:1.5rem !important;font-weight:900 !important;text-align:center;}
</style>""", unsafe_allow_html=True)
_MENU = {"ℹ️\nAbout": "About", "🎬\nVideo": "Video", "🎙️\nAudio": "Audio", "🖼️\nGallery": "Gallery", "🔴\nLive": "Live"}
with st.sidebar:
    st.markdown("### 🛡️ SentryDeepfake")
    _pick = st.radio("Menu", list(_MENU), label_visibility="collapsed")
mode = _MENU[_pick]

if mode == "Live":
    from sentrydeepfake.ui.live import show_live
    show_live()
elif mode == "About":
    show_about()
elif mode == "Gallery":
    show_video_examples()
    st.write("")
    show_audio_examples(check_audio)
elif mode == "Audio":
    show_header(AUDIO_CHECKS)
    up = st.file_uploader("Upload an audio file",
                          type=[e.lstrip(".") for e in sorted(ALLOWED_AUDIO_EXTENSIONS)])
    smp = sample_buttons(AUDIO_SAMPLES, "aud")
    run_now = smp is not None
    if run_now:
        up = smp
    if up is not None:
        st.audio(up.getvalue())
        clicked = st.button("Check audio", type="primary", use_container_width=True)
        if clicked or run_now:
            check_audio(up)
    st.caption("See AI examples in the Gallery tab.")
else:
    show_header(VIDEO_CHECKS)
    uploaded = st.file_uploader(
        "Upload a video",
        type=[ext.lstrip(".") for ext in sorted(ALLOWED_VIDEO_EXTENSIONS)],
    )

    smp = sample_buttons(VIDEO_SAMPLES, "vid")
    run_now = smp is not None
    if run_now:
        uploaded = smp
    if uploaded is not None:
        st.video(uploaded.getvalue())
        clicked = st.button("Check video", type="primary", use_container_width=True)
        if clicked or run_now:
            session_dir = new_session_dir("ui")
            temp_path = session_dir / uploaded.name
            try:
                data = uploaded.getvalue()
                temp_path.write_bytes(data)
                with st.spinner("Checking video, voice and lip-sync..."):
                    b = run_video_analysis(filename=uploaded.name, data=data, temp_path=temp_path,
                                           run_sync=True, run_audio=True, progress=None)
                if b.video.status in ("unavailable", "failed"):
                    st.error(f"Could not check this video. {b.video.error or 'Please try another file.'}")
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
                    f"<div class='result3d' style='background-color:{color};padding:1.4rem;border-radius:12px;text-align:center'>"
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
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not check this video: {type(exc).__name__}: {exc}")
            finally:
                cleanup_path(temp_path)
                cleanup_path(session_dir)
    st.caption("See AI examples in the Gallery tab.")
