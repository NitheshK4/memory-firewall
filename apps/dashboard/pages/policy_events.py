import sys
import os
import requests
import streamlit as st
import pandas as pd

# Set up paths so that imports work reliably on Streamlit Community Cloud
pages_dir = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.dirname(pages_dir)
repo_root = os.path.dirname(dashboard_dir)
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from api_helper import API_BASE_URL as API_BASE, get_headers  # type: ignore[import]
from ui_theme import apply_theme, render_hero, render_sidebar_status  # type: ignore[import]

st.set_page_config(
    page_title="Policy Audit Log — Memory Firewall",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Swiss Editorial & Forensic Dossier theme
apply_theme()

render_hero(
    title="Policy Audit Log",
    subtitle="Forensic Ledger of All Memory Ingestion Events, Automated Risk Calculations & Policy Actions"
)

try:
    resp = requests.get(f"{API_BASE}/api/v1/memories", headers=get_headers(), timeout=60)
    resp.raise_for_status()
    memories_data = resp.json()
    memories = memories_data.get("items", [])
except Exception as e:
    st.error(f"Could not reach API: {e}")
    memories = []

events = []
for mem in memories:
    events.append({
        "Case ID": mem.get("memory_id", "?"),
        "Status": mem.get("status", "unknown"),
        "Trust Score": round(float(mem.get("trust_score", 0.0)), 2),
        "Policy Flags": ", ".join(mem.get("flags", [])) or "—",
        "Actor": mem.get("provenance", {}).get("actor", "?"),
        "Source": mem.get("provenance", {}).get("source_type", "?"),
        "Timestamp": mem.get("created_at", "?"),
    })

if not events:
    st.markdown(
        """
        <div class="dossier-card" style="text-align: center; padding: 36px 20px; background: #faf9f5;">
            <span class="dossier-stamp dossier-stamp-trusted" style="font-size: 0.85rem; padding: 6px 16px;">
                📋 AUDIT LEDGER EMPTY
            </span>
            <p style="color: #71717a; font-size: 0.9rem; margin-top: 10px;">
                Ingest context from the main console to generate policy audit trails.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        st.markdown(
            f"""
            <div style="margin-bottom: 12px;">
                <span class="dossier-stamp dossier-stamp-trusted" style="font-size: 0.85rem; padding: 6px 14px;">
                    📋 ENTRIES: {len(events)} AUDIT RECORDS
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_f2:
        status_filter = st.multiselect(
            "Filter By Verdict",
            options=["allowed", "low_trust", "quarantined", "blocked"],
            default=["allowed", "low_trust", "quarantined", "blocked"],
        )

    df = pd.DataFrame(events)
    if status_filter:
        df = df[df["Status"].isin(status_filter)]

    st.markdown('<div class="dossier-card">', unsafe_allow_html=True)
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "Trust Score": st.column_config.ProgressColumn(
                "Trust Score",
                help="Normalized zero-trust reliability score",
                format="%.2f",
                min_value=0,
                max_value=1,
            ),
        }
    )
    st.markdown('</div>', unsafe_allow_html=True)

render_sidebar_status(api_url=API_BASE, is_connected=True)
