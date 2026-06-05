install:
	pip install -e .

run-api:
	uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000

run-dashboard:
	streamlit run apps/dashboard/streamlit_app.py

run:
	docker compose -f infra/compose.yaml up --build

test:
	pytest

