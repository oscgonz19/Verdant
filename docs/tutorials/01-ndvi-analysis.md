# Tutorial 1: Basic NDVI Analysis

Learn how to perform a basic vegetation analysis using NDVI.

## Prerequisites

- Platform installed (`pip install -e .`)
- Earth Engine authenticated (`earthengine authenticate`)
- Basic Python knowledge

## What You'll Learn

1. Load an area of interest
2. Create a satellite composite
3. Calculate NDVI
4. Visualize results
5. Export data

---

## Step 1: Setup

```python
# Import required modules
import ee
from engine.composites import create_landsat_composite
from engine.indices import add_ndvi
from engine.config import TEMPORAL_PERIODS

# Initialize Earth Engine
ee.Initialize()

print("Setup complete!")
```

## Step 2: Define Your Area of Interest

### Option A: Bounding Box

```python
# Define AOI as bounding box [west, south, east, north]
aoi = ee.Geometry.Rectangle([-62.5, -4.0, -62.0, -3.5])

# Get area in square kilometers
area_km2 = aoi.area().divide(1e6).getInfo()
print(f"AOI area: {area_km2:.2f} km²")
```

### Option B: Load from File

```python
from engine.io.aoi import load_aoi, aoi_to_ee_geometry

# Load from GeoJSON file
gdf = load_aoi('my_area.geojson')
aoi = aoi_to_ee_geometry(gdf)

print(f"Loaded AOI with {len(gdf)} features")
```

### Option C: Draw on Map

```python
import geemap

# Create interactive map
Map = geemap.Map(center=[-3.75, -62.25], zoom=9)
Map.add_draw_control()
Map
```

After drawing, extract the geometry:

```python
# Get drawn feature
if Map.draw_features:
    aoi = ee.Geometry(Map.draw_features[0]['geometry'])
    print("AOI captured from map!")
```

## Step 3: Create Satellite Composite

```python
# Get period configuration
period = TEMPORAL_PERIODS['present']

# Create cloud-free median composite
composite = create_landsat_composite(
    aoi=aoi,
    start_date=period['start'],
    end_date=period['end'],
    sensors=period['sensors'],
    cloud_threshold=20
)

# Check band names
print("Bands:", composite.bandNames().getInfo())
# Output: ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
```

## Step 4: Calculate NDVI

```python
# Add NDVI band to composite
composite_with_ndvi = add_ndvi(composite)

# Extract just the NDVI band
ndvi = composite_with_ndvi.select('ndvi')

# Get basic statistics
stats = ndvi.reduceRegion(
    reducer=ee.Reducer.percentile([5, 50, 95]),
    geometry=aoi,
    scale=30,
    maxPixels=1e9
).getInfo()

print(f"NDVI Statistics:")
print(f"  5th percentile: {stats['ndvi_p5']:.3f}")
print(f"  Median: {stats['ndvi_p50']:.3f}")
print(f"  95th percentile: {stats['ndvi_p95']:.3f}")
```

## Step 5: Visualize Results

### In Jupyter/geemap

```python
import geemap

Map = geemap.Map(center=[-3.75, -62.25], zoom=10)

# Add true color composite
Map.addLayer(
    composite.select(['red', 'green', 'blue']),
    {'min': 0, 'max': 0.3},
    'True Color'
)

# Add NDVI
Map.addLayer(
    ndvi,
    {'min': -0.2, 'max': 0.8, 'palette': ['brown', 'yellow', 'green', 'darkgreen']},
    'NDVI'
)

# Add colorbar
Map.add_colorbar(
    vis_params={'min': -0.2, 'max': 0.8, 'palette': ['brown', 'yellow', 'green', 'darkgreen']},
    label='NDVI',
    position='bottomright'
)

Map
```

### Save as HTML

```python
# Save interactive map
Map.to_html('ndvi_map.html')
print("Map saved to ndvi_map.html")
```

### Create Static Image

