FROM python:3.11-slim

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -e .

CMD ["streamlit", "run", "apps/dashboard/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]

