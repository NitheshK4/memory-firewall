import sys
import os
import time
import requests
import streamlit as st

# Set up paths so that imports work reliably on Streamlit Community Cloud
pages_dir = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.dirname(pages_dir)
repo_root = os.path.dirname(dashboard_dir)
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from api_helper import API_BASE_URL as API_BASE, get_headers  # type: ignore[import]
from ui_theme import apply_theme, render_hero, render_sidebar_status, get_trust_badge_html  # type: ignore[import]

st.set_page_config(
    page_title="Quarantine Review — Memory Firewall",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Swiss Editorial & Forensic Dossier theme
apply_theme()

render_hero(
    title="Quarantined Dossiers",
    subtitle="Human-in-the-Loop Adjudication Gateway for Flagged, Contradictory, or Suspicious Memory Context"
)

try:
    resp = requests.get(f"{API_BASE}/api/v1/review/quarantine", headers=get_headers(), timeout=60)
    resp.raise_for_status()
    memories = resp.json()
except Exception as e:
    st.error(f"Could not reach API: {e}")
    memories = []

if not memories:
    st.markdown(
        """
        <div class="dossier-card" style="text-align: center; padding: 36px 20px; background: #faf9f5;">
            <span class="dossier-stamp dossier-stamp-approved" style="font-size: 0.85rem; padding: 6px 16px;">
                ⚖️ ZERO PENDING CASES // QUEUE CLEAR
            </span>
            <p style="color: #71717a; font-size: 0.9rem; margin-top: 10px;">
                All ingested memories have satisfied zero-trust policy invariants.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div style="margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center;">
            <span class="dossier-stamp dossier-stamp-quarantine" style="font-size: 0.85rem; padding: 6px 14px;">
                ⚖️ CASELOAD: {len(memories)} PENDING ADJUDICATION
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for mem in memories:
        trust = mem.get("trust_score", 0.0)
        with st.expander(f"⚖️ CASE #{mem['memory_id']}  ·  TRUST SCORE: {trust:.2f}", expanded=True):
            st.markdown(get_trust_badge_html(trust), unsafe_allow_html=True)
            
            st.markdown(
                f"""
                <div class="dossier-evidence">
                    <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: #71717a; font-weight: 700; text-transform: uppercase; margin-bottom: 2px;">
                        <span>INGESTED RAW CONTENT:</span>
                        <span>📄 CASE REF #{mem['memory_id']}</span>
                    </div>
                    {mem.get('raw_content', '—')}
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            flags = mem.get("flags", [])
            flag_chips = " ".join([f'<span class="dossier-stamp dossier-stamp-quarantine">FLAG: {f}</span>' for f in flags]) if flags else '<span style="color: #a1a1aa;">NONE</span>'
            st.markdown(f"**Policy Flags:** {flag_chips}", unsafe_allow_html=True)
            
            claims = mem.get("claims", [])
            if claims:
                st.markdown("**Extracted Claims Analysis:**")
                for claim in claims:
                    st.markdown(f"- `<span style='color: #1d4ed8; font-family: \"JetBrains Mono\", monospace;'>{claim['claim_type']}</span>` — {claim['text']}", unsafe_allow_html=True)

            st.write("")
            col1, col2, _ = st.columns([1, 1, 2])
            with col1:
                if st.button("✓ APPROVE & INGEST", key=f"approve_{mem['memory_id']}", use_container_width=True):
                    r = requests.post(
                        f"{API_BASE}/api/v1/review/{mem['memory_id']}/decision",
                        json={"action": "approve", "reviewer": "editorial_officer"},
                        headers=get_headers(),
                        timeout=60,
                    )
                    st.toast("Case Approved and Committed to Store!", icon="✓")
                    time.sleep(0.3)
                    st.rerun()
            with col2:
                if st.button("✕ REJECT & EXPUNGE", key=f"reject_{mem['memory_id']}", use_container_width=True):
                    r = requests.post(
                        f"{API_BASE}/api/v1/review/{mem['memory_id']}/decision",
                        json={"action": "reject", "reviewer": "editorial_officer"},
                        headers=get_headers(),
                        timeout=60,
                    )
                    st.toast("Case Rejected and Expunged.", icon="✕")
                    time.sleep(0.3)
                    st.rerun()

render_sidebar_status(api_url=API_BASE, is_connected=True)
