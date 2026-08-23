import sys
import os
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
    page_title="Retrieval Risk Audit — Memory Firewall",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Swiss Editorial & Forensic Dossier theme
apply_theme()

render_hero(
    title="Retrieval Risk Monitor",
    subtitle="Simulate AI Agent Context Recall & Inspect Real-Time Risk Profiling and Trust Floor Violations"
)

st.markdown('<div class="dossier-card">', unsafe_allow_html=True)
st.markdown('<div style="font-family: \'Space Grotesk\', sans-serif; font-weight: 700; font-size: 1.1rem; text-transform: uppercase; margin-bottom: 12px;">Query Parameters</div>', unsafe_allow_html=True)

q_col1, q_col2, q_col3 = st.columns([3, 2, 1])
with q_col1:
    query = st.text_input("Semantic Query Prompt", placeholder="e.g. API keys, credentials, or vendor procedures", key="risk_query")
with q_col2:
    actor = st.text_input("Requesting Agent Actor", value="forensic_analyst", key="risk_actor")
with q_col3:
    max_results = st.slider("Max Results (K)", 1, 20, 5, key="risk_max_results")

if st.button("EXECUTE GOVERNED SEARCH ↵", type="primary", use_container_width=True):
    if not query.strip():
        st.warning("⚠️ Please provide a query to execute search.")
    else:
        try:
            resp = requests.post(
                f"{API_BASE}/api/v1/retrieval/query",
                json={"query": query, "actor": actor, "max_results": max_results},
                headers=get_headers(),
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            st.session_state["risk_search_data"] = data
            st.session_state["risk_query_text"] = query
        except Exception as e:
            st.error(f"API Query Failed: {e}")
            st.session_state["risk_search_data"] = None

st.markdown('</div>', unsafe_allow_html=True)

if "risk_search_data" in st.session_state and st.session_state["risk_search_data"]:
    data = st.session_state["risk_search_data"]
    results = data.get("results", [])
    
    st.markdown(
        f"""
        <div style="margin: 20px 0 14px 0; display: flex; align-items: center; justify-content: space-between;">
            <span class="dossier-stamp dossier-stamp-trusted" style="font-size: 0.85rem; padding: 6px 14px;">
                🔍 MATCH COUNT: {len(results)} RECORDS
            </span>
            <span style="color: #71717a; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
                QUERY: <strong style="color: #18181b;">"{st.session_state.get('risk_query_text', '')}"</strong>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not results:
        st.markdown(
            """
            <div class="dossier-card" style="text-align: center; padding: 24px; color: #71717a;">
                🔍 No memories satisfied the trust floor criteria for this query.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for idx, r in enumerate(results, 1):
            trust = r.get("trust_score", 0.0)
            status = r.get("status", "unknown")
            
            with st.expander(f"MATCH #{idx} · {r['memory_id']}  ·  TRUST: {trust:.2f} [{status.upper()}]", expanded=True):
                st.markdown(get_trust_badge_html(trust), unsafe_allow_html=True)
                
                st.markdown(
                    f"""
                    <div class="dossier-evidence">
                        <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: #71717a; font-weight: 700; text-transform: uppercase; margin-bottom: 2px;">
                            <span>RETRIEVED MEMORY CONTENT:</span>
                            <span>📄 RECORD REF #{r['memory_id']}</span>
                        </div>
                        {r.get('raw_content', '—')}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
                reasons = r.get("reasons", [])
                if reasons:
                    st.markdown("**Firewall Inspection Insights:**")
                    for reason in reasons:
                        st.markdown(f"- <span style='font-family: \"JetBrains Mono\", monospace; font-size: 0.82rem; color: #3f3f46;'>{reason}</span>", unsafe_allow_html=True)

render_sidebar_status(api_url=API_BASE, is_connected=True)
