# Code Style Guide

Coding standards and style guidelines for the Vegetation Change Intelligence Platform.

## Overview

We use automated tools to enforce consistent code style:

- **Black**: Code formatting
- **isort**: Import sorting
- **Ruff**: Fast linting
- **mypy**: Type checking

---

## Quick Reference

```bash
# Format code
black veg_change_engine/ engine/ services/ app/ cli/
isort veg_change_engine/ engine/ services/ app/ cli/

# Or use make
make format

# Check style
ruff check .
mypy veg_change_engine/

# Or use make
make lint
```

---

## Python Style

### General Rules

- **Line length**: 100 characters maximum
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Trailing commas**: Yes, in multi-line structures

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | lowercase_with_underscores | `cloud_masking.py` |
| Classes | PascalCase | `ChangeOrchestrator` |
| Functions | lowercase_with_underscores | `calculate_ndvi()` |
| Constants | UPPERCASE_WITH_UNDERSCORES | `DEFAULT_SCALE` |
| Variables | lowercase_with_underscores | `cloud_threshold` |
| Private | Leading underscore | `_internal_method()` |

### Examples

```python
# Good
class SpectralIndex:
    """Base class for spectral indices."""

    DEFAULT_SCALE = 30

    def __init__(self, name: str):
        self.name = name
        self._cache = {}

    def calculate(self, image: ee.Image) -> ee.Image:
        """Calculate the index for an image."""
        return self._compute_index(image)

    def _compute_index(self, image: ee.Image) -> ee.Image:
        """Internal computation method."""
        pass


# Bad
class spectral_index:  # Should be PascalCase
    default_scale = 30  # Should be UPPERCASE

    def Calculate(self, Image):  # Should be lowercase
        pass
```

---

## Imports

### Order

1. Standard library imports
2. Third-party imports
3. Local application imports

Each group separated by a blank line.

```python
# Standard library
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party
import ee
import geopandas as gpd
import numpy as np
from pydantic import BaseModel

# Local application
from engine.config import TEMPORAL_PERIODS
from engine.indices import add_ndvi
from services.change_orchestrator import ChangeOrchestrator
```

### Import Style

```python
# Good: explicit imports
from engine.indices import NDVIIndex, NBRIndex, add_all_indices

# Acceptable: module import
from engine import indices
result = indices.add_ndvi(image)

# Bad: wildcard imports (except in __init__.py for re-exports)
from engine.indices import *
```

---

## Type Hints

### Required For

- Function parameters
- Function return types
- Class attributes

### Examples

```python
from typing import Any, Dict, List, Optional, Union

def create_composite(
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
    sensors: List[str],
    cloud_threshold: float = 20.0,
) -> ee.Image:
    """Create a cloud-free median composite."""
    pass


def analyze(
    config: Dict[str, Any],
    callback: Optional[Callable[[float], None]] = None,
) -> Dict[str, Union[ee.Image, Dict[str, float]]]:
    """Run analysis with optional progress callback."""
    pass


class AnalysisResult:
    """Container for analysis results."""

    composites: Dict[str, ee.Image]
    changes: Dict[str, ee.Image]
    statistics: Dict[str, Dict[str, float]]

    def __init__(
        self,
        composites: Dict[str, ee.Image],
        changes: Dict[str, ee.Image],
        statistics: Dict[str, Dict[str, float]],
    ) -> None:
        self.composites = composites
        self.changes = changes
        self.statistics = statistics
```

---

## Docstrings

### Format

Use Google-style docstrings:

```python
def create_landsat_composite(
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
    sensors: List[str],
    cloud_threshold: float = 20.0,
) -> ee.Image:
    """Create a cloud-free median composite from Landsat imagery.

    Creates a temporal median composite from the specified Landsat sensors,
    with cloud masking applied using QA bands.

    Args:
        aoi: Earth Engine geometry defining the area of interest.
        start_date: Start date in 'YYYY-MM-DD' format.
        end_date: End date in 'YYYY-MM-DD' format.
        sensors: List of Landsat sensor IDs (e.g., ['LANDSAT/LC08/C02/T1_L2']).
        cloud_threshold: Maximum cloud cover percentage (0-100). Defaults to 20.

    Returns:
        Cloud-free median composite with harmonized band names:
        blue, green, red, nir, swir1, swir2.

    Raises:
        ValueError: If no images found for the specified parameters.
        RuntimeError: If Earth Engine computation fails.

    Example:
        >>> aoi = ee.Geometry.Rectangle([-62.5, -4.0, -62.0, -3.5])
        >>> composite = create_landsat_composite(
        ...     aoi=aoi,
        ...     start_date='2023-01-01',
        ...     end_date='2023-12-31',
        ...     sensors=['LANDSAT/LC08/C02/T1_L2']
        ... )
    """
    pass
```