```python
import matplotlib.pyplot as plt
import numpy as np

# Download as numpy array (small areas only)
ndvi_array = geemap.ee_to_numpy(ndvi, region=aoi, scale=30)

# Plot
plt.figure(figsize=(10, 8))
plt.imshow(ndvi_array, cmap='RdYlGn', vmin=-0.2, vmax=0.8)
plt.colorbar(label='NDVI')
plt.title('NDVI Analysis')
plt.axis('off')
plt.savefig('ndvi_analysis.png', dpi=300, bbox_inches='tight')
plt.show()
```

## Step 6: Export Results

### To Google Drive

```python
from engine.io.exporters import export_to_drive

# Export NDVI as GeoTIFF
task = export_to_drive(
    image=ndvi,
    description='NDVI_Analysis',
    folder='VegChange/Tutorial',
    region=aoi,
    scale=30
)

task.start()
print(f"Export started: {task.id}")

# Monitor progress
import time
while task.status()['state'] == 'RUNNING':
    print(f"Progress: {task.status()}")
    time.sleep(10)

print(f"Export complete: {task.status()['state']}")
```

### Export Statistics as CSV

```python
import pandas as pd

# Create NDVI histogram
histogram = ndvi.reduceRegion(
    reducer=ee.Reducer.histogram(100, 0.01),
    geometry=aoi,
    scale=30,
    maxPixels=1e9
).getInfo()

# Convert to DataFrame
hist_data = histogram['ndvi']
df = pd.DataFrame({
    'ndvi': hist_data['bucketMeans'],
    'count': hist_data['histogram']
})

df.to_csv('ndvi_histogram.csv', index=False)
print("Statistics saved to ndvi_histogram.csv")
```

---

## Complete Script

Here's the complete analysis in one script:

```python
"""
Basic NDVI Analysis
==================
Analyzes vegetation using NDVI for a given area of interest.
"""

import ee
from engine.composites import create_landsat_composite
from engine.indices import add_ndvi
from engine.io.aoi import load_aoi, aoi_to_ee_geometry
from engine.io.exporters import export_to_drive
from engine.config import TEMPORAL_PERIODS

# Initialize
ee.Initialize()

# Load AOI
gdf = load_aoi('my_area.geojson')
aoi = aoi_to_ee_geometry(gdf)

# Create composite
period = TEMPORAL_PERIODS['present']
composite = create_landsat_composite(
    aoi=aoi,
    start_date=period['start'],
    end_date=period['end'],
    sensors=period['sensors'],
    cloud_threshold=20
)

# Calculate NDVI
composite = add_ndvi(composite)
ndvi = composite.select('ndvi')

# Get statistics
stats = ndvi.reduceRegion(
    reducer=ee.Reducer.mean().combine(
        ee.Reducer.stdDev(), sharedInputs=True
    ),
    geometry=aoi,
    scale=30,
    maxPixels=1e9
).getInfo()

print(f"Mean NDVI: {stats['ndvi_mean']:.3f}")
print(f"Std Dev: {stats['ndvi_stdDev']:.3f}")

# Export
task = export_to_drive(
    image=ndvi,
    description='NDVI_Analysis',
    folder='VegChange',
    region=aoi,
    scale=30
)
task.start()

print(f"Export started: {task.id}")
```

---

## Exercises

1. **Compare Seasons**: Create NDVI composites for wet and dry seasons. What differences do you observe?

2. **Different Regions**: Analyze NDVI for different land cover types (forest, agriculture, urban). How do values differ?

3. **Resolution Comparison**: Export at 10m (Sentinel-2) and 30m (Landsat). What details are visible at each scale?

---

## Next Steps

- [Tutorial 2: Change Detection](02-change-detection.md) - Compare NDVI across time periods
- [Tutorial 3: Custom AOI](03-custom-aoi.md) - Work with complex geometries
- [Tutorial 4: API Integration](04-api-integration.md) - Use the REST API
