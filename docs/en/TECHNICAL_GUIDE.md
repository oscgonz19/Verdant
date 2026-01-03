# Technical Guide

## API Reference, Configuration, and Extension Guide

---

## 1. Package Structure

```
veg_change_engine/
├── __init__.py          # Public API exports
├── config.py            # Configuration system
├── pipeline.py          # Main orchestrator
├── core/                # Analysis algorithms
│   ├── composites.py    # Temporal composite generation
│   ├── indices.py       # Spectral index calculation
│   └── change.py        # Change detection
├── io/                  # Input/Output
│   ├── aoi.py           # AOI loading
│   ├── exporters.py     # Export to Drive/Assets
│   └── cache.py         # Data persistence
└── viz/                 # Visualization
    ├── maps.py          # Folium map generation
    └── colors.py        # Color palettes
```

---

## 2. API Reference

### 2.1 High-Level Functions

```python
from veg_change_engine import analyze_vegetation_change, run_full_analysis

# Analyze with ee.Geometry
results = analyze_vegetation_change(
    aoi: ee.Geometry,
    periods: List[str] = ["1990s", "2000s", "2010s", "present"],
    indices: List[str] = ["ndvi", "nbr"],
    reference_period: str = "1990s",
    config: Optional[VegChangeConfig] = None,
) -> Dict[str, Any]

# Run from file
results = run_full_analysis(
    aoi_path: str,
    site_name: str = "Analysis Site",
    periods: Optional[List[str]] = None,
    indices: Optional[List[str]] = None,
    reference_period: str = "1990s",
    buffer_distance: float = 500.0,
    export: bool = False,
    export_folder: str = "VegChangeAnalysis",
) -> Dict[str, Any]
```

### 2.2 Core Functions

```python
from veg_change_engine.core import (
    create_all_period_composites,
    add_all_indices,
    create_change_analysis,
)

# Create composites
composites = create_all_period_composites(
    aoi: ee.Geometry,
    periods: List[str] = None,
    cloud_threshold: float = 20.0,
) -> Dict[str, ee.Image]

# Add indices
image = add_all_indices(
    image: ee.Image,
    indices: List[str] = ["ndvi", "nbr"],
) -> ee.Image

# Change analysis
changes = create_change_analysis(
    composites: Dict[str, ee.Image],
    indices: List[str] = ["ndvi", "nbr"],
    reference_period: str = "1990s",
) -> Dict[str, ee.Image]
```

### 2.3 IO Functions

```python
from veg_change_engine.io import (
    load_aoi,
    aoi_to_ee_geometry,
    export_to_drive,
    setup_cache,
)

# Load AOI from file
gdf = load_aoi(filepath: str) -> gpd.GeoDataFrame

# Convert to EE geometry
aoi = aoi_to_ee_geometry(gdf: gpd.GeoDataFrame) -> ee.Geometry

# Export to Drive
task = export_to_drive(
    image: ee.Image,
    name: str,
    region: ee.Geometry,
    folder: str = "VegChangeAnalysis",
    scale: int = 30,
) -> ee.batch.Task

# Setup caching
cache = setup_cache(asset_folder: str) -> CachedAnalysis
```

---

## 3. Configuration

### 3.1 VegChangeConfig Class

```python
from veg_change_engine import VegChangeConfig

@dataclass
class VegChangeConfig:
    # Site identification
    site_name: str = "Analysis Site"
    site_description: str = "Vegetation change analysis"
    region: str = "Region"
    country: str = "Country"

    # Analysis periods
    periods: List[str] = ["1990s", "2000s", "2010s", "present"]

    # Spatial parameters
    buffer_distance: float = 500.0  # meters
    export_scale: int = 30          # meters

    # Processing
    cloud_threshold: float = 20.0   # percent
    min_images: int = 5

    # Indices
    indices: List[str] = ["ndvi", "nbr"]

    # Output
    output_dir: str = "outputs"
    export_to_drive: bool = True
    drive_folder: str = "VegChangeAnalysis"
```

### 3.2 YAML Configuration

```yaml
# config.yaml
site_name: "My Analysis"
periods:
  - "1990s"
  - "present"
indices:
  - "ndvi"
  - "nbr"
buffer_distance: 500.0
cloud_threshold: 20.0
drive_folder: "VegChangeAnalysis"
```

### 3.3 Load/Save Configuration

```python
# From YAML
config = VegChangeConfig.from_yaml("config.yaml")

# Save to YAML
config.to_yaml("my_config.yaml")

# Programmatic
config = VegChangeConfig(
    site_name="My Site",
    periods=["2010s", "present"],
)
```

---

## 4. Temporal Periods

