"""Visual fill for Video/Audio screens: check cards, how-it-works strip, upload zone, sample buttons."""
from pathlib import Path
import streamlit as st

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
VIDEO_CHECKS = [("🎞️", "Face frames"), ("🎙️", "Voice"), ("👄", "Lip-sync"), ("📊", "Risk score")]
AUDIO_CHECKS = [("🧬", "Voice clone"), ("🎚️", "Tone / pitch"), ("📊", "Risk score")]
VIDEO_SAMPLES = [("Genuine sample", "sample_genuine_labeled.mp4"),
                 ("Manipulated sample", "sample_manipulated_labeled.mp4")]
AUDIO_SAMPLES = [("AI bank OTP call", "audio/bank_otp.mp3"), ("AI CEO transfer", "audio/ceo_transfer.mp3"),
                 ("AI family scam", "audio/family_help.mp3")]

CSS = """<style>
[data-testid='stFileUploaderDropzone']{min-height:170px;border:3px dashed #1D4ED8!important;
 background:linear-gradient(160deg,#EFF6FF,#DBEAFE)!important;border-radius:16px!important;
 box-shadow:0 10px 24px rgba(29,78,216,.18);justify-content:center}
[data-testid='stFileUploaderDropzone']::before{content:'⬆';font-size:2.6rem;color:#1D4ED8;margin-right:1rem}
.chk{background:#FFFFFF;border-radius:14px;padding:.8rem;text-align:center;border-top:5px solid #1D4ED8;
 box-shadow:0 8px 18px rgba(15,23,42,.15);transition:transform .25s}
.chk:hover{transform:perspective(600px) rotateX(5deg) translateY(-5px)}
.chk .i{font-size:1.9rem}.chk .t{color:#0F172A;font-weight:800}
.steps{display:flex;gap:.5rem;align-items:center;justify-content:center;margin:.8rem 0}
.step{background:#1E3A8A;color:#FFFFFF;font-weight:800;padding:.6rem 1rem;border-radius:12px;
 box-shadow:0 8px 16px rgba(30,58,138,.35)}.arr{color:#1E3A8A;font-size:1.5rem;font-weight:900}
</style>"""


class Sample:
    def __init__(self, p):
        self.name, self._p = p.name, p

    def getvalue(self):
        return self._p.read_bytes()


def show_header(checks):
    st.markdown(CSS, unsafe_allow_html=True)
    cols = st.columns(len(checks))
    for c, (i, t) in zip(cols, checks):
        c.markdown(f"<div class='chk'><div class='i'>{i}</div><div class='t'>{t}</div></div>",
                   unsafe_allow_html=True)
    st.markdown("<div class='steps'><span class='step'>① Upload</span><span class='arr'>➜</span>"
                "<span class='step'>② Analyze</span><span class='arr'>➜</span>"
                "<span class='step'>③ Get result</span></div>", unsafe_allow_html=True)


def sample_buttons(items, key):
    st.markdown("**Try a sample**")
    cols = st.columns(len(items))
    for c, (label, f) in zip(cols, items):
        p = SAMPLES / f
        if p.exists() and c.button(label, key=f"{key}_{f}", use_container_width=True):
            st.session_state[f"{key}_sample"] = str(p)
            return Sample(p)
    return None
