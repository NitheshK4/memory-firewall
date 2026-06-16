#!/bin/bash

# Start FastAPI backend in the background
echo "Starting FastAPI Backend..."
python3 -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000 &

# Wait briefly for FastAPI to initialize
sleep 2

# Start Streamlit frontend on port 7860 (default Hugging Face port)
echo "Starting Streamlit Frontend..."
python3 -m streamlit run apps/dashboard/streamlit_app.py --server.port 7860 --server.address 0.0.0.0
