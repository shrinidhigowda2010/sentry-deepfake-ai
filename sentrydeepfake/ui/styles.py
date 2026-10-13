"""Clean, high-contrast light theme for Streamlit."""

CUSTOM_CSS = """
:root {
  --bg: #F5F7FB;
  --panel: #FFFFFF;
  --accent: #1D4ED8;
  --amber: #B45309;
  --red: #B91C1C;
  --green: #15803D;
  --text: #0F172A;
  --muted: #475569;
  --border: #CBD5E1;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: Arial, Helvetica, sans-serif;
}
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] span,
[data-testid="stAppViewContainer"] label, [data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] div, [data-testid="stMarkdownContainer"] {
  color: var(--text);
}
h1, h2, h3, h4, .brand-title { color: var(--text) !important; }

[data-testid="stHeader"] { background: var(--bg); }
[data-testid="stToolbar"] { visibility: hidden; height: 0; }
.block-container { padding-top: 1.4rem; max-width: 1180px; }

.brand-wrap { display: flex; align-items: center; gap: 1rem; padding: 0.4rem 0 1.2rem;
  border-bottom: 2px solid var(--border); margin-bottom: 1.25rem; }
.brand-mark { width: 52px; height: 52px; border-radius: 12px; background: var(--accent);
  display: grid; place-items: center; font-weight: 800; font-size: 1.15rem; color: #FFFFFF !important; }
.brand-title { font-size: 1.85rem; font-weight: 800; margin: 0; }
.brand-sub { margin: 0.15rem 0 0; color: var(--muted) !important; font-size: 1rem; }

.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
  padding: 1rem 1.1rem; margin-bottom: 0.85rem; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
.panel h3 { margin: 0 0 0.55rem 0; font-size: 1.05rem; }
.muted { color: var(--muted) !important; font-size: 0.95rem; }
.mono { font-family: monospace; font-size: 0.9rem; }

.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; }
@media (max-width: 900px) { .metric-grid { grid-template-columns: repeat(2, 1fr); } }
.metric { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 0.85rem 0.9rem; }
.metric .label { color: var(--muted) !important; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; }
.metric .value { font-size: 1.4rem; font-weight: 700; margin-top: 0.25rem; color: var(--text) !important; }
.metric .hint { color: var(--muted) !important; font-size: 0.8rem; margin-top: 0.2rem; }

.badge { display: inline-block; padding: 0.3rem 0.75rem; border-radius: 999px; font-size: 0.8rem; font-weight: 700; color: #FFFFFF !important; }
.badge-green { background: var(--green); }
.badge-amber { background: var(--amber); }
.badge-red { background: var(--red); }
.badge-blue { background: var(--accent); }

.risk-hero { border-radius: 12px; padding: 1.1rem 1.2rem; background: var(--panel); border: 2px solid var(--border); }
.risk-hero.lower { border-color: var(--green); }
.risk-hero.suspicious { border-color: var(--red); }
.risk-hero.inconclusive { border-color: var(--amber); }

.status-pill { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.2rem 0.6rem;
  border-radius: 999px; background: var(--panel); border: 1px solid var(--border); font-size: 0.85rem; color: var(--text) !important; }
.dot { width: 9px; height: 9px; border-radius: 50%; background: var(--accent); }
.dot.ok { background: var(--green); }
.dot.warn { background: var(--amber); }
.dot.bad { background: var(--red); }

.sim-banner { background: #FEF3C7; border: 1px solid #F59E0B; color: #78350F !important;
  padding: 0.75rem 1rem; border-radius: 10px; font-weight: 700; margin: 0.5rem 0 1rem; }

div[data-testid="stFileUploader"] section { background: var(--panel); border: 2px dashed var(--accent); border-radius: 12px; }
div[data-testid="stFileUploader"] * { color: var(--text) !important; }

.stButton > button, .stDownloadButton > button { background: var(--accent) !important; color: #FFFFFF !important;
  border: none; border-radius: 10px; font-weight: 600; }
.stButton > button *, .stDownloadButton > button * { color: #FFFFFF !important; }
.stButton > button:hover, .stDownloadButton > button:hover { background: #1E40AF !important; }

[data-testid="stSidebar"] { background: #E2E8F0 !important; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] * { color: var(--text) !important; }
section[data-testid="stSidebar"] div[role="radiogroup"] label,
section[data-testid="stSidebar"] div[role="radiogroup"] label *,
section[data-testid="stSidebar"] div[role="radiogroup"] label p,
section[data-testid="stSidebar"] div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
  font-size: 2.1rem !important; font-weight: 900 !important; line-height: 1.35 !important;
  letter-spacing: .05em !important; text-transform: uppercase !important;
  color: #FFFFFF !important; text-shadow: 0 3px 8px rgba(0,0,0,.55) !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) * { color: #0F172A !important; text-shadow: none !important; }
section[data-testid="stSidebar"] { min-width: 260px !important; max-width: 260px !important; }
"""


def inject_styles() -> str:
    return f"<style>{CUSTOM_CSS}</style>"
