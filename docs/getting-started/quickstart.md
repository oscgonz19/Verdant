# Quick Start Guide

Get up and running with vegetation change analysis in 5 minutes.

## Prerequisites

Ensure you have:
- [Installed the platform](installation.md)
- Authenticated with Earth Engine (`earthengine authenticate`)

## Your First Analysis

### Option 1: Using Python

```python
import ee
ee.Initialize()

from services.change_orchestrator import run_full_analysis

# Run analysis on sample area
results = run_full_analysis(
    aoi_path="data/sample_aoi.geojson",  # Your AOI file
    site_name="My First Analysis",
    periods=["1990s", "present"],
    indices=["ndvi"],
    export=False,  # Set True to export to Google Drive
)

# View results
print(f"Composites: {list(results['composites'].keys())}")
print(f"Changes: {list(results['changes'].keys())}")
print(f"Area: {results['aoi_area_ha']:.1f} hectares")
```

### Option 2: Using the CLI

```bash
# List available commands
veg-change --help

# Run demo analysis
veg-change run-demo

# Analyze custom area
veg-change analyze \
    --aoi data/my_area.geojson \
    --periods 1990s,2010s,present \
    --indices ndvi,nbr \
    --site-name "My Site"

# Quick preview
veg-change preview \
    --aoi data/my_area.geojson \
    --period present \
    --index ndvi
```

### Option 3: Using the Dashboard

```bash
# Launch Streamlit dashboard
streamlit run app/Home.py

# Open browser to http://localhost:8501
```

### Option 4: Using the REST API

```bash
# Start API server
uvicorn app.api.main:app --reload

# Create analysis job
curl -X POST http://localhost:8000/analysis \
    -H "Content-Type: application/json" \
    -d '{
        "site_name": "Test Site",
        "bbox": {
            "min_lon": -62.5,
            "min_lat": -4.0,
            "max_lon": -62.0,
            "max_lat": -3.5
        },
        "periods": ["1990s", "present"],
        "indices": ["ndvi"]
    }'

# Check job status
curl http://localhost:8000/analysis/{job_id}
```

## Understanding the Output

### Composites

Median composites for each temporal period with harmonized bands:
- `blue`, `green`, `red`, `nir`, `swir1`, `swir2`
- Spectral indices: `ndvi`, `nbr`, etc.

### Change Maps

Delta indices showing change between periods:
- `dndvi`: NDVI change (positive = gain, negative = loss)
- `change_class`: Classified change (1-5 scale)

### Statistics

Summary statistics for the analysis:
```python
{
    "total_area_ha": 25000.5,
    "area_by_class": {
        "Strong Loss": 1234.5,
        "Moderate Loss": 2345.6,
        "Stable": 15000.2,
        "Moderate Gain": 4567.8,
        "Strong Gain": 1852.4
    }
}
```

## Change Classification

| Class | Label | dNDVI Range | Color |
|-------|-------|-------------|-------|
| 1 | Strong Loss | < -0.15 | Red |
| 2 | Moderate Loss | -0.15 to -0.05 | Orange |
| 3 | Stable | -0.05 to +0.05 | Yellow |
| 4 | Moderate Gain | +0.05 to +0.15 | Light Green |
| 5 | Strong Gain | > +0.15 | Dark Green |

## Sample Data

The platform includes sample data for testing:

```bash
data/
├── sample_aoi.geojson    # Amazon test area
├── rondonia.kmz          # Deforestation frontier
└── atlantic_forest.gpkg  # Atlantic Forest sample
```

## Visualization Example

```python
import folium
from engine.config import VIS_PARAMS

# Get NDVI visualization parameters
ndvi_vis = VIS_PARAMS['ndvi']

# Create map
m = folium.Map(location=[-3.75, -62.25], zoom_start=10)

# Add NDVI layer
ndvi_image = results['composites']['present'].select('ndvi')
map_id = ndvi_image.getMapId(ndvi_vis)

folium.TileLayer(
    tiles=map_id['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    name='NDVI'
).add_to(m)

m.save('ndvi_map.html')
```

## Next Steps

- [Configuration Guide](configuration.md) - Customize analysis parameters
- [CLI Guide](../guides/cli-guide.md) - Advanced CLI usage
- [Methodology](../academic/methodology.md) - Understanding the science
- [Tutorials](../tutorials/01-ndvi-analysis.md) - Detailed walkthroughs
