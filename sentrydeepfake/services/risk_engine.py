"""Explainable multimodal risk combination engine.

Categories:
  LOWER RISK   — available checks did not surface strong suspicious signals
  SUSPICIOUS   — one or more available detectors reported concerning evidence
  INCONCLUSIVE — evidence insufficient, conflicting, or unavailable

Missing detectors are NEVER treated as successful authenticity checks.
Model scores are NOT calibrated fraud probabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sentrydeepfake.config import (
    RISK_FAKE_MAX_SUSPICIOUS,
    RISK_FAKE_MEAN_SUSPICIOUS,
    RISK_UNCERTAIN_BAND,
)
from sentrydeepfake.services.audio_detector import AudioDetectionResult
from sentrydeepfake.services.sync_analyzer import SyncAnalysisResult
from sentrydeepfake.services.video_detector import VideoDetectionResult


@dataclass
class RiskAssessment:
    category: str  # LOWER RISK | SUSPICIOUS | INCONCLUSIVE
    summary: str
    evidence: List[str] = field(default_factory=list)
    modules_run: Dict[str, str] = field(default_factory=dict)
    contributing_signals: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)
    config_used: Dict[str, float] = field(default_factory=dict)
    recommended_verification: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "summary": self.summary,
            "evidence": self.evidence,
            "modules_run": self.modules_run,
            "contributing_signals": self.contributing_signals,
            "caveats": self.caveats,
            "config_used": self.config_used,
            "recommended_verification": self.recommended_verification,
        }


def assess_risk(
    video: Optional[VideoDetectionResult] = None,
    audio: Optional[AudioDetectionResult] = None,
    sync: Optional[SyncAnalysisResult] = None,
) -> RiskAssessment:
    modules: Dict[str, str] = {}
    evidence: List[str] = []
    signals: List[str] = []
    caveats = [
        "Risk category is an operational triage label, not legal proof of fraud or identity.",
        "Detector confidence scores are model outputs — not calibrated probabilities of fraud.",
        "Modules that did not run successfully do not contribute authenticity evidence.",
    ]
    config = {
        "fake_mean_suspicious": RISK_FAKE_MEAN_SUSPICIOUS,
        "fake_max_suspicious": RISK_FAKE_MAX_SUSPICIOUS,
        "uncertain_band": RISK_UNCERTAIN_BAND,
    }

    suspicious_votes = 0
    lower_votes = 0
    inconclusive_votes = 0

    # --- Video module ---
    if video is None:
        modules["video"] = "not_provided"
        inconclusive_votes += 1
        evidence.append("Video detector output was not provided.")
    elif video.status != "success":
        modules["video"] = video.status
        inconclusive_votes += 1
        evidence.append(
            f"Video detector did not succeed (status={video.status}"
            + (f", error={video.error}" if video.error else "")
            + ")."
        )
        caveats.append("Missing video results make overall authenticity assessment weaker.")
    else:
        modules["video"] = "success"
        mean_f = video.mean_fake_score
        max_f = video.max_fake_score
        evidence.append(
            f"Video model '{video.model_id}' analyzed {video.frames_analyzed} frames; "
            f"aggregate={video.aggregate_label}; "
            f"mean_fake={_fmt(mean_f)}; max_fake={_fmt(max_f)}."
        )
        if mean_f is None:
            inconclusive_votes += 1
            signals.append("video:unknown_label_mapping")
            evidence.append("Could not map model labels to a fake/real score.")
        else:
            mid = 0.5
            if mean_f >= RISK_FAKE_MEAN_SUSPICIOUS or (
                max_f is not None and max_f >= RISK_FAKE_MAX_SUSPICIOUS
            ):
                suspicious_votes += 1
                signals.append("video:elevated_fake_score")
                evidence.append(
                    "Video detector reported elevated synthetic-media scores on sampled frames."
                )
            elif abs(mean_f - mid) < RISK_UNCERTAIN_BAND:
                inconclusive_votes += 1
                signals.append("video:uncertain_band")
                evidence.append("Video scores fell in an uncertain mid-range band.")
            elif mean_f <= (1.0 - RISK_FAKE_MEAN_SUSPICIOUS):
                lower_votes += 1
                signals.append("video:lower_synthetic_signal")
                evidence.append("Video detector did not surface strong synthetic signals.")
            else:
                inconclusive_votes += 1
                signals.append("video:borderline")
                evidence.append("Video scores were borderline relative to configured thresholds.")

    # --- Audio module ---
    if audio is None:
        modules["audio"] = "not_provided"
        evidence.append("Audio detector was not invoked.")
        caveats.append("No audio authenticity check contributed to this assessment.")
    elif audio.status in {"unavailable", "skipped"}:
        modules["audio"] = audio.status
        evidence.append(f"Audio detector status={audio.status} — not treated as a pass.")
        caveats.append("Unavailable audio checks are ignored, not counted as authentic.")
    elif audio.status != "success":
        modules["audio"] = audio.status
        inconclusive_votes += 1
        evidence.append(f"Audio detector failed (status={audio.status}).")
    else:
        modules["audio"] = "success"
        evidence.append(
            f"Audio model '{audio.model_id}' label={audio.aggregate_label}; "
            f"spoof={_fmt(audio.spoof_score)}."
        )
        if audio.spoof_score is not None and audio.spoof_score >= RISK_FAKE_MEAN_SUSPICIOUS:
            suspicious_votes += 1
            signals.append("audio:elevated_spoof_score")
        elif audio.spoof_score is not None and audio.spoof_score <= (
            1.0 - RISK_FAKE_MEAN_SUSPICIOUS
        ):
            lower_votes += 1
            signals.append("audio:lower_spoof_signal")
        else:
            inconclusive_votes += 1
            signals.append("audio:uncertain")

    # --- Sync module (informational; weak vote only) ---
    if sync is None:
        modules["sync"] = "not_provided"
        evidence.append("A/V synchronization analysis was not invoked.")
    elif sync.status != "success":
        modules["sync"] = sync.status
        evidence.append(
            f"A/V sync status={sync.status} — mismatch/absence not counted as authenticity."
        )
        caveats.append("Sync failure or unavailability does not imply media is authentic or fake.")
    else:
        modules["sync"] = "success"
        evidence.append(
            f"Sync method='{sync.method}'; correlation={_fmt(sync.correlation)}; "
            f"lag_s={_fmt(sync.lag_estimate_sec)}. {sync.interpretation}"
        )
        # Sync never alone flips to SUSPICIOUS; low corr only adds inconclusive pressure
        if sync.correlation is not None and sync.correlation < 0.15:
            inconclusive_votes += 1
            signals.append("sync:low_correlation")
            evidence.append(
                "Low A/V correlation noted as uncertainty — not automatic fake classification."
            )
        else:
            signals.append("sync:informational")

    # --- Combine ---
    successful_detectors = [
        k for k, v in modules.items() if v == "success" and k in {"video", "audio"}
    ]

    if not successful_detectors:
        category = "INCONCLUSIVE"
        summary = (
            "Evidence is insufficient because no primary media authenticity detector "
            "completed successfully."
        )
    elif suspicious_votes > 0 and lower_votes > 0 and suspicious_votes == lower_votes:
        category = "INCONCLUSIVE"
        summary = (
            "Available detectors reported conflicting signals. Treat as inconclusive and "
            "use out-of-band verification for sensitive actions."
        )
    elif suspicious_votes > 0:
        category = "SUSPICIOUS"
        summary = (
            "One or more available detectors reported concerning evidence. "
            "Additional verification is recommended before trusting the interaction."
        )
    elif inconclusive_votes > 0 and lower_votes == 0:
        category = "INCONCLUSIVE"
        summary = (
            "Completed checks were uncertain or incomplete. Do not interpret this as clearance."
        )
    elif lower_votes > 0 and inconclusive_votes > lower_votes:
        category = "INCONCLUSIVE"
        summary = (
            "Some lower-risk signals were present, but uncertainty from other checks "
            "dominates the combined assessment."
        )
    else:
        category = "LOWER RISK"
        summary = (
            "No strong suspicious signals were detected by the available checks. "
            "This is not proof of identity and does not replace verification for high-risk actions."
        )

    recommend = category in {"SUSPICIOUS", "INCONCLUSIVE"}
    return RiskAssessment(
        category=category,
        summary=summary,
        evidence=evidence,
        modules_run=modules,
        contributing_signals=signals,
        caveats=caveats,
        config_used=config,
        recommended_verification=recommend,
    )


def _fmt(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"