### Class Docstrings

```python
class ChangeOrchestrator:
    """Orchestrates vegetation change analysis workflows.

    This class coordinates the end-to-end process of vegetation change
    detection, including composite creation, index calculation, change
    detection, and statistics generation.

    Attributes:
        config: Configuration settings for analysis.
        cache: Optional asset cache for storing computed results.

    Example:
        >>> orchestrator = ChangeOrchestrator()
        >>> results = orchestrator.analyze(
        ...     aoi=my_geometry,
        ...     periods=['1990s', 'present'],
        ...     indices=['ndvi']
        ... )
    """

    def __init__(
        self,
        config: Optional[VegChangeConfig] = None,
        cache: Optional[AssetCache] = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            config: Optional configuration. Uses defaults if not provided.
            cache: Optional asset cache for result persistence.
        """
        self.config = config or VegChangeConfig()
        self.cache = cache
```

---

## Error Handling

### Exception Types

```python
# Use specific exceptions
class VegChangeError(Exception):
    """Base exception for vegetation change platform."""
    pass

class AOIError(VegChangeError):
    """Error related to area of interest processing."""
    pass

class CompositeError(VegChangeError):
    """Error during composite creation."""
    pass

# Usage
def load_aoi(path: str) -> gpd.GeoDataFrame:
    """Load AOI from file."""
    if not Path(path).exists():
        raise AOIError(f"AOI file not found: {path}")

    try:
        gdf = gpd.read_file(path)
    except Exception as e:
        raise AOIError(f"Failed to read AOI file: {e}") from e

    if gdf.empty:
        raise AOIError("AOI file contains no features")

    return gdf
```

### Error Messages

```python
# Good: specific, actionable
raise ValueError(
    f"Invalid cloud threshold: {value}. "
    f"Must be between 0 and 100."
)

# Bad: vague
raise ValueError("Invalid value")
```

---

## Comments

### When to Comment

- Complex algorithms
- Non-obvious business logic
- Workarounds and TODOs
- API quirks

### When NOT to Comment

- Obvious code
- Restating what the code does
- Outdated information

### Examples

```python
# Good: explains WHY
# Earth Engine requires coordinates in [lon, lat] order,
# but GeoJSON spec uses [lon, lat] so no conversion needed
coords = geometry.coordinates

# Good: documents workaround
# TODO(#123): Remove this workaround when EE fixes the bug
# Currently EE returns wrong scale for Sentinel-2 SWIR bands
scale = 20 if is_sentinel2 else 30

# Bad: restates the code
# Increment counter by 1
counter += 1

# Bad: outdated
# This function returns a list  (actually returns dict now)
def get_results():
    return {"key": "value"}
```

---

## Code Organization

### Module Structure

```python
"""Module docstring describing purpose.

This module provides functionality for...

Example:
    >>> from engine.module import function
    >>> result = function()
"""

# Imports (in order: stdlib, third-party, local)
from typing import Dict, List

import ee

from engine.config import DEFAULTS

# Constants
DEFAULT_SCALE = 30
MAX_PIXELS = 1e9

# Module-level variables (sparingly)
_cache: Dict[str, Any] = {}

# Classes
class MyClass:
    """Class docstring."""
    pass

# Functions
def public_function():
    """Public function docstring."""
    pass

def _private_function():
    """Private function docstring."""
    pass

# Main block (if applicable)
if __name__ == "__main__":
    main()
```

### Class Structure

```python
class SpectralIndex:
    """Class docstring."""

    # Class constants
    DEFAULT_BANDS = ["nir", "red"]

    # Class methods
    @classmethod
    def from_config(cls, config: Dict) -> "SpectralIndex":
        """Create from configuration."""
        pass

    # Static methods
    @staticmethod
    def validate_bands(bands: List[str]) -> bool:
        """Validate band names."""
        pass

    # Instance methods
    def __init__(self, name: str):
        """Initialize index."""
        self.name = name
        self._cache = {}

    def calculate(self, image: ee.Image) -> ee.Image:
        """Public method."""
        pass

    def _internal_method(self) -> None:
        """Private method."""
        pass

    # Properties
    @property
    def formula(self) -> str:
        """Get formula string."""
        return self._formula

    # Magic methods
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
```

