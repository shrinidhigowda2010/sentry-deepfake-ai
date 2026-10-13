"""Reference examples: AI videos (YouTube embeds) and AI voice samples (local TTS). Edit the lists freely."""
from pathlib import Path
import streamlit as st

# (title, YouTube URL) - all verified via YouTube oEmbed (HTTP 200)
AI_VIDEOS = [
    ("Introducing Sora (OpenAI)", "https://www.youtube.com/watch?v=HK6y8DAPN_0"),
    ("Introducing Sora 2 (OpenAI)", "https://www.youtube.com/watch?v=gzneGhpXwjU"),
    ("Sound on for Sora 2 (OpenAI)", "https://www.youtube.com/watch?v=1PaoWKvcJP0"),
    ("Veo 3.1 (Google DeepMind)", "https://www.youtube.com/watch?v=I06Ef8alr2Y"),
    ("Veo 2 compilation (Google DeepMind)", "https://www.youtube.com/watch?v=G9RDHs9nx04"),
    ("Veo 3 rollout (Google)", "https://www.youtube.com/watch?v=rwUt22HTTx0"),
    ("Gen-3 Alpha (Runway)", "https://www.youtube.com/watch?v=nByslCkykj8"),
    ("Introducing Gen-4 (Runway)", "https://www.youtube.com/watch?v=uRkfzKYFOxc"),
    ("In Event of Moon Disaster - Nixon deepfake (MIT)", "https://www.youtube.com/watch?v=LWLadJFI8Pk"),
    ("Obama deepfake PSA (BuzzFeed / Jordan Peele)", "https://www.youtube.com/watch?v=cQ54GDm1eL0"),
]

AUDIO_DIR = Path(__file__).resolve().parent.parent / "samples" / "audio"
# (title, file) - generated locally with Google Text-to-Speech (gTTS)
AI_VOICES = [
    ("Fake bank asking for OTP", "bank_otp.mp3"),
    ("Fake CEO urgent transfer", "ceo_transfer.mp3"),
    ("Fake family member in trouble", "family_help.mp3"),
    ("Fake job interviewer", "job_interview.mp3"),
    ("Fake KYC update", "kyc_update.mp3"),
    ("Fake police threat", "police_call.mp3"),
    ("Fake lottery prize", "lottery.mp3"),
    ("Fake tech support", "tech_support.mp3"),
    ("Fake friend asking for UPI money", "friend_upi.mp3"),
    ("Fake colleague in a meeting", "meeting_voice.mp3"),
]

BADGE = ("<span style='background:#B91C1C;color:#FFFFFF;font-weight:800;font-size:.8rem;"
         "padding:.2rem .6rem;border-radius:6px'>AI-GENERATED</span>")


def _title(col, t):
    col.markdown(f"<div class='panel' style='padding:.7rem;margin-bottom:.4rem'>{BADGE}"
                 f"<div style='color:#0F172A;font-weight:700;margin-top:.4rem'>{t}</div></div>",
                 unsafe_allow_html=True)


def show_video_examples():
    st.subheader("AI video examples")
    for i in range(0, len(AI_VIDEOS), 2):
        cols = st.columns(2)
        for col, (t, url) in zip(cols, AI_VIDEOS[i:i + 2]):
            _title(col, t)
            col.video(url)


class _Sample:
    def __init__(self, p):
        self.name, self._p = p.name, p

    def getvalue(self):
        return self._p.read_bytes()


def show_audio_examples(check_fn):
    st.subheader("AI voice examples")
    for i in range(0, len(AI_VOICES), 2):
        cols = st.columns(2)
        for col, (t, f) in zip(cols, AI_VOICES[i:i + 2]):
            p = AUDIO_DIR / f
            if not p.exists():
                continue
            _title(col, t)
            col.audio(str(p))
            if col.button("Check this sample", key=f"ex_{f}", use_container_width=True):
                with col:
                    check_fn(_Sample(p))
