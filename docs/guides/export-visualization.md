# Export and Visualization Guide

Complete guide to exporting analysis results and visualizing them in external tools.

## Overview

The platform supports multiple export formats and visualization options:

- **GeoTIFF**: Standard raster format for GIS
- **Google Drive**: Cloud storage and sharing
- **Earth Engine Assets**: Persistent cloud storage
- **Tile URLs**: Web map integration
- **Statistics**: CSV/JSON data export

---

## Export Formats

### GeoTIFF

The standard format for geospatial raster data.

```python
from engine.io.exporters import export_to_drive

task = export_to_drive(
    image=change_map,
    description='NDVI_Change_2024',
    folder='VegChange',
    region=aoi,
    scale=30,
    crs='EPSG:4326',
    file_format='GeoTIFF'
)

# Start the export
task.start()

# Monitor progress
print(task.status())
```

**Options:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `scale` | Resolution in meters | 30 |
| `crs` | Coordinate system | EPSG:4326 |
| `maxPixels` | Max pixels to export | 1e10 |
| `fileFormat` | Output format | GeoTIFF |

### Cloud Optimized GeoTIFF (COG)

For efficient web streaming:

```python
task = export_to_drive(
    image=change_map,
    description='NDVI_Change_COG',
    folder='VegChange',
    region=aoi,
    scale=30,
    formatOptions={'cloudOptimized': True}
)
```

---

## Export Destinations

### Google Drive

Most common export destination:

```python
from engine.io.exporters import export_all_composites, export_all_changes

# Export all composites
export_all_composites(
    composites=results['composites'],
    aoi=aoi,
    folder='VegChange/Composites',
    scale=30
)

# Export all change maps
export_all_changes(
    changes=results['changes'],
    aoi=aoi,
    folder='VegChange/Changes',
    scale=30
)
```

**Folder Structure:**

```
Google Drive/
└── VegChange/
    ├── Composites/
    │   ├── 1990s_composite.tif
    │   ├── 2000s_composite.tif
    │   ├── 2010s_composite.tif
    │   └── present_composite.tif
    └── Changes/
        ├── 1990s_to_present_ndvi.tif
        └── 1990s_to_present_nbr.tif
```

### Earth Engine Assets

For persistent cloud storage and reuse:

```python
from engine.io.cache import AssetCache

cache = AssetCache(asset_folder='users/username/vegchange')

# Save composite as asset
cache.save_composite(
    composite=composite,
    period='present',
    aoi_hash='abc123'
)

# Load from cache
cached = cache.get_composite(
    period='present',
    aoi_hash='abc123'
)
```

### Local Download

Download directly to local machine (small areas only):

```python
import geemap

# Download as GeoTIFF
geemap.ee_export_image(
    image=change_map,
    filename='change_map.tif',
    scale=30,
    region=aoi
)

# Download as NumPy array
import numpy as np
array = geemap.ee_to_numpy(
    image=change_map,
    region=aoi,
    scale=30
)
```

---

## Visualization Options

### Web Map Tiles

Generate tile URLs for web maps:

```python
from engine.io.exporters import get_map_tile_url

tile_url = get_map_tile_url(
    image=change_map,
    vis_params={
        'min': 1,
        'max': 5,
        'palette': ['#d73027', '#fc8d59', '#fee08b', '#91cf60', '#1a9850']
    }
)

# Use in Leaflet, Mapbox, etc.
print(tile_url)
# https://earthengine.googleapis.com/v1alpha/.../{z}/{x}/{y}
```

### folium Integration

```python
import folium
import geemap.foliumap as geemap

# Create map
m = folium.Map(location=[-3.75, -62.25], zoom_start=10)

# Add Earth Engine layer
vis_params = {
    'min': -0.2,
    'max': 0.8,
    'palette': ['red', 'yellow', 'green']
}

# Add tile layer
m.add_ee_layer(ndvi_image, vis_params, 'NDVI')

# Add legend
m.add_legend(
    title='NDVI',
    colors=['red', 'yellow', 'green'],
    labels=['Low', 'Medium', 'High']
)

m.save('ndvi_map.html')
```

