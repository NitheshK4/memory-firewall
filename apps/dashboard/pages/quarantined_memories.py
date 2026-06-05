import streamlit as st

st.set_page_config(page_title="Quarantined Memories", page_icon="🔒", layout="wide")
st.title("🔒 Quarantined Memories")
st.caption("Review memory items flagged for human approval before they enter the agent's memory store.")

import requests, os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")


def get_headers() -> dict[str, str]:
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers


try:
    resp = requests.get(f"{API_BASE}/api/v1/review/quarantine", headers=get_headers(), timeout=5)
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
        with st.expander(f"🆔 {mem['memory_id']} · trust={mem.get('trust_score', '?'):.2f}"):
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
                        timeout=5,
                    )
                    st.success("Approved" if r.ok else f"Error: {r.text}")
                    st.rerun()
            with col2:
                if st.button("❌ Reject", key=f"reject_{mem['memory_id']}"):
                    r = requests.post(
                        f"{API_BASE}/api/v1/review/{mem['memory_id']}/decision",
                        json={"action": "reject", "reviewer": "dashboard"},
                        headers=get_headers(),
                        timeout=5,
                    )
                    st.success("Rejected" if r.ok else f"Error: {r.text}")
                    st.rerun()
