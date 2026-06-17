import sys
import os

# Set up paths so that imports work reliably on Streamlit Community Cloud
pages_dir = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.dirname(pages_dir)
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

import streamlit as st
import requests

from api_helper import API_BASE_URL as API_BASE, get_headers  # type: ignore[import]

st.set_page_config(page_title="Quarantined Memories", page_icon="🔒", layout="wide")
st.title("🔒 Quarantined Memories")
st.caption("Review memory items flagged for human approval before they enter the agent's memory store.")


try:
    resp = requests.get(f"{API_BASE}/api/v1/review/quarantine", headers=get_headers(), timeout=60)
    resp.raise_for_status()
    memories = resp.json()
except Exception as e:
    st.error(f"Could not reach API: {e}")
    memories = []

if not memories:
    st.info("No memories are currently quarantined. ✅")
else:
    st.metric("Quarantined", len(memories))
    for mem in memories:
        with st.expander(f"🆔 {mem['memory_id']} · trust={mem.get('trust_score', 0.0):.2f}"):
            st.write("**Content:**", mem.get("raw_content", "—"))
            st.write("**Flags:**", ", ".join(mem.get("flags", [])) or "none")
            st.write("**Claims:**")
            for claim in mem.get("claims", []):
                st.markdown(f"- `{claim['claim_type']}` — {claim['text']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", key=f"approve_{mem['memory_id']}"):
                    r = requests.post(
                        f"{API_BASE}/api/v1/review/{mem['memory_id']}/decision",
                        json={"action": "approve", "reviewer": "dashboard"},
                        headers=get_headers(),
                        timeout=60,
                    )
                    st.success("Approved" if r.ok else f"Error: {r.text}")
                    st.rerun()
            with col2:
                if st.button("❌ Reject", key=f"reject_{mem['memory_id']}"):
                    r = requests.post(
                        f"{API_BASE}/api/v1/review/{mem['memory_id']}/decision",
                        json={"action": "reject", "reviewer": "dashboard"},
                        headers=get_headers(),
                        timeout=60,
                    )
                    st.success("Rejected" if r.ok else f"Error: {r.text}")
                    st.rerun()

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
