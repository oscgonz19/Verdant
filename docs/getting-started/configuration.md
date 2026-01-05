# Configuration Guide

Learn how to customize the Vegetation Change Intelligence Platform for your specific needs.

## Configuration Overview

The platform uses a hierarchical configuration system:
1. Default values in code
2. YAML configuration files
3. Environment variables
4. Runtime parameters

## VegChangeConfig Class

The main configuration class:

```python
from engine.config import VegChangeConfig

config = VegChangeConfig(
    # Site identification
    site_name="My Analysis Site",
    site_description="Vegetation monitoring project",
    region="Amazon",
    country="Brazil",

    # Analysis periods
    periods=["1990s", "2000s", "2010s", "present"],

    # Spatial parameters
    buffer_distance=500.0,  # meters around AOI
    export_scale=30,        # meters (Landsat resolution)

    # Processing parameters
    cloud_threshold=20.0,   # Max cloud cover %
    min_images=5,           # Minimum images for composite

    # Spectral indices
    indices=["ndvi", "nbr"],

    # Output configuration
    output_dir="outputs",
    export_to_drive=True,
    drive_folder="VegChangeAnalysis",

    # CRS
    target_epsg=4326,  # WGS84
)
```

## YAML Configuration

Save and load configurations from YAML:

```yaml
# config.yaml
site_name: "Amazon Monitoring"
site_description: "Deforestation detection project"
region: "Rondônia"
country: "Brazil"

periods:
  - "1990s"
  - "2000s"
  - "2010s"
  - "present"

buffer_distance: 500.0
export_scale: 30
cloud_threshold: 20.0
min_images: 5

indices:
  - "ndvi"
  - "nbr"

output_dir: "outputs"
export_to_drive: true
drive_folder: "VegChangeAnalysis"

target_epsg: 4326
```

Load from YAML:

```python
config = VegChangeConfig.from_yaml("config.yaml")
```

Save to YAML:

```python
config.to_yaml("my_config.yaml")
```

## Temporal Periods

### Default Periods

| Period | Date Range | Sensors | Description |
|--------|------------|---------|-------------|
| 1990s | 1985-1999 | Landsat 5 TM | Pre-2000 baseline |
| 2000s | 2000-2012 | Landsat 5/7 | Early 2000s |
| 2010s | 2013-2020 | Landsat 8 OLI | Recent decade |
| present | 2021-2024 | Landsat 8 + Sentinel-2 | Current |

### Custom Periods

```python
from engine.config import TEMPORAL_PERIODS

# View period configuration
for name, info in TEMPORAL_PERIODS.items():
    print(f"{name}: {info['start']} to {info['end']}")
    print(f"  Sensors: {info['sensors']}")
```

## Spectral Indices

### Available Indices

| Index | Full Name | Use Case |
|-------|-----------|----------|
| ndvi | Normalized Difference Vegetation Index | Vegetation health |
| nbr | Normalized Burn Ratio | Fire/disturbance |
| ndwi | Normalized Difference Water Index | Water detection |
| evi | Enhanced Vegetation Index | High biomass areas |
| ndmi | Normalized Difference Moisture Index | Drought stress |

### Index Selection

```python
# Single index
config = VegChangeConfig(indices=["ndvi"])

# Multiple indices
config = VegChangeConfig(indices=["ndvi", "nbr", "ndwi"])
```

## Change Detection Thresholds

### Default Thresholds

```python
from engine.config import CHANGE_THRESHOLDS

# dNDVI thresholds
CHANGE_THRESHOLDS["dndvi"] = {
    "strong_loss": -0.15,
    "moderate_loss": -0.05,
    "stable_min": -0.05,
    "stable_max": 0.05,
    "moderate_gain": 0.05,
    "strong_gain": 0.15,
}

# dNBR thresholds (more sensitive)
CHANGE_THRESHOLDS["dnbr"] = {
    "strong_loss": -0.20,
    "moderate_loss": -0.10,
    "stable_min": -0.10,
    "stable_max": 0.10,
    "moderate_gain": 0.10,
    "strong_gain": 0.20,
}
```

### Custom Thresholds

```python
from engine.change import ChangeThresholds, ThresholdClassifier

# Create custom thresholds
custom_thresholds = ChangeThresholds(
    strong_loss=-0.20,
    moderate_loss=-0.08,
    stable_min=-0.08,
    stable_max=0.08,
    moderate_gain=0.08,
    strong_gain=0.20,
)

# Use with classifier
classifier = ThresholdClassifier(custom_thresholds)
classified = classifier.classify(delta_image)
```

## Visualization Parameters

### Default Visualization

```python
from engine.config import VIS_PARAMS

# NDVI visualization
VIS_PARAMS["ndvi"] = {
    "min": -0.2,
    "max": 0.8,
    "palette": ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"]
}

# Change classification
VIS_PARAMS["change_class"] = {
    "min": 1,
    "max": 5,
    "palette": ["#d7191c", "#fdae61", "#ffffbf", "#a6d96a", "#1a9641"]
}
```

### Custom Visualization

```python
custom_vis = {
    "min": 0,
    "max": 1,
    "palette": ["blue", "white", "green"]
}

map_id = image.getMapId(custom_vis)
```

## Export Configuration

### Google Drive Export

```python
from engine.io.exporters import ExportConfig

export_config = ExportConfig(
    drive_folder="MyAnalysis",
    scale=30,                           # Export resolution
    prefix="veg_change",                # File name prefix
    date_format="%Y%m%d",               # Date in filename
    crs="EPSG:4326",                    # Coordinate system
    format_options={"cloudOptimized": True}  # Cloud-optimized GeoTIFF
)
```

### Export Scale Guidelines

| Resolution | Use Case | File Size |
|------------|----------|-----------|
| 10m | High detail, Sentinel-2 | Largest |
| 30m | Standard Landsat | Medium |
| 100m | Regional overview | Smaller |
| 500m | Continental scale | Smallest |

## API Configuration

### FastAPI Settings

```python
# Environment variables for API
CORS_ORIGINS="*"
MAX_JOBS=100
JOB_TIMEOUT=3600
```

### Running API

```bash
# Development
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.api.main:app --workers 4 --host 0.0.0.0 --port 8000
```

## Caching Configuration

### Asset Cache

```python
from engine.io.cache import AssetCache

cache = AssetCache(
    asset_folder="users/myuser/veg_cache"
)
```

### Local Cache

```python
from engine.io.cache import LocalCache

cache = LocalCache(
    cache_dir=".veg_change_cache"  # Local directory
)
```

## Best Practices

### 1. Cloud Threshold

- **20%**: Good balance for most regions
- **10%**: Stricter, fewer but cleaner images
- **40%**: More lenient, useful for cloudy regions

### 2. Buffer Distance

- **500m**: Standard buffer for edge effects
- **0m**: No buffer (exact AOI boundary)
- **1000m+**: Large buffer for context

### 3. Index Selection

- **Vegetation monitoring**: `ndvi`
- **Fire/disturbance**: `nbr`, `ndvi`
- **Comprehensive**: `ndvi`, `nbr`, `ndmi`

## Next Steps

- [Architecture Overview](../technical/architecture.md)
- [API Reference](../technical/api-reference.md)
- [Methodology](../academic/methodology.md)