---

## Testing Style

### Test Naming

```python
# Pattern: test_<function>_<scenario>_<expected>

def test_add_ndvi_valid_image_returns_ndvi_band():
    """Test NDVI calculation with valid input."""
    pass

def test_add_ndvi_missing_bands_raises_error():
    """Test error handling for missing bands."""
    pass

def test_create_composite_empty_collection_raises_error():
    """Test handling of empty image collection."""
    pass
```

### Test Structure

```python
import pytest

class TestNDVIIndex:
    """Tests for NDVI index calculation."""

    @pytest.fixture
    def sample_image(self):
        """Create sample image for tests."""
        return create_mock_image()

    def test_basic_calculation(self, sample_image):
        """Test basic NDVI calculation."""
        # Arrange
        index = NDVIIndex()

        # Act
        result = index.calculate(sample_image)

        # Assert
        assert "ndvi" in result.bandNames().getInfo()

    def test_handles_negative_values(self, sample_image):
        """Test handling of negative reflectance values."""
        # Arrange
        index = NDVIIndex()
        negative_image = sample_image.multiply(-1)

        # Act
        result = index.calculate(negative_image)

        # Assert
        stats = result.reduceRegion(...).getInfo()
        assert stats["ndvi_min"] >= -1
        assert stats["ndvi_max"] <= 1
```

---

## Configuration Files

### pyproject.toml

```toml
[tool.black]
line-length = 100
target-version = ["py39", "py310", "py311"]

[tool.isort]
profile = "black"
line_length = 100

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N", "D", "UP"]
ignore = ["D100", "D104"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_ignores = true
ignore_missing_imports = true
```

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
```

---

## Common Patterns

### Factory Pattern

```python
class AOILoaderFactory:
    """Factory for creating AOI loaders."""

    _loaders: Dict[str, Type[AOILoader]] = {}

    @classmethod
    def register(cls, extension: str, loader: Type[AOILoader]) -> None:
        """Register a loader for a file extension."""
        cls._loaders[extension] = loader

    @classmethod
    def create(cls, path: str) -> AOILoader:
        """Create appropriate loader for file."""
        ext = Path(path).suffix.lower()
        if ext not in cls._loaders:
            raise ValueError(f"No loader for extension: {ext}")
        return cls._loaders[ext]()
```

### Registry Pattern

```python
INDEX_REGISTRY: Dict[str, Type[SpectralIndex]] = {}

def register_index(cls: Type[SpectralIndex]) -> Type[SpectralIndex]:
    """Decorator to register an index class."""
    INDEX_REGISTRY[cls.name] = cls
    return cls

@register_index
class NDVIIndex(SpectralIndex):
    name = "ndvi"
```

### Context Manager

```python
from contextlib import contextmanager

@contextmanager
def ee_session(project: str):
    """Context manager for Earth Engine session."""
    try:
        ee.Initialize(project=project)
        yield
    finally:
        # Cleanup if needed
        pass

# Usage
with ee_session("my-project"):
    composite = create_composite(...)
```

---

## Anti-Patterns to Avoid

### 1. God Classes

```python
# Bad: class does too much
class AnalysisManager:
    def load_aoi(self): ...
    def create_composite(self): ...
    def calculate_ndvi(self): ...
    def export_to_drive(self): ...
    def send_email(self): ...

# Good: separate concerns
class AOILoader: ...
class CompositeCreator: ...
class IndexCalculator: ...
class Exporter: ...
```

### 2. Magic Numbers

```python
# Bad
if cloud_cover < 20:
    include_image()

# Good
MAX_CLOUD_COVER = 20

if cloud_cover < MAX_CLOUD_COVER:
    include_image()
```

### 3. Deep Nesting

```python
# Bad
if condition1:
    if condition2:
        if condition3:
            do_something()

# Good: early returns
if not condition1:
    return
if not condition2:
    return
if not condition3:
    return
do_something()
```

---

## Resources

- [PEP 8](https://pep8.org/) - Python Style Guide
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Black Documentation](https://black.readthedocs.io/)
- [Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
