# SentryDeepfake AI

AI-powered security prototype for detecting potential deepfake videos, assessing multimodal risk signals, and recommending out-of-band verification during digital interactions.

Built for an ideathon MVP: **working video analysis**, explainable risk engine, demo mode, and report export — not a static mock dashboard.

## Features

| Area | Status |
|------|--------|
| Video upload, validation, preview | Working |
| Frame extraction (OpenCV) | Working |
| Pretrained deepfake image classifier on frames | Working when model downloads |
| Explainable multimodal risk engine | Working |
| JSON / CSV analysis reports | Working |
| Verification workflow guidance | Working |
| Demo mode (live or clearly labeled simulated) | Working |
| A/V sync heuristic (mouth motion vs audio energy) | Working when audio decodable |
| Audio spoof model | Interface ready — **not enabled** by default |
| Live / periodic frame sampling | Working when model + camera/clip available |
| Zoom / Meet / phone integration | **Not implemented** |

## Architecture

```
app.py                      # Streamlit dashboard
pages/                      # Demo Mode + Live Analysis
sentrydeepfake/
  config.py                 # Env-driven configuration
  api.py                    # Optional FastAPI risk/analysis service
  services/
    frame_extractor.py
    video_detector.py       # HF Transformers image classifier
    audio_detector.py       # Integration stub (unavailable unless configured)
    sync_analyzer.py
    risk_engine.py          # LOWER RISK / SUSPICIOUS / INCONCLUSIVE
    report_generator.py
    pipeline.py
    demo_data.py
    sample_media.py
  ui/                       # Theme + components
tests/
```

**Privacy:** Uploads go to local temp files, are analyzed on-device, and are deleted after analysis (`SENTRY_STORE_UPLOADS=0` by default). Model weights may be downloaded once from Hugging Face.

## Requirements

- Python 3.10+ (tested with 3.12)
- ~2–4 GB disk for PyTorch + model weights
- CPU is sufficient (GPU optional)
- Network required for the first model download (unless using simulated Demo Mode offline)

## Setup

```bash
cd "/home/shri/Desktop/ideathon 2.0"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env   # optional
```

First launch may download `dima806/deepfake_vs_real_image_detection` from Hugging Face.

## Launch

### Streamlit UI (primary)

```bash
source .venv/bin/activate
streamlit run app.py --server.port 8501
```

Open `http://localhost:8501`.

### Optional FastAPI risk service

```bash
source .venv/bin/activate
uvicorn sentrydeepfake.api:app --host 0.0.0.0 --port 8000
```

- Health: `GET http://localhost:8000/health`
- Risk fuse: `POST http://localhost:8000/risk/assess`
- Video analyze: `POST http://localhost:8000/analyze/video`

## Demo Mode

1. Open **Demo Mode** in the sidebar.
2. If the model loaded: run **live inference** on local procedural sample clips.
3. If the model failed: use **Simulated comparison** — results are marked  
   **`SIMULATED DEMO DATA — NOT LIVE AI DETECTION`**.

Sample clips in `sentrydeepfake/samples/` are generated locally and **do not depict real people**.

## Risk categories

- **LOWER RISK** — Available checks did not surface strong suspicious signals.
- **SUSPICIOUS** — One or more available detectors reported concerning evidence.
- **INCONCLUSIVE** — Evidence insufficient, conflicting, or unavailable.

Missing modules are **never** treated as successful authenticity checks. Model scores are **not** calibrated fraud probabilities. Detection is **not** legal identity verification.

## Tests

```bash
source .venv/bin/activate
pytest
```

## Configuration

See `.env.example` for thresholds, model id, max upload size/duration, and `SENTRY_FORCE_DEMO_MODE`.

## Verified in this environment (2026-10-12)

**Tests:** `25 passed` (`pytest`).

**Runtime checks performed:**
- Streamlit UI starts (`http://localhost:8501` → HTTP 200)
- FastAPI `/health` reports video model available
- FastAPI `/risk/assess` returns explainable `SUSPICIOUS` for elevated fake scores
- Hugging Face model `dima806/deepfake_vs_real_image_detection` loads on CPU
- Label map inspected: `{0: Real, 1: Fake}` → roles `real` / `fake`
- End-to-end pipeline on local sample clips completes with real frame scores (not invented)

**Working features**
- Video upload validation, preview, frame extraction, multi-frame inference
- Dashboard risk UI, evidence, verification guidance, session history
- JSON/CSV report download
- Demo Mode (live inference when model ready; simulated path clearly labeled)
- Multimodal risk engine (missing modules never counted as authenticity passes)
- Optional FastAPI risk/analysis API
- Temp-file cleanup after analysis

**Incomplete / limited**
- Dedicated audio spoof model: interface only (`SENTRY_AUDIO_ENABLED=0` by default)
- A/V sync needs a decodable audio track; procedural silent samples skip meaningful sync
- Live mode = periodic sampling / short clips — not continuous real-time detection
- No Zoom / Google Meet / phone-call integration
- Procedural “manipulated-role” clips are not real face-swap deepfakes; the face classifier may score them as non-synthetic. Use Demo Mode simulated comparison to show contrasting triage outcomes offline.

## Limitations

- Frame-level classifiers can err under compression, filters, low resolution, or non-face content.
- Procedural sample clips are for pipeline/UI demos — not a benchmark dataset.
- Audio deepfake detection requires configuring a compatible model (`SENTRY_AUDIO_ENABLED=1`).
- A/V sync mismatch alone does not prove a deepfake (dubbing, lag, compression).
- Live mode samples occasional frames; it is not continuous real-time monitoring.
- Model scores are not calibrated fraud probabilities; risk categories are triage labels only.

## License / use

Ideathon prototype for defensive security awareness. Do not use as sole evidence for legal, employment, or law-enforcement decisions.
