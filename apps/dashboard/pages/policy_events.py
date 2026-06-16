import sys
import os

# Set up paths so that imports work reliably on Streamlit Community Cloud
pages_dir = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.dirname(pages_dir)
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

import requests
import streamlit as st

from api_helper import API_BASE_URL as API_BASE, get_headers

st.set_page_config(page_title="Policy Events", page_icon="📋", layout="wide")
st.title("📋 Policy Events")
st.caption("Audit trail of every policy decision made by the Memory Firewall.")


try:
    resp = requests.get(f"{API_BASE}/api/v1/memories", headers=get_headers(), timeout=5)
    resp.raise_for_status()
    memories_data = resp.json()
    memories = memories_data.get("items", [])
except Exception as e:
    st.error(f"Could not reach API: {e}")
    memories = []

# Derive policy events from memory status + flags
events = []
for mem in memories:
    events.append({
        "memory_id": mem.get("memory_id", "?"),
        "status": mem.get("status", "unknown"),
        "trust_score": mem.get("trust_score", 0.0),
        "flags": ", ".join(mem.get("flags", [])) or "—",
        "actor": mem.get("provenance", {}).get("actor", "?"),
        "source_type": mem.get("provenance", {}).get("source_type", "?"),
        "created_at": mem.get("created_at", "?"),
    })

if not events:
    st.info("No policy events recorded yet.")
else:
    import pandas as pd

    st.metric("Total Events", len(events))

    status_filter = st.multiselect(
        "Filter by status",
        options=["allowed", "low_trust", "quarantined", "blocked"],
        default=["quarantined", "blocked"],
    )
    df = pd.DataFrame(events)
    if status_filter:
        df = df[df["status"].isin(status_filter)]

    st.dataframe(df, use_container_width=True)

repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
with st.sidebar:
    st.markdown("---")
    st.subheader("⚙️ System Status")
    
    log_path = os.path.join(repo_root, "fastapi_server.log")
    if os.path.exists(log_path):
        with st.expander("📝 View Backend Logs", expanded=False):
            with open(log_path, "r", encoding="utf-8") as f:
                st.code(f.read(), language="text")
            if st.button("🔄 Refresh Logs"):
                st.rerun()
