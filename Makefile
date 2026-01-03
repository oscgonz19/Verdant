.PHONY: install dev-install test lint format clean app demo auth help

# Default target
help:
	@echo "Vegetation Change Intelligence Platform"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install      Install package"
	@echo "  dev-install  Install with development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo "  clean        Clean build artifacts"
	@echo "  app          Run Streamlit dashboard"
	@echo "  demo         Run demo analysis"
	@echo "  auth         Authenticate with Earth Engine"

# Installation
install:
	pip install -e .

dev-install:
	pip install -e ".[all]"

# Testing
test:
	pytest tests/ -v --cov=veg_change_engine

# Linting and formatting
lint:
	ruff check veg_change_engine/ cli/ app/
	mypy veg_change_engine/

format:
	black veg_change_engine/ cli/ app/
	isort veg_change_engine/ cli/ app/

# Clean
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Run applications
app:
	streamlit run app/Home.py

demo:
	python -m cli.main run-demo

# Earth Engine
auth:
	earthengine authenticate

# Show available periods
periods:
	python -m cli.main periods

# Show available indices
indices:
	python -m cli.main indices