### geemap Integration

```python
import geemap

Map = geemap.Map(center=[-3.75, -62.25], zoom=10)

# Add layers with controls
Map.addLayer(composite.select(['red', 'green', 'blue']),
             {'min': 0, 'max': 0.3}, 'True Color')

Map.addLayer(ndvi,
             {'min': -0.2, 'max': 0.8, 'palette': ['red', 'yellow', 'green']},
             'NDVI')

Map.addLayer(change_map,
             {'min': 1, 'max': 5, 'palette': ['#d73027', '#fc8d59', '#fee08b', '#91cf60', '#1a9850']},
             'Change')

# Add colorbar
Map.add_colorbar(vis_params={'min': 1, 'max': 5},
                 label='Change Class',
                 orientation='vertical')

Map
```

---

## Visualization Palettes

### NDVI Palette

```python
NDVI_VIS = {
    'min': -0.2,
    'max': 0.8,
    'palette': [
        '#d73027',  # -0.2 to 0.0 (water/bare)
        '#fc8d59',  # 0.0 to 0.2 (sparse)
        '#fee08b',  # 0.2 to 0.4 (grassland)
        '#d9ef8b',  # 0.4 to 0.6 (shrubland)
        '#91cf60',  # 0.6 to 0.7 (forest)
        '#1a9850'   # 0.7 to 0.8 (dense forest)
    ]
}
```

### NBR Palette

```python
NBR_VIS = {
    'min': -0.5,
    'max': 0.7,
    'palette': [
        '#8c510a',  # Burned
        '#d8b365',  # Low veg
        '#f6e8c3',  # Sparse
        '#c7eae5',  # Moderate
        '#5ab4ac',  # Healthy
        '#01665e'   # Dense
    ]
}
```

### Change Classification Palette

```python
CHANGE_VIS = {
    'min': 1,
    'max': 5,
    'palette': [
        '#d73027',  # 1 - Strong Loss (red)
        '#fc8d59',  # 2 - Moderate Loss (orange)
        '#fee08b',  # 3 - Stable (yellow)
        '#91cf60',  # 4 - Moderate Gain (light green)
        '#1a9850'   # 5 - Strong Gain (dark green)
    ]
}
```

---

## GIS Software Integration

### QGIS

1. Export GeoTIFF to Google Drive
2. Download from Drive
3. Open in QGIS: Layer > Add Layer > Add Raster Layer

**Styling in QGIS:**

```
Properties > Symbology > Render Type: Singleband Pseudocolor
  Color Ramp: RdYlGn
  Mode: Equal Interval
  Classes: 5
```

### ArcGIS Pro

1. Export GeoTIFF
2. Add to Map
3. Apply symbology:
   - Right-click layer > Symbology
   - Primary symbology: Classify
   - Field: Value
   - Classes: 5
   - Color scheme: Red-Yellow-Green

### Google Earth Pro

1. Export as KMZ (with overlay)
2. Open in Google Earth Pro

```python
# Export with KML overlay
geemap.ee_export_image_to_drive(
    image=change_map,
    description='change_kml',
    folder='VegChange',
    region=aoi,
    scale=30,
    file_per_band=False
)
```

---

## Statistics Export

### CSV Export

```python
import pandas as pd

# Convert statistics to DataFrame
stats_df = pd.DataFrame([
    {'class': 'Strong Loss', 'area_ha': 1234.5, 'percent': 4.9},
    {'class': 'Moderate Loss', 'area_ha': 2345.6, 'percent': 9.4},
    {'class': 'Stable', 'area_ha': 15000.2, 'percent': 60.0},
    {'class': 'Moderate Gain', 'area_ha': 4567.8, 'percent': 18.3},
    {'class': 'Strong Gain', 'area_ha': 1852.4, 'percent': 7.4}
])

# Save to CSV
stats_df.to_csv('change_statistics.csv', index=False)
```

