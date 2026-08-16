.PHONY: install test lint format clean dev-backend dev-frontend

install:
	python -m pip install --upgrade pip
	pip install -e .[dev,ai]

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache

dev-backend:
	uvicorn forgesight.api.main:app --reload --port 8000

dev-frontend:
	cd frontend/forgesight-web && npm run dev
