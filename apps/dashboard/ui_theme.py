import streamlit as st

SWISS_EDITORIAL_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
/* =========================================================
   MODERN SWISS EDITORIAL & FORENSIC DOSSIER DESIGN SYSTEM
   ========================================================= */

:root {
    --bg-canvas: #f7f5ef;
    --bg-paper: #ffffff;
    --bg-card: #fdfcf9;
    --bg-subtle: #f0eee6;
    --bg-inset: #edeae0;
    
    /* Swiss Editorial Palette */
    --c-cobalt: #1d4ed8;
    --c-cobalt-light: #eff6ff;
    --c-terracotta: #c2410c;
    --c-terracotta-light: #fff7ed;
    --c-crimson: #dc2626;
    --c-crimson-light: #fef2f2;
    --c-emerald: #15803d;
    --c-emerald-light: #f0fdf4;
    --c-ochre: #b45309;
    --c-ochre-light: #fffbeb;
    
    /* Monochromes */
    --text-main: #18181b;
    --text-body: #3f3f46;
    --text-muted: #71717a;
    --text-faint: #a1a1aa;
    
    --border-card: #e5e2d9;
    --border-strong: #18181b;
    --border-dashed: #d4d0c3;
    
    /* Tactile Paper Shadows */
    --shadow-paper: 3px 3px 0px rgba(24, 24, 27, 0.08), 0 1px 3px rgba(0, 0, 0, 0.03);
    --shadow-card: 4px 4px 0px rgba(24, 24, 27, 0.1);
    --shadow-btn: 3px 3px 0px #18181b;
    --shadow-btn-hover: 1px 1px 0px #18181b;
}

/* Global Reset & Typography */
html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: var(--bg-canvas) !important;
    color: var(--text-main) !important;
    letter-spacing: -0.01em;
}

/* Subtle Editorial Grid Canvas */
.stApp {
    background-image: 
        radial-gradient(var(--border-dashed) 1px, transparent 1px);
    background-size: 24px 24px;
}

/* Header & Navigation Bar */
header[data-testid="stHeader"] {
    background-color: rgba(247, 245, 239, 0.9) !important;
    backdrop-filter: blur(8px) !important;
    border-bottom: 2px solid var(--border-card) !important;
}

/* Sidebar - Editorial Archive Index */
section[data-testid="stSidebar"] {
    background-color: #f2efe5 !important;
    border-right: 2px solid var(--border-card) !important;
    box-shadow: 2px 0 12px rgba(0, 0, 0, 0.02) !important;
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    color: var(--text-main) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}

/* Editorial Hero Banner */
.dossier-hero {
    background: var(--bg-paper);
    border: 2px solid var(--border-strong);
    border-radius: 4px;
    padding: 24px 28px;
    box-shadow: var(--shadow-card);
    margin-bottom: 24px;
    position: relative;
}

.dossier-hero-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 1px dashed var(--border-dashed);
    padding-bottom: 12px;
    margin-bottom: 16px;
}

.dossier-hero-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.dossier-hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.1rem;
    font-weight: 700;
    color: var(--text-main);
    letter-spacing: -0.03em;
    line-height: 1.15;
    margin: 0 0 6px 0;
}

.dossier-hero-subtitle {
    font-size: 0.95rem;
    color: var(--text-body);
    margin: 0;
    line-height: 1.5;
}

/* Swiss Editorial Metric Grid */
.dossier-metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 26px;
}

@media (max-width: 900px) {
    .dossier-metrics-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

.dossier-metric-tile {
    background: var(--bg-paper);
    border: 2px solid var(--border-strong);
    border-radius: 4px;
    padding: 16px 18px;
    box-shadow: var(--shadow-paper);
    position: relative;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.dossier-metric-tile:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-card);
}

.dossier-metric-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 2px 6px;
    border-radius: 2px;
    display: inline-block;
    margin-bottom: 8px;
}

.dossier-metric-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1;
    color: var(--text-main);
    letter-spacing: -0.03em;
}

.dossier-metric-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-muted);
    margin-top: 6px;
}

/* Forensic Ink Stamps */
.dossier-stamp {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 3px 8px;
    border-radius: 2px;
    border: 1.5px solid;
    position: relative;
}

.dossier-stamp-approved {
    color: var(--c-emerald);
    border-color: var(--c-emerald);
    background-color: var(--c-emerald-light);
}

.dossier-stamp-quarantine {
    color: var(--c-terracotta);
    border-color: var(--c-terracotta);
    background-color: var(--c-terracotta-light);
}

.dossier-stamp-blocked {
    color: var(--c-crimson);
    border-color: var(--c-crimson);
    background-color: var(--c-crimson-light);
}

.dossier-stamp-trusted {
    color: var(--c-cobalt);
    border-color: var(--c-cobalt);
    background-color: var(--c-cobalt-light);
}

.dossier-stamp-lowtrust {
    color: var(--c-ochre);
    border-color: var(--c-ochre);
    background-color: var(--c-ochre-light);
}

/* Case File Card */
.dossier-card {
    background: var(--bg-paper);
    border: 1.5px solid var(--border-card);
    border-radius: 4px;
    padding: 18px 20px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-paper);
    position: relative;
    transition: all 0.15s ease;
}

