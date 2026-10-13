"""Live Check: record from the mic, analyse in ~3 s chunks, show verdict + timeline."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List

import streamlit as st

from sentrydeepfake.services.audio_detector import get_audio_detector
from sentrydeepfake.utils.audio_io import load_audio

CHUNK_SEC = 3.0


def analyze_chunks(path: Path, chunk_sec: float = CHUNK_SEC) -> List[float]:
    """AI probability per ~3 s chunk (silent/too-short chunks skipped). Raises on unreadable audio."""
    det = get_audio_detector()
    if not det.is_available:
        raise RuntimeError(det.status_message)
    import numpy as np
    y, sr = load_audio(Path(path), sr=16000, max_sec=120)
    n = int(chunk_sec * sr)
    scores = []
    for i in range(0, len(y), n):
        c = y[i:i + n]
        if len(c) < sr or float(np.sqrt(np.mean(c ** 2))) < 1e-3:
            continue
        out = det._pipe({"raw": c, "sampling_rate": sr}, top_k=None)
        sc = {d["label"].lower(): float(d["score"]) for d in out}
        fake = sc.get("fake", sc.get("spoof"))
        if fake is None:
            fake = 1 - sc.get("real", 0.5)
        scores.append(round(fake, 4))
    return scores


def show_live():
    st.markdown("<h2 style='color:#0F172A;margin:0'>🔴 Live Check</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#1E293B;font-weight:600'>Put your Zoom, Meet or phone call on speaker "
                "near the mic, then record.</p>", unsafe_allow_html=True)
    rec = st.audio_input("Record from microphone")
    if rec is None:
        return
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(rec.getvalue())
        p = Path(f.name)
    try:
        with st.spinner("Listening for AI voice..."):
            scores = analyze_chunks(p)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not check this recording: {exc}")
        return
    finally:
        p.unlink(missing_ok=True)
    if not scores:
        st.warning("No clear speech heard. Move closer to the mic and record again.")
        return
    peak, avg = max(scores), sum(scores) / len(scores)
    if peak >= 0.6:
        label, color = "AI VOICE DETECTED", "#B91C1C"
        st.error("ALERT: Part of this call sounds AI-generated. Do not share OTPs, passwords or money. "
                 "Hang up and call back on a number you trust. Ask a question only the real person knows.")
    elif avg < 0.4:
        label, color = "VOICE LOOKS REAL", "#15803D"
    else:
        label, color = "NOT SURE", "#B45309"
    st.markdown(
        f"<div class='result3d' style='background-color:{color};padding:1.4rem;border-radius:12px;text-align:center'>"
        f"<div style='color:#FFFFFF;font-size:2rem;font-weight:800'>{label}</div>"
        f"<div style='color:#FFFFFF;font-size:1.1rem'>Highest risk: {round(peak*100)}/100 · "
        f"{len(scores)} parts checked</div></div>", unsafe_allow_html=True)
    st.subheader("AI probability over time")
    import pandas as pd
    df = pd.DataFrame({"AI probability (%)": [s * 100 for s in scores]},
                      index=[f"{i*CHUNK_SEC:.0f}s" for i in range(len(scores))])
    st.bar_chart(df, color="#B91C1C" if peak >= 0.6 else "#1D4ED8")
    st.caption("Voice detection is experimental and may miss new AI voices.")
