# Vegetation Change Intelligence Platform

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Earth Engine](https://img.shields.io/badge/Google-Earth%20Engine-green.svg)](https://earthengine.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**GEE-based satellite analysis for detecting and quantifying vegetation change over multi-decadal time periods.**

![Vegetation Change Detection](docs/assets/change_detection_example.png)

## Overview

The Vegetation Change Intelligence Platform automates the analysis of satellite imagery to track vegetation dynamics across large areas. Built on Google Earth Engine, it processes decades of Landsat and Sentinel-2 imagery to identify areas of vegetation loss, recovery, and stability.

### Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Sensor Fusion** | Combines Landsat 5/7/8 and Sentinel-2 for continuous temporal coverage |
| **Automated Cloud Masking** | QA-based cloud and shadow removal for clean composites |
| **Spectral Indices** | NDVI, NBR, NDWI, EVI, NDMI calculations |
| **Change Detection** | Threshold-based classification of vegetation change |
| **Data Persistence** | Cache system to avoid repeated API consumption |
| **Multiple Export Options** | Google Drive, Cloud Storage, or EE Assets |

### Temporal Coverage

| Period | Years | Sensors | Description |
|--------|-------|---------|-------------|
| 1990s | 1985-1999 | Landsat 5 TM | Historical baseline |
| 2000s | 2000-2012 | Landsat 5/7 | Early millennium |
| 2010s | 2013-2020 | Landsat 8 OLI | Recent decade |
| Present | 2021-2024 | Landsat 8 + Sentinel-2 | Current conditions |

## Installation

### Prerequisites

- Python 3.9+
- Google Earth Engine account ([Sign up](https://earthengine.google.com/signup/))
- Earth Engine Python API authenticated

### Install from Source

```bash
# Clone the repository
git clone https://github.com/oscgonz19/vegetation-change-platform.git
cd vegetation-change-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install package
pip install -e .

# Authenticate Earth Engine (first time only)
earthengine authenticate
```

## Quick Start

### Command Line Interface

```bash
# Run demo analysis
veg-change run-demo

# Analyze custom AOI
veg-change analyze \
    --aoi area.geojson \
    --periods 1990s,2010s,present \
    --indices ndvi,nbr \
    --export

# Generate preview map
veg-change preview --aoi area.geojson --period present --index ndvi

# List available periods and indices
veg-change periods
veg-change indices
```

### Python API

```python
import ee
ee.Initialize()

from veg_change_engine import run_full_analysis

# Run complete analysis
results = run_full_analysis(
    aoi_path="area.geojson",
    site_name="My Study Area",
    periods=["1990s", "2000s", "2010s", "present"],
    indices=["ndvi", "nbr"],
    export=True,
)

# Access results
composites = results["composites"]  # Dict of period -> ee.Image
changes = results["changes"]        # Dict of comparison -> ee.Image
```

### With Caching (Recommended)

```python
from veg_change_engine.io import setup_cache

# Setup cache to avoid repeated API calls
cache = setup_cache("users/myusername/veg_change_cache")

# Get composite (loads from cache if available)
composite = cache.get_composite(
    aoi=aoi,
    period="2010s",
    indices=["ndvi", "nbr"],
)

# Second call loads from cache - much faster!
composite2 = cache.get_composite(aoi, "2010s", ["ndvi", "nbr"])
```

### Streamlit Dashboard

```bash
# Launch interactive dashboard
streamlit run app/Home.py
```

## Architecture

```
vegetation-change-intelligence-platform/
├── veg_change_engine/          # Core Python package
│   ├── core/                   # Analysis algorithms
│   │   ├── composites.py       # Temporal composite generation
│   │   ├── indices.py          # Spectral index calculation
│   │   └── change.py           # Change detection & classification
│   ├── io/                     # Input/Output
│   │   ├── aoi.py              # AOI loading (KMZ, GeoJSON, etc.)
│   │   ├── exporters.py        # Export to Drive/Assets
│   │   └── cache.py            # Data persistence
│   ├── viz/                    # Visualization
│   │   ├── maps.py             # Folium map generation
│   │   └── colors.py           # Color palettes
│   ├── config.py               # Configuration & constants
│   └── pipeline.py             # Main orchestrator
├── cli/                        # Command-line interface
├── app/                        # Streamlit dashboard
├── docs/                       # Documentation (EN/ES)
└── tests/                      # Unit tests
```

## Change Detection Classes

The platform classifies vegetation change into 5 categories based on NDVI/NBR delta:

| Class | Label | Color | Threshold (dNDVI) |
|-------|-------|-------|-------------------|
| 1 | Strong Loss | 🔴 Red | < -0.15 |
| 2 | Moderate Loss | 🟠 Orange | -0.15 to -0.05 |
| 3 | Stable | 🟡 Yellow | -0.05 to +0.05 |
| 4 | Moderate Gain | 🟢 Light Green | +0.05 to +0.15 |
| 5 | Strong Gain | 🌲 Dark Green | > +0.15 |

## Configuration

### YAML Configuration File

```yaml
# config.yaml
site_name: "My Analysis Site"
site_description: "Vegetation monitoring project"
region: "Andes"
country: "Colombia"

periods:
  - "1990s"
  - "2000s"
  - "2010s"
  - "present"

indices:
  - "ndvi"
  - "nbr"

buffer_distance: 500.0  # meters
export_scale: 30        # meters (Landsat resolution)
cloud_threshold: 20.0   # percent
drive_folder: "VegChangeAnalysis"
```

### Python Configuration

```python
from veg_change_engine import VegChangeConfig

config = VegChangeConfig(
    site_name="My Site",
    periods=["1990s", "present"],
    indices=["ndvi", "nbr"],
    buffer_distance=500.0,
    cloud_threshold=20.0,
)

# Save configuration
config.to_yaml("config.yaml")

# Load configuration
config = VegChangeConfig.from_yaml("config.yaml")
```

## Supported Input Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| GeoPackage | `.gpkg` | OGC standard (recommended) |
| GeoJSON | `.geojson`, `.json` | Web-friendly format |
| Shapefile | `.shp` | Legacy format |
| KMZ | `.kmz` | Google Earth format |
| KML | `.kml` | Keyhole Markup Language |

## Output Products

### Temporal Composites
- Cloud-free median composites for each period
- Harmonized bands: blue, green, red, nir, swir1, swir2
- Spectral indices: ndvi, nbr, ndwi, evi, ndmi

### Change Detection Maps
- Delta indices (dNDVI, dNBR)
- Classified change (1-5 scale)
- Period comparison metadata

### Export Formats
- **GeoTIFF**: Cloud-optimized rasters
- **EE Assets**: Persistent cloud storage
- **PNG Maps**: Publication-ready visualizations

## API Reference

### Core Functions

```python
# Composites
from veg_change_engine.core import create_all_period_composites
composites = create_all_period_composites(aoi, periods, cloud_threshold)

# Indices
from veg_change_engine.core import add_all_indices
image_with_indices = add_all_indices(image, ["ndvi", "nbr"])

# Change Detection
from veg_change_engine.core import create_change_analysis
changes = create_change_analysis(composites, indices, reference_period)
```

### IO Functions

```python
# Load AOI
from veg_change_engine.io import load_aoi, aoi_to_ee_geometry
gdf = load_aoi("area.kmz")
aoi = aoi_to_ee_geometry(gdf)

# Export
from veg_change_engine.io import export_to_drive
task = export_to_drive(image, "output_name", aoi)
```

## Performance Tips

1. **Use Caching**: Set up asset caching to avoid recomputing composites
2. **Limit Periods**: Start with fewer periods for testing
3. **Reduce AOI Size**: Large areas take longer to process
4. **Increase Cloud Threshold**: If getting empty composites, allow more clouds
5. **Use Appropriate Scale**: 30m for Landsat, 10m for Sentinel-2

## Requirements

- Python 3.9+
- earthengine-api
- geopandas
- folium
- streamlit
- typer
- rich
- pyyaml

## Documentation

- [English Documentation](docs/en/)
- [Documentación en Español](docs/es/)

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Google Earth Engine](https://earthengine.google.com/) for cloud computing platform
- [Landsat](https://landsat.gsfc.nasa.gov/) and [Sentinel-2](https://sentinel.esa.int/web/sentinel/missions/sentinel-2) programs for satellite imagery
- Open source geospatial community

---

*Built for environmental monitoring and land change analysis*
