"""
Pytest configuration and fixtures for Verdant testing.

This module provides:
- Shared fixtures for all tests
- Mock Earth Engine objects
- Sample data generators
- Test configuration
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Set test environment
    os.environ["VERDANT_ENV"] = "test"
    os.environ["VERDANT_LOG_LEVEL"] = "DEBUG"


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests based on path
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)


# =============================================================================
# Earth Engine Mocks
# =============================================================================

@pytest.fixture
def mock_ee():
    """Mock Earth Engine module for unit tests."""
    with patch.dict("sys.modules", {"ee": MagicMock()}):
        import ee

        # Mock basic EE objects
        ee.Initialize = MagicMock()
        ee.Geometry.Rectangle = MagicMock(return_value=Mock())
        ee.Geometry.Point = MagicMock(return_value=Mock())
        ee.Geometry.Polygon = MagicMock(return_value=Mock())

        # Mock Image
        mock_image = MagicMock()
        mock_image.select.return_value = mock_image
        mock_image.add.return_value = mock_image
        mock_image.subtract.return_value = mock_image
        mock_image.multiply.return_value = mock_image
        mock_image.divide.return_value = mock_image
        mock_image.rename.return_value = mock_image
        mock_image.addBands.return_value = mock_image
        mock_image.bandNames.return_value.getInfo.return_value = [
            "blue", "green", "red", "nir", "swir1", "swir2"
        ]
        ee.Image = MagicMock(return_value=mock_image)

        # Mock ImageCollection
        mock_collection = MagicMock()
        mock_collection.filterBounds.return_value = mock_collection
        mock_collection.filterDate.return_value = mock_collection
        mock_collection.filter.return_value = mock_collection
        mock_collection.map.return_value = mock_collection
        mock_collection.median.return_value = mock_image
        mock_collection.size.return_value.getInfo.return_value = 10
        ee.ImageCollection = MagicMock(return_value=mock_collection)

        # Mock Reducer
        ee.Reducer.mean = MagicMock()
        ee.Reducer.sum = MagicMock()
        ee.Reducer.count = MagicMock()
        ee.Reducer.histogram = MagicMock()

        yield ee


@pytest.fixture
def mock_ee_initialized(mock_ee):
    """Mock EE that's already initialized."""
    mock_ee.data._initialized = True
    return mock_ee


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_aoi_geojson() -> Dict[str, Any]:
    """Sample GeoJSON for testing."""
    return {
        "type": "Feature",
        "properties": {"name": "Test Area"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-62.5, -4.0],
                [-62.0, -4.0],
                [-62.0, -3.5],
                [-62.5, -3.5],
                [-62.5, -4.0]
            ]]
        }
    }


@pytest.fixture
def sample_bbox() -> Dict[str, float]:
    """Sample bounding box for testing."""
    return {
        "min_lon": -62.5,
        "min_lat": -4.0,
        "max_lon": -62.0,
        "max_lat": -3.5
    }


@pytest.fixture
def sample_analysis_config() -> Dict[str, Any]:
    """Sample analysis configuration."""
    return {
        "site_name": "Test Site",
        "periods": ["1990s", "present"],
        "indices": ["ndvi", "nbr"],
        "reference_period": "1990s",
        "cloud_threshold": 20.0,
        "export_scale": 30
    }


@pytest.fixture
def sample_statistics() -> Dict[str, Any]:
    """Sample change statistics for testing."""
    return {
        "total_pixels": 125000,
        "total_area_ha": 11250.0,
        "area_by_class": {
            "Strong Loss": 1234.5,
            "Moderate Loss": 2345.6,
            "Stable": 5000.2,
            "Moderate Gain": 1567.8,
            "Strong Gain": 1101.9
        },
        "percentage_by_class": {
            "Strong Loss": 10.97,
            "Moderate Loss": 20.85,
            "Stable": 44.45,
            "Moderate Gain": 13.94,
            "Strong Gain": 9.79
        }
    }


# =============================================================================
# File Fixtures
# =============================================================================

@pytest.fixture
def temp_geojson_file(tmp_path, sample_aoi_geojson) -> Path:
    """Create a temporary GeoJSON file."""
    filepath = tmp_path / "test_aoi.geojson"
    with open(filepath, "w") as f:
        json.dump(sample_aoi_geojson, f)
    return filepath


@pytest.fixture
def temp_config_file(tmp_path, sample_analysis_config) -> Path:
    """Create a temporary config file."""
    import yaml
    filepath = tmp_path / "config.yaml"
    with open(filepath, "w") as f:
        yaml.dump(sample_analysis_config, f)
    return filepath


# =============================================================================
# API Testing Fixtures
# =============================================================================

@pytest.fixture
def api_client():
    """Create FastAPI test client."""
    from fastapi.testclient import TestClient

    # Mock EE before importing app
    with patch("ee.Initialize"):
        from app.api.main import app
        client = TestClient(app)
        yield client


@pytest.fixture
def mock_orchestrator():
    """Mock ChangeOrchestrator for API tests."""
    mock = MagicMock()
    mock.analyze.return_value = {
        "composites": {},
        "changes": {},
        "statistics": {
            "1990s_to_present_ndvi": {
                "area_by_class": {
                    "Strong Loss": 100.0,
                    "Stable": 800.0,
                    "Strong Gain": 100.0
                }
            }
        }
    }
    return mock


# =============================================================================
# Performance Testing Fixtures
# =============================================================================

@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.elapsed = None

        def start(self):
            self.start_time = time.perf_counter()
            return self

        def stop(self):
            self.end_time = time.perf_counter()
            self.elapsed = self.end_time - self.start_time
            return self.elapsed

        def __enter__(self):
            self.start()
            return self

        def __exit__(self, *args):
            self.stop()

    return Timer()


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_env():
    """Clean up environment after each test."""
    yield
    # Reset any modified environment variables
    if "VERDANT_ENV" in os.environ:
        del os.environ["VERDANT_ENV"]


@pytest.fixture
def isolated_filesystem(tmp_path):
    """Provide an isolated filesystem for tests."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)
