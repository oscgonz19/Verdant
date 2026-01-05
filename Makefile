.PHONY: install dev-install test test-unit test-integration test-api test-all \
        lint format clean app api demo auth help coverage sandbox metrics check

# Default target
help:
	@echo "Verdant - Vegetation Change Intelligence Platform"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Installation:"
	@echo "  install        Install core package"
	@echo "  dev-install    Install with all development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test           Run all tests with coverage"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-api       Run API tests only"
	@echo "  test-fast      Run tests without slow markers"
	@echo "  coverage       Generate HTML coverage report"
	@echo "  sandbox        Run sandbox testing environment"
	@echo "  metrics        Run tests and show metrics"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint           Run linters (ruff, mypy)"
	@echo "  format         Format code (black, isort)"
	@echo "  check          Run all checks (lint + test)"
	@echo ""
	@echo "Applications:"
	@echo "  app            Run Streamlit dashboard"
	@echo "  api            Run FastAPI server"
	@echo "  demo           Run demo analysis"
	@echo ""
	@echo "Utilities:"
	@echo "  auth           Authenticate with Earth Engine"
	@echo "  clean          Clean build artifacts"
	@echo "  periods        Show available temporal periods"
	@echo "  indices        Show available spectral indices"

# =============================================================================
# Installation
# =============================================================================

install:
	pip install -e .

dev-install:
	pip install -e ".[all]"
	pre-commit install || true

# =============================================================================
# Testing
# =============================================================================

test:
	pytest tests/ -v --cov=engine --cov=services --cov=veg_change_engine --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v -m "not integration and not api" --cov=engine --cov-report=term-missing

test-integration:
	pytest tests/integration/ -v -m integration --cov=engine --cov-report=term-missing

test-api:
	pytest tests/api/ -v -m api --cov=app --cov-report=term-missing

test-fast:
	pytest tests/ -v -m "not slow and not integration" --cov=engine --cov-report=term-missing

test-all:
	pytest tests/ -v --cov=engine --cov=services --cov=app --cov=veg_change_engine \
		--cov-report=term-missing --cov-report=html --cov-report=xml

# Coverage
coverage:
	pytest tests/ -v --cov=engine --cov=services --cov=veg_change_engine \
		--cov-report=html --cov-report=term-missing
	@echo ""
	@echo "HTML coverage report: htmlcov/index.html"

coverage-open: coverage
	python -m webbrowser htmlcov/index.html

# Sandbox Testing Environment
sandbox:
	python scripts/sandbox.py --verbose --report

sandbox-quick:
	python scripts/sandbox.py --quick

sandbox-json:
	python scripts/sandbox.py --json sandbox_results.json

# Metrics Dashboard
metrics:
	@echo "Running tests with metrics..."
	pytest tests/ -v --tb=short --durations=10 \
		--cov=engine --cov=services --cov-report=term-missing 2>&1 | tee test_output.log
	@echo ""
	@echo "Test metrics saved to test_output.log"

# =============================================================================
# Code Quality
# =============================================================================

lint:
	@echo "Running ruff..."
	ruff check engine/ services/ app/ veg_change_engine/ cli/ || true
	@echo ""
	@echo "Running mypy..."
	mypy engine/ services/ --ignore-missing-imports || true

format:
	black engine/ services/ app/ veg_change_engine/ cli/
	isort engine/ services/ app/ veg_change_engine/ cli/

check: lint test
	@echo ""
	@echo "All checks completed!"

# =============================================================================
# Applications
# =============================================================================

app:
	streamlit run app/Home.py

api:
	uvicorn app.api.main:app --reload --port 8000

api-prod:
	uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 4

demo:
	python -m cli.main run-demo

# =============================================================================
# Earth Engine
# =============================================================================

auth:
	earthengine authenticate

# Show available periods
periods:
	python -m cli.main periods

# Show available indices
indices:
	python -m cli.main indices

# =============================================================================
# Clean
# =============================================================================

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf sandbox_report.html
	rm -rf sandbox_results.json
	rm -rf test_output.log
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# =============================================================================
# Docker
# =============================================================================

docker-build:
	docker build -t verdant-api .

docker-run:
	docker run -p 8000:8000 -v ~/.config/earthengine:/root/.config/earthengine verdant-api

docker-compose:
	docker-compose up -d

# =============================================================================
# Documentation
# =============================================================================

docs-serve:
	cd docs && python -m http.server 8080

# =============================================================================
# CI/CD Helpers
# =============================================================================

ci-test:
	pytest tests/ -v --tb=short --cov=engine --cov=services --cov-report=xml

ci-lint:
	ruff check engine/ services/ app/ --output-format=github
	mypy engine/ services/ --ignore-missing-imports
