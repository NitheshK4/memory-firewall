import os
import requests
import streamlit as st

st.set_page_config(page_title="Policy Events", page_icon="📋", layout="wide")
st.title("📋 Policy Events")
st.caption("Audit trail of every policy decision made by the Memory Firewall.")

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")


def get_headers() -> dict[str, str]:
    import uuid
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
    headers["X-Session-ID"] = st.session_state["session_id"]
    return headers


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