```python
from veg_change_engine.config import TEMPORAL_PERIODS

TEMPORAL_PERIODS = {
    "1990s": {
        "start": "1985-01-01",
        "end": "1999-12-31",
        "sensors": ["LANDSAT/LT05/C02/T1_L2"],
    },
    "2000s": {
        "start": "2000-01-01",
        "end": "2012-12-31",
        "sensors": ["LANDSAT/LE07/C02/T1_L2", "LANDSAT/LT05/C02/T1_L2"],
    },
    "2010s": {
        "start": "2013-01-01",
        "end": "2020-12-31",
        "sensors": ["LANDSAT/LC08/C02/T1_L2"],
    },
    "present": {
        "start": "2021-01-01",
        "end": "2024-12-31",
        "sensors": ["LANDSAT/LC08/C02/T1_L2", "COPERNICUS/S2_SR_HARMONIZED"],
    },
}
```

---

## 5. Caching System

### 5.1 Why Cache?

Earth Engine API calls can be slow and have quotas. Caching:
- Saves computed composites as EE Assets (persistent)
- Caches tile URLs locally (24-hour TTL)
- Dramatically speeds up repeated analyses

### 5.2 Using the Cache

```python
from veg_change_engine.io import setup_cache

# Initialize cache
cache = setup_cache("users/myusername/veg_change_cache")

# Get composite (loads from cache if available)
composite = cache.get_composite(
    aoi=aoi,
    period="2010s",
    indices=["ndvi", "nbr"],
)

# Force recompute
composite = cache.get_composite(
    aoi=aoi,
    period="2010s",
    indices=["ndvi"],
    force_recompute=True,
)

# Get change map with caching
change = cache.get_change_map(
    aoi=aoi,
    before_period="1990s",
    after_period="present",
    index="ndvi",
)

# List cached assets
cached = cache.list_cached_assets()

# Clear cache
cache.clear_cache(assets=True, local=True)
```

### 5.3 Cache Flow

```
Request → Check Local Cache → Check EE Asset → Compute → Cache → Return
           ↓ (hit)            ↓ (hit)
           Return URL         Return Image
```

---

## 6. Spectral Indices

### 6.1 Available Indices

| Index | Formula | Description |
|-------|---------|-------------|
| NDVI | (NIR - Red) / (NIR + Red) | Vegetation health |
| NBR | (NIR - SWIR2) / (NIR + SWIR2) | Burn severity |
| NDWI | (Green - NIR) / (Green + NIR) | Water content |
| EVI | 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1) | Enhanced vegetation |
| NDMI | (NIR - SWIR1) / (NIR + SWIR1) | Moisture content |

### 6.2 Adding Custom Indices

```python
from veg_change_engine.core.indices import SpectralIndex, register_index

class MyCustomIndex(SpectralIndex):
    @property
    def name(self) -> str:
        return "myindex"

    @property
    def description(self) -> str:
        return "My Custom Index"

    def calculate(self, image: ee.Image) -> ee.Image:
        # Custom calculation
        result = image.select("nir").divide(image.select("red"))
        return image.addBands(result.rename(self.name))

# Register
register_index(MyCustomIndex())
```

---

## 7. Change Detection

### 7.1 Thresholds

```python
CHANGE_THRESHOLDS = {
    "dndvi": {
        "strong_loss": -0.15,
        "moderate_loss": -0.05,
        "stable_min": -0.05,
        "stable_max": 0.05,
        "moderate_gain": 0.05,
        "strong_gain": 0.15,
    },
}
```

### 7.2 Custom Thresholds

```python
from veg_change_engine.core.change import ChangeThresholds, classify_change

custom = ChangeThresholds(
    strong_loss=-0.20,
    moderate_loss=-0.10,
    stable_min=-0.10,
    stable_max=0.10,
    moderate_gain=0.10,
    strong_gain=0.20,
)

classified = classify_change(delta_image, thresholds=custom)
```

---

## 8. CLI Reference

```bash
# Full analysis
veg-change analyze \
    --aoi area.geojson \
    --name "My Site" \
    --periods 1990s,2000s,2010s,present \
    --indices ndvi,nbr \
    --reference 1990s \
    --buffer 500 \
    --export \
    --folder MyFolder

# Quick preview
veg-change preview --aoi area.geojson --period present --index ndvi

# Show periods
veg-change periods

# Show indices
veg-change indices

# Run demo
veg-change run-demo

# Authenticate
veg-change auth
```

---

## 9. Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ee.EEException` | EE API error | Check authentication, quotas |
| `FileNotFoundError` | AOI file missing | Verify file path |
| `ValueError: No images` | Empty collection | Reduce cloud threshold, check dates |
| `CRSError` | Invalid projection | Data will be reprojected to WGS84 |

---

## 10. Performance Tips

1. **Use Caching**: Set up asset caching for repeated analyses
2. **Limit AOI Size**: Large areas take longer and may hit quotas
3. **Increase Cloud Threshold**: If composites are empty
4. **Reduce Periods**: Start with fewer time periods
5. **Use Appropriate Scale**: 30m for Landsat, 10m for Sentinel-2 exports
