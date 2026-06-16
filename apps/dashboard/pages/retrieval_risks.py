import os
import requests
import streamlit as st

st.set_page_config(page_title="Retrieval Risks", page_icon="🔍", layout="wide")
st.title("🔍 Retrieval Risk Monitor")
st.caption("Inspect the risk profile of memories served during retrieval queries.")

from apps.dashboard.api_helper import API_BASE_URL as API_BASE, get_headers


st.subheader("Run a retrieval query")
query = st.text_input("Query text", placeholder="e.g. API keys and credentials")
actor = st.text_input("Actor", value="dashboard_user")
max_results = st.slider("Max results", 1, 20, 5)

if st.button("🔎 Search"):
    if not query.strip():
        st.warning("Enter a query first.")
    else:
        try:
            resp = requests.post(
                f"{API_BASE}/api/v1/retrieval/query",
                json={"query": query, "actor": actor, "max_results": max_results},
                headers=get_headers(),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            st.error(f"API error: {e}")
            data = None

        if data:
            results = data.get("results", [])
            st.metric("Results returned", len(results))

            for r in results:
                risk_color = (
                    "🔴" if r["trust_score"] < 0.3
                    else "🟡" if r["trust_score"] < 0.6
                    else "🟢"
                )
                with st.expander(f"{risk_color} {r['memory_id']} — trust {r['trust_score']:.2f} · {r['status']}"):
                    st.write("**Content:**", r.get("raw_content", "—"))
                    st.write("**Reasons:**")
                    for reason in r.get("reasons", []):
                        st.markdown(f"- {reason}")
