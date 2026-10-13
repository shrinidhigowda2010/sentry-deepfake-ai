"""About view: problem, pain point, features, short lines about AI."""
import streamlit as st

PROBLEMS = [
    ("AI impersonation is increasing", "Deepfakes imitate real faces and voices convincingly."),
    ("People struggle to identify fakes", "Clues are hard to spot in live video calls."),
    ("High-risk interactions are vulnerable", "Job interviews, online meetings, banking, remote ID checks."),
    ("Human verification is insufficient", "People trust familiar faces and voices."),
    ("Fraud causes serious losses", "Financial loss, identity misuse, reputational damage, broken trust."),
]
FEATURES = [
    ("Video Analysis", "Checks video frames for deepfake manipulation."),
    ("Voice Analysis", "Detects AI-generated or cloned voices."),
    ("Audio-Video Matching", "Checks if lip movements match the speech."),
    ("AI Risk Assessment", "One risk score with clear reasons."),
    ("Instant Alerts", "Warns you so you can take extra care."),
]
GOOD = ["AI can create wonders. Truth must stay human.",
        "Use AI to build trust, not to break it."]
BAD = ["Seeing is no longer believing.",
       "A familiar face can now be a stranger's mask.",
       "One fake call can cost a lifetime of savings."]


def _cards(items, color):
    for i in range(0, len(items), 3):
        cols = st.columns(3)
        for col, (t, d) in zip(cols, items[i:i + 3]):
            col.markdown(
                f"<div class='panel' style='border-top:5px solid {color};min-height:150px'>"
                f"<h4 style='color:#0F172A;margin:0 0 .4rem'>{t}</h4>"
                f"<p style='color:#1E293B;margin:0'>{d}</p></div>", unsafe_allow_html=True)


def show_about():
    st.markdown("<p style='text-align:center;font-size:1.25rem;font-weight:700;color:#0F172A'>"
                "Help people identify potential deepfake threats earlier and make safer, "
                "more informed decisions.</p>", unsafe_allow_html=True)
    st.subheader("The problem")
    _cards(PROBLEMS, "#B91C1C")
    st.markdown("<div class='result3d' style='background-color:#1E3A8A;padding:1.2rem;border-radius:12px;"
                "text-align:center;margin:1rem 0'><div style='color:#FFFFFF;font-size:.95rem;"
                "font-weight:700'>CORE PAIN POINT</div><div style='color:#FFFFFF;font-size:1.2rem;"
                "font-weight:700'>People lack an accessible, real-time way to assess whether a face "
                "or voice may be AI-generated or manipulated.</div></div>", unsafe_allow_html=True)
    st.subheader("What we do")
    _cards(FEATURES, "#1D4ED8")
    st.write("")
    for q in GOOD:
        st.markdown(f"<p style='text-align:center;color:#15803D;font-size:1.15rem;font-weight:700;"
                    f"font-style:italic;margin:.3rem'>“{q}”</p>", unsafe_allow_html=True)
    for q in BAD:
        st.markdown(f"<p style='text-align:center;color:#B91C1C;font-size:1.15rem;font-weight:700;"
                    f"margin:.3rem'>⚠ {q}</p>", unsafe_allow_html=True)
