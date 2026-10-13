"""Reusable Streamlit rendering helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st

from sentrydeepfake.config import APP_NAME, APP_TAGLINE, EXTERNAL_PROCESSING, VIDEO_MODEL_ID
from sentrydeepfake.services.audio_detector import AudioDetectionResult, get_audio_detector
from sentrydeepfake.services.risk_engine import RiskAssessment
from sentrydeepfake.services.sync_analyzer import SyncAnalysisResult
from sentrydeepfake.services.video_detector import VideoDetectionResult, get_video_detector


def render_brand() -> None:
    st.markdown(
        f"""
        <div class="brand-wrap">
          <div class="brand-mark">SD</div>
          <div>
            <p class="brand-title">{APP_NAME}</p>
            <p class="brand-sub">{APP_TAGLINE}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_privacy_status() -> None:
    detector = get_video_detector()
    audio = get_audio_detector()
    model_ok = detector.is_available
    model_dot = "ok" if model_ok else "warn"
    model_text = "Video model ready" if model_ok else "Video model unavailable"
    audio_dot = "ok" if audio.is_available else "warn"
    ext = "No external media processing" if not EXTERNAL_PROCESSING else "External processing enabled"
    st.markdown(
        f"""
        <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
          <span class="status-pill"><span class="dot {model_dot}"></span>{model_text}</span>
          <span class="status-pill"><span class="dot {audio_dot}"></span>Audio: {'ready' if audio.is_available else 'unavailable'}</span>
          <span class="status-pill"><span class="dot ok"></span>{ext}</span>
          <span class="status-pill"><span class="dot ok"></span>Uploads cleaned after analysis</span>
          <span class="status-pill"><span class="dot"></span>Model: <span class="mono">{VIDEO_MODEL_ID}</span></span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not model_ok and detector.load_error:
        st.warning(f"Model load issue: {detector.load_error}")


def risk_badge_class(category: str) -> str:
    if category == "LOWER RISK":
        return "badge-green"
    if category == "SUSPICIOUS":
        return "badge-red"
    return "badge-amber"


def risk_hero_class(category: str) -> str:
    if category == "LOWER RISK":
        return "lower"
    if category == "SUSPICIOUS":
        return "suspicious"
    return "inconclusive"


def render_risk(risk: RiskAssessment) -> None:
    cls = risk_hero_class(risk.category)
    badge = risk_badge_class(risk.category)
    st.markdown(
        f"""
        <div class="risk-hero {cls}">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap;">
            <div>
              <div class="muted">Combined risk assessment</div>
              <div style="font-size:1.6rem;font-weight:800;margin-top:0.2rem;">{risk.category}</div>
            </div>
            <span class="badge {badge}">{risk.category}</span>
          </div>
          <p style="margin:0.75rem 0 0.35rem;color:#0F172A;">{risk.summary}</p>
          <p class="muted" style="margin:0;">Model scores ≠ calibrated fraud probabilities. Detection ≠ identity verification.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_video_metrics(video: VideoDetectionResult, total_latency_ms: Optional[float] = None) -> None:
    latency = total_latency_ms if total_latency_ms is not None else video.latency_ms
    mean_f = "n/a" if video.mean_fake_score is None else f"{video.mean_fake_score:.3f}"
    max_f = "n/a" if video.max_fake_score is None else f"{video.max_fake_score:.3f}"
    st.markdown(
        f"""
        <div class="metric-grid">
          <div class="metric"><div class="label">Video status</div><div class="value">{video.status}</div><div class="hint">{video.aggregate_label or '—'}</div></div>
          <div class="metric"><div class="label">Mean fake score</div><div class="value">{mean_f}</div><div class="hint">Across sampled frames</div></div>
          <div class="metric"><div class="label">Max fake score</div><div class="value">{max_f}</div><div class="hint">Peak frame signal</div></div>
          <div class="metric"><div class="label">Latency</div><div class="value">{latency:.0f} ms</div><div class="hint">{video.frames_analyzed} frames · model time {video.latency_ms:.0f} ms</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_module_cards(
    video: VideoDetectionResult,
    audio: AudioDetectionResult,
    sync: SyncAnalysisResult,
) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="panel"><h3>Video authenticity</h3>', unsafe_allow_html=True)
        st.write(f"**Status:** `{video.status}`")
        st.write(f"**Model:** `{video.model_id}`")
        if video.aggregate_label:
            st.write(f"**Aggregate:** `{video.aggregate_label}`")
        if video.error:
            st.caption(f"Error: {video.error}")
        if video.labels_map:
            st.caption(f"Label roles: {video.labels_map}")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel"><h3>Audio authenticity</h3>', unsafe_allow_html=True)
        st.write(f"**Status:** `{audio.status}`")
        st.write(f"**Model:** `{audio.model_id}`")
        st.caption(
            "Voice authenticity ≠ speaker identity verification. "
            "Unavailable modules are not treated as authenticity passes."
        )
        if audio.error:
            st.caption(audio.error)
        st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="panel"><h3>A/V synchronization</h3>', unsafe_allow_html=True)
        st.write(f"**Status:** `{sync.status}`")
        st.write(f"**Method:** `{sync.method}`")
        if sync.correlation is not None:
            st.write(f"**Correlation:** `{sync.correlation:.3f}`")
            st.write(f"**Lag est.:** `{sync.lag_estimate_sec:.2f}s`")
        if sync.interpretation:
            st.caption(sync.interpretation)
        if sync.error:
            st.caption(sync.error)
        st.markdown("</div>", unsafe_allow_html=True)


def render_evidence(risk: RiskAssessment) -> None:
    st.markdown("#### Suspicious signals & evidence")
    if risk.contributing_signals:
        st.write("Contributing signals: " + ", ".join(f"`{s}`" for s in risk.contributing_signals))
    for item in risk.evidence:
        st.markdown(f"- {item}")
    with st.expander("Caveats & limitations"):
        for c in risk.caveats:
            st.markdown(f"- {c}")


def render_history(history: List[Dict[str, Any]]) -> None:
    st.markdown("#### Session detection history")
    if not history:
        st.caption("No analyses in this session yet.")
        return
    st.dataframe(history[::-1], use_container_width=True, hide_index=True)


def render_frame_table(video: VideoDetectionResult) -> None:
    if not video.frame_predictions:
        return
    rows = []
    for fp in video.frame_predictions:
        rows.append(
            {
                "timestamp_sec": round(fp.timestamp_sec, 3),
                "normalized_label": fp.label,
                "fake_score": fp.fake_score,
                "real_score": fp.real_score,
                "raw_top_label": fp.raw_top_label,
                "raw_top_score": round(fp.raw_top_score, 4),
            }
        )
    st.markdown("#### Frame-level model outputs")
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_verification_panel(risk: RiskAssessment) -> None:
    st.markdown("#### Identity verification workflow")
    st.info(
        "Deepfake detection and identity verification are **separate** capabilities. "
        "This application does **not** verify legal identity."
    )
    if not risk.recommended_verification:
        st.success(
            "Available checks did not raise strong alarms. Continue standard security controls "
            "for high-value actions."
        )
        return
    st.warning("Additional verification is recommended based on the risk category.")
    st.markdown(
        """
        Recommended actions:
        1. Contact the person using a **previously verified phone number**.
        2. Confirm sensitive requests through an **independent channel** (not the same call/chat).
        3. Require an **additional authentication step** before any high-value transfer.
        4. Escalate suspicious remote interviews for **manual verification**.
        """
    )


def render_report_downloads(report: Dict[str, Any]) -> None:
    from sentrydeepfake.services.report_generator import report_to_csv, report_to_json

    json_data = report_to_json(report)
    csv_data = report_to_csv(report)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download report (JSON)",
            data=json_data,
            file_name=f"sentrydeepfake_report_{report.get('session_id', 'session')}.json",
            mime="application/json",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "Download report (CSV)",
            data=csv_data,
            file_name=f"sentrydeepfake_report_{report.get('session_id', 'session')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