.dossier-card:hover {
    border-color: var(--border-strong);
    box-shadow: var(--shadow-card);
}

/* Section Title - Swiss Grotesque */
.dossier-section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-main);
    margin: 28px 0 14px 0;
    display: flex;
    align-items: center;
    gap: 10px;
    text-transform: uppercase;
    letter-spacing: 0.02em;
}

.dossier-section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border-dashed);
    margin-left: 12px;
}

/* Evidence Paper Box */
.dossier-evidence {
    background: var(--bg-inset);
    border: 1px solid var(--border-dashed);
    border-left: 3px solid var(--border-strong);
    border-radius: 2px;
    padding: 12px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: var(--text-main);
    line-height: 1.5;
    margin: 8px 0;
}

/* Confidence Meter - Swiss Stepped Bar */
.dossier-meter-container {
    background: var(--bg-subtle);
    border: 1px solid var(--border-dashed);
    border-radius: 2px;
    height: 8px;
    width: 100%;
    overflow: hidden;
    margin: 6px 0;
}

.dossier-meter-fill {
    height: 100%;
    transition: width 0.3s ease;
}

/* Streamlit Buttons Override - Tactile Swiss Editorial */
div.stButton > button {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    border-radius: 3px !important;
    padding: 10px 20px !important;
    border: 2px solid var(--border-strong) !important;
    background: var(--bg-paper) !important;
    color: var(--text-main) !important;
    box-shadow: var(--shadow-btn) !important;
    transition: all 0.1s ease !important;
    cursor: pointer !important;
}

div.stButton > button:hover {
    transform: translate(2px, 2px) !important;
    box-shadow: var(--shadow-btn-hover) !important;
    background: var(--bg-subtle) !important;
    color: var(--text-main) !important;
}

div.stButton > button:active {
    transform: translate(3px, 3px) !important;
    box-shadow: none !important;
}

/* Primary Action Button (Cobalt) */
div.stButton > button[kind="primary"],
div.stButton > button[data-testid*="primary"] {
    background: var(--c-cobalt) !important;
    color: #ffffff !important;
    border-color: var(--border-strong) !important;
}

div.stButton > button[kind="primary"]:hover,
div.stButton > button[data-testid*="primary"]:hover {
    background: #1e40af !important;
    color: #ffffff !important;
}

/* Streamlit Inputs Override */
div[data-baseweb="input"] {
    background-color: var(--bg-paper) !important;
    border-radius: 3px !important;
    border: 2px solid var(--border-strong) !important;
    box-shadow: 2px 2px 0px rgba(24, 24, 27, 0.08) !important;
    transition: all 0.15s ease !important;
}

div[data-baseweb="input"]:focus-within {
    border-color: var(--c-cobalt) !important;
    box-shadow: 3px 3px 0px var(--c-cobalt) !important;
}

input.stTextInput, div[data-baseweb="input"] input {
    color: var(--text-main) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.95rem !important;
}

/* Streamlit Expanders - Case File Dossier Style */
div[data-testid="stExpander"] {
    background: var(--bg-paper) !important;
    border-radius: 3px !important;
    border: 1.5px solid var(--border-card) !important;
    box-shadow: var(--shadow-paper) !important;
    margin-bottom: 12px !important;
    transition: border-color 0.15s ease !important;
}

div[data-testid="stExpander"]:hover {
    border-color: var(--border-strong) !important;
}

details[data-testid="stExpander"] summary {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    color: var(--text-main) !important;
    padding: 12px 16px !important;
    border-bottom: 1px dashed transparent !important;
}

details[data-testid="stExpander"][open] summary {
    border-bottom-color: var(--border-dashed) !important;
}