### JSON Export

```python
import json

results = {
    'site_name': 'Amazon Forest Reserve',
    'analysis_date': '2024-01-15',
    'periods': ['1990s', 'present'],
    'statistics': {
        '1990s_to_present_ndvi': {
            'total_area_ha': 25000.5,
            'area_by_class': {
                'Strong Loss': 1234.5,
                'Moderate Loss': 2345.6,
                'Stable': 15000.2,
                'Moderate Gain': 4567.8,
                'Strong Gain': 1852.4
            }
        }
    }
}

with open('analysis_results.json', 'w') as f:
    json.dump(results, f, indent=2)
```

---

## Batch Export

### Export Multiple Analyses

```python
from pathlib import Path

aoi_files = list(Path('aois').glob('*.geojson'))

for aoi_file in aoi_files:
    site_name = aoi_file.stem

    # Run analysis
    results = orchestrator.analyze_from_file(
        aoi_path=str(aoi_file),
        site_name=site_name,
        periods=['1990s', 'present'],
        indices=['ndvi']
    )

    # Export results
    export_all_changes(
        changes=results['changes'],
        aoi=results['aoi'],
        folder=f'VegChange/{site_name}',
        scale=30
    )
```

### Monitor Export Tasks

```python
import ee
import time

# Get all running tasks
tasks = ee.batch.Task.list()

# Monitor until complete
while True:
    running = [t for t in tasks if t.status()['state'] == 'RUNNING']
    if not running:
        break

    for task in running:
        status = task.status()
        print(f"{status['description']}: {status['state']}")

    time.sleep(30)
    tasks = ee.batch.Task.list()

print("All exports complete!")
```

---

## Visualization Examples

### Side-by-Side Comparison

```python
import matplotlib.pyplot as plt
import geemap

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Before image
axes[0].set_title('1990s NDVI')
# Add raster visualization...

# After image
axes[1].set_title('Present NDVI')
# Add raster visualization...

plt.tight_layout()
plt.savefig('comparison.png', dpi=300)
```

### Change Animation

```python
import geemap

# Create animated GIF
geemap.create_timelapse(
    collection=ndvi_collection,
    out_gif='ndvi_timelapse.gif',
    region=aoi,
    dimensions=500,
    framesPerSecond=2,
    vis_params=NDVI_VIS
)
```

### Interactive Dashboard

```python
import panel as pn
pn.extension()

# Create widgets
period_select = pn.widgets.Select(
    name='Period',
    options=['1990s', '2000s', '2010s', 'present']
)

# Create map view
map_pane = pn.pane.HTML(...)

# Layout
dashboard = pn.Column(
    '# Vegetation Change Dashboard',
    pn.Row(period_select),
    map_pane
)

dashboard.servable()
```

---

## Tips and Best Practices

### 1. Choose Appropriate Scale

| AOI Size | Recommended Scale |
|----------|-------------------|
| < 100 km² | 10-30 m |
| 100-1000 km² | 30 m |
| 1000-10000 km² | 30-100 m |
| > 10000 km² | 100-250 m |

### 2. Optimize File Size

- Use Cloud Optimized GeoTIFF for web
- Compress with LZW or DEFLATE
- Export only needed bands

### 3. Consistent Projections

```python
# Always specify CRS
export_to_drive(
    image=change_map,
    crs='EPSG:32720',  # UTM zone 20S
    crsTransform=[30, 0, xmin, 0, -30, ymax]
)
```

### 4. Document Exports

Include metadata with exports:

```python
image = image.set({
    'source': 'VegChange Platform',
    'analysis_date': '2024-01-15',
    'periods': '1990s to present',
    'index': 'ndvi'
})
```
