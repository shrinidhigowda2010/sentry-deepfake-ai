"""Premium cybersecurity SaaS theme for Streamlit."""

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Syne:wght@600;700;800&display=swap');

:root {
  --bg: #0B1020;
  --panel: #14226B;
  --panel-2: #101B45;
  --accent: #3B82F6;
  --accent-bright: #60A5FA;
  --amber: #F59E0B;
  --red: #EF4444;
  --green: #22C55E;
  --text: #E8EEF9;
  --muted: #94A3B8;
  --border: rgba(96, 165, 250, 0.22);
  --glow: rgba(59, 130, 246, 0.28);
}

html, body, [data-testid="stAppViewContainer"] {
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(59,130,246,0.18), transparent 55%),
    radial-gradient(900px 500px at 90% 0%, rgba(20,34,107,0.85), transparent 50%),
    linear-gradient(180deg, #0B1020 0%, #0A1228 45%, #0B1020 100%) !important;
  color: var(--text);
  font-family: 'IBM Plex Sans', sans-serif;
}

[data-testid="stHeader"] { background: rgba(11,16,32,0.65); backdrop-filter: blur(8px); }
[data-testid="stToolbar"] { visibility: hidden; height: 0; }

h1, h2, h3, .brand-title {
  font-family: 'Syne', 'IBM Plex Sans', sans-serif !important;
  letter-spacing: -0.02em;
}

.block-container { padding-top: 1.4rem; max-width: 1180px; }

.brand-wrap {
  display: flex; align-items: center; gap: 1rem;
  padding: 0.4rem 0 1.2rem 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 1.25rem;
}
.brand-mark {
  width: 52px; height: 52px; border-radius: 12px;
  background: linear-gradient(145deg, #1E3A8A, #2563EB 55%, #38BDF8);
  box-shadow: 0 0 0 1px rgba(96,165,250,0.35), 0 0 28px var(--glow);
  display: grid; place-items: center;
  font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.15rem; color: white;
}
.brand-title { font-size: 1.85rem; font-weight: 800; margin: 0; color: #F8FAFC; }
.brand-sub { margin: 0.15rem 0 0; color: var(--muted); font-size: 0.95rem; }

.panel {
  background: linear-gradient(180deg, rgba(20,34,107,0.92), rgba(16,27,69,0.92));
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1rem 1.1rem;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 10px 30px rgba(0,0,0,0.25);
  margin-bottom: 0.85rem;
}
.panel h3 { margin: 0 0 0.55rem 0; font-size: 1.02rem; color: #F1F5F9; }
.muted { color: var(--muted); font-size: 0.9rem; }
.mono { font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; }

.metric-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem;
}
@media (max-width: 900px) {
  .metric-grid { grid-template-columns: repeat(2, 1fr); }
}
.metric {
  background: rgba(11,16,32,0.45);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.85rem 0.9rem;
}
.metric .label { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }
.metric .value { font-size: 1.35rem; font-weight: 700; margin-top: 0.25rem; color: #F8FAFC; }
.metric .hint { color: var(--muted); font-size: 0.78rem; margin-top: 0.2rem; }

.badge {
  display: inline-block; padding: 0.28rem 0.7rem; border-radius: 999px;
  font-size: 0.78rem; font-weight: 700; letter-spacing: 0.04em;
  border: 1px solid transparent;
}
.badge-green { background: rgba(34,197,94,0.12); color: #4ADE80; border-color: rgba(34,197,94,0.35); }
.badge-amber { background: rgba(245,158,11,0.12); color: #FBBF24; border-color: rgba(245,158,11,0.4); }
.badge-red { background: rgba(239,68,68,0.12); color: #F87171; border-color: rgba(239,68,68,0.4); }
.badge-blue { background: rgba(59,130,246,0.12); color: #93C5FD; border-color: rgba(59,130,246,0.35); }

.risk-hero {
  border-radius: 14px; padding: 1.1rem 1.2rem; border: 1px solid var(--border);
  background: linear-gradient(120deg, rgba(20,34,107,0.95), rgba(11,16,32,0.9));
}
.risk-hero.lower { box-shadow: 0 0 0 1px rgba(34,197,94,0.25), 0 0 36px rgba(34,197,94,0.12); }
.risk-hero.suspicious { box-shadow: 0 0 0 1px rgba(239,68,68,0.3), 0 0 36px rgba(239,68,68,0.14); }
.risk-hero.inconclusive { box-shadow: 0 0 0 1px rgba(245,158,11,0.3), 0 0 36px rgba(245,158,11,0.12); }

.status-pill {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.2rem 0.55rem; border-radius: 999px;
  background: rgba(11,16,32,0.55); border: 1px solid var(--border);
  font-size: 0.8rem; color: var(--muted);
}
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 8px var(--glow); }
.dot.ok { background: var(--green); box-shadow: 0 0 8px rgba(34,197,94,0.5); }
.dot.warn { background: var(--amber); box-shadow: 0 0 8px rgba(245,158,11,0.5); }
.dot.bad { background: var(--red); box-shadow: 0 0 8px rgba(239,68,68,0.5); }

.sim-banner {
  background: rgba(245,158,11,0.12);
  border: 1px solid rgba(245,158,11,0.45);
  color: #FDE68A;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
  margin: 0.5rem 0 1rem;
}

div[data-testid="stFileUploader"] section {
  background: rgba(16,27,69,0.65);
  border: 1px dashed rgba(96,165,250,0.35);
  border-radius: 12px;
}

.stButton > button {
  background: linear-gradient(180deg, #2563EB, #1D4ED8);
  color: white; border: 1px solid rgba(147,197,253,0.35);
  border-radius: 10px; font-weight: 600;
  box-shadow: 0 0 18px rgba(37,99,235,0.25);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 0 26px rgba(37,99,235,0.4);
  border-color: rgba(147,197,253,0.55);
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0E1630, #0B1020);
  border-right: 1px solid var(--border);
}
"""


def inject_styles() -> str:
    return f"<style>{CUSTOM_CSS}</style>"