/* Status Sidebar Dossier Card */
.dossier-status-card {
    background: var(--bg-paper);
    border: 2px solid var(--border-strong);
    border-radius: 3px;
    padding: 14px 16px;
    box-shadow: var(--shadow-paper);
    margin-bottom: 16px;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
    width: 7px;
    height: 7px;
}
::-webkit-scrollbar-track {
    background: var(--bg-canvas);
}
::-webkit-scrollbar-thumb {
    background: #d4d0c3;
    border-radius: 2px;
}
::-webkit-scrollbar-thumb:hover {
    background: #a1a1aa;
}
</style>
"""


def apply_theme():
    """Injects Modern Swiss Editorial & Forensic Dossier styles."""
    st.markdown(SWISS_EDITORIAL_CSS, unsafe_allow_html=True)


def render_hero(title: str = "Memory Firewall Dossier", subtitle: str = "Zero-Trust Agent Memory Inspection, Policy Interception & Forensic Audit"):
    """Renders the Swiss Editorial Dossier hero header."""
    st.markdown(
        f"""
        <div class="dossier-hero">
            <div class="dossier-hero-header">
                <div class="dossier-hero-meta" style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1rem;">🛡️</span>
                    <span>DEFENSE DIRECTIVE // AGENT MEMORY FIREWALL</span>
                </div>
                <div class="dossier-stamp dossier-stamp-trusted">PROTOCOL: ZERO-TRUST V1</div>
            </div>
            <h1 class="dossier-hero-title">{title}</h1>
            <p class="dossier-hero-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_cards(stored: int, quarantined: int, blocked: int, low_trust: int):
    """Renders 4 Swiss Editorial metric tiles with relocated top-right icons."""
    st.markdown(
        f"""
        <div class="dossier-metrics-grid">
            <div class="dossier-metric-tile" style="border-top: 4px solid var(--c-cobalt); position: relative;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div class="dossier-metric-tag" style="background: var(--c-cobalt-light); color: var(--c-cobalt); margin-bottom: 0;">
                        ARCHIVE // ACTIVE
                    </div>
                    <span style="font-size: 1.25rem; background: var(--c-cobalt-light); width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 4px; border: 1px solid rgba(29, 78, 216, 0.2);">
                        🗄️
                    </span>
                </div>
                <div class="dossier-metric-value">{stored}</div>
                <div class="dossier-metric-label">Stored Memories</div>
            </div>
            <div class="dossier-metric-tile" style="border-top: 4px solid var(--c-terracotta); position: relative;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div class="dossier-metric-tag" style="background: var(--c-terracotta-light); color: var(--c-terracotta); margin-bottom: 0;">
                        REVIEW // PENDING
                    </div>
                    <span style="font-size: 1.25rem; background: var(--c-terracotta-light); width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 4px; border: 1px solid rgba(194, 65, 12, 0.2);">
                        ⚖️
                    </span>
                </div>
                <div class="dossier-metric-value" style="color: var(--c-terracotta);">{quarantined}</div>
                <div class="dossier-metric-label">In Quarantine</div>
            </div>
            <div class="dossier-metric-tile" style="border-top: 4px solid var(--c-crimson); position: relative;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div class="dossier-metric-tag" style="background: var(--c-crimson-light); color: var(--c-crimson); margin-bottom: 0;">
                        POLICY // VIOLATIONS
                    </div>
                    <span style="font-size: 1.25rem; background: var(--c-crimson-light); width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 4px; border: 1px solid rgba(220, 38, 38, 0.2);">
                        🚫
                    </span>
                </div>
                <div class="dossier-metric-value" style="color: var(--c-crimson);">{blocked}</div>
                <div class="dossier-metric-label">Blocked Attempts</div>
            </div>
            <div class="dossier-metric-tile" style="border-top: 4px solid var(--c-ochre); position: relative;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div class="dossier-metric-tag" style="background: var(--c-ochre-light); color: var(--c-ochre); margin-bottom: 0;">
                        CONFIDENCE // LOW
                    </div>
                    <span style="font-size: 1.25rem; background: var(--c-ochre-light); width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 4px; border: 1px solid rgba(180, 83, 9, 0.2);">
                        🧭
                    </span>
                </div>
                <div class="dossier-metric-value" style="color: var(--c-ochre);">{low_trust}</div>
                <div class="dossier-metric-label">Low Trust Items</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_status(api_url: str, is_connected: bool = True):
    """Renders the forensic sidebar status card with telemetry badge."""
    with st.sidebar:
        st.markdown(
            f"""
            <div class="dossier-status-card">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <span style="display: flex; align-items: center; gap: 6px; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.85rem; text-transform: uppercase;">
                        <span>📡</span> ENGINE TELEMETRY
                    </span>
                    <span class="dossier-stamp dossier-stamp-approved" style="font-size: 0.65rem;">ONLINE</span>
                </div>
                <div style="font-size: 0.75rem; color: #71717a; font-family: 'JetBrains Mono', monospace; word-break: break-all; margin-bottom: 6px;">
                    HOST: <span style="color: #1d4ed8; font-weight: 600;">{api_url}</span>
                </div>
                <div style="font-size: 0.72rem; color: #a1a1aa; font-family: 'JetBrains Mono', monospace;">
                    MODE: WRITE/READ INTERCEPTION
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def get_trust_badge_html(trust_score: float) -> str:
    """Returns HTML for Swiss confidence meter & forensic stamp."""
    score_pct = int(max(0.0, min(1.0, trust_score)) * 100)
    if trust_score >= 0.7:
        stamp_class = "dossier-stamp-approved"
        stamp_text = "VERIFIED // HIGH TRUST"
        fill_color = "var(--c-emerald)"
    elif trust_score >= 0.4:
        stamp_class = "dossier-stamp-lowtrust"
        stamp_text = "CAUTION // MODERATE TRUST"
        fill_color = "var(--c-ochre)"
    else:
        stamp_class = "dossier-stamp-blocked"
        stamp_text = "ELEVATED RISK // UNTRUSTED"
        fill_color = "var(--c-crimson)"

    return f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin: 4px 0 2px 0;">
        <span class="dossier-stamp {stamp_class}">{stamp_text}</span>
        <span style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 0.82rem; color: #18181b;">
            SCORE: {trust_score:.2f} ({score_pct}%)
        </span>
    </div>
    <div class="dossier-meter-container">
        <div class="dossier-meter-fill" style="width: {score_pct}%; background-color: {fill_color};"></div>
    </div>
    """
