import os
import sys
import subprocess
import time
import uuid
import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")

def ensure_api_running():
    # Only auto-start if we are pointing to localhost or 127.0.0.1
    if "localhost" not in API_BASE_URL and "127.0.0.1" not in API_BASE_URL:
        return

    health_url = f"{API_BASE_URL}/health"
    try:
        # Check if already running
        r = httpx.get(health_url, timeout=0.5)
        if r.status_code == 200:
            return
    except Exception:
        pass

    # Start FastAPI backend process using same python environment
    print("FastAPI backend not running. Starting background server...", flush=True)
    try:
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "apps.api.app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Wait up to 10 seconds for it to start
        for _ in range(20):
            try:
                r = httpx.get(health_url, timeout=0.5)
                if r.status_code == 200:
                    print("FastAPI background server successfully started!", flush=True)
                    break
            except Exception:
                time.sleep(0.5)
    except Exception as e:
        print(f"Failed to launch background FastAPI process: {e}", flush=True)

def get_headers() -> dict[str, str]:
    ensure_api_running()
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
    headers["X-Session-ID"] = st.session_state["session_id"]
    return headers
