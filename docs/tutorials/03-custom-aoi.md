# Tutorial 3: Working with Custom AOIs

Learn how to work with various Area of Interest formats and geometries.

## Prerequisites

- Completed previous tutorials
- Understanding of GIS file formats

## What You'll Learn

1. Load different file formats
2. Handle multi-polygon geometries
3. Create buffers and simplify shapes
4. Work with administrative boundaries
5. Optimize large AOIs

---

## Supported Formats

The platform supports these AOI formats:

| Format | Extension | Best For |
|--------|-----------|----------|
| GeoJSON | .geojson, .json | Web maps, simple shapes |
| GeoPackage | .gpkg | Complex data, attributes |
| Shapefile | .shp (+.shx, .dbf) | Legacy GIS systems |
| KML/KMZ | .kml, .kmz | Google Earth exports |
| WKT | inline | Programmatic definitions |

---

## Loading AOIs

### From GeoJSON

```python
from engine.io.aoi import load_aoi, aoi_to_ee_geometry

# Load GeoJSON file
gdf = load_aoi('my_area.geojson')

# Inspect the data
print(f"Number of features: {len(gdf)}")
print(f"Columns: {list(gdf.columns)}")
print(f"CRS: {gdf.crs}")
print(f"Total area: {gdf.geometry.area.sum() / 1e6:.2f} km²")

# Convert to Earth Engine geometry
aoi = aoi_to_ee_geometry(gdf)
```

### From GeoPackage

```python
# GeoPackage can contain multiple layers
import geopandas as gpd

# List layers in file
layers = gpd.list_layers('data.gpkg')
print(f"Available layers: {layers}")

# Load specific layer
gdf = load_aoi('data.gpkg', layer='protected_areas')
aoi = aoi_to_ee_geometry(gdf)
```

### From Shapefile

```python
# Shapefile needs all components (.shp, .shx, .dbf)
gdf = load_aoi('boundary.shp')

# Check for encoding issues
if gdf.crs is None:
    gdf = gdf.set_crs('EPSG:4326')  # Assume WGS84

aoi = aoi_to_ee_geometry(gdf)
```

### From KMZ/KML

```python
# KMZ files are compressed KML
gdf = load_aoi('area.kmz')

# KML often has extra properties
print(gdf[['Name', 'description', 'geometry']])

aoi = aoi_to_ee_geometry(gdf)
```

### From Coordinates (Programmatic)

```python
import ee

# Rectangle (bounding box)
aoi = ee.Geometry.Rectangle([-62.5, -4.0, -62.0, -3.5])

# Polygon (custom shape)
aoi = ee.Geometry.Polygon([
    [-62.5, -4.0],
    [-62.0, -4.0],
    [-62.0, -3.5],
    [-62.3, -3.3],
    [-62.5, -3.5],
    [-62.5, -4.0]  # Close polygon
])

# Point with buffer
center = ee.Geometry.Point([-62.25, -3.75])
aoi = center.buffer(10000)  # 10km radius

# From WKT string
from shapely import wkt
shape = wkt.loads('POLYGON((-62.5 -4.0, -62.0 -4.0, -62.0 -3.5, -62.5 -3.5, -62.5 -4.0))')
aoi = ee.Geometry(shape.__geo_interface__)
```

---

## Handling Multi-Polygon AOIs

### Union Multiple Features

```python
# If GeoDataFrame has multiple rows
if len(gdf) > 1:
    # Option 1: Dissolve into single polygon
    gdf_dissolved = gdf.dissolve()
    aoi = aoi_to_ee_geometry(gdf_dissolved)

    # Option 2: Union all geometries
    from shapely.ops import unary_union
    union = unary_union(gdf.geometry)
    aoi = ee.Geometry(union.__geo_interface__)
```

### Process Features Separately

```python
# Analyze each feature independently
results = []

for idx, row in gdf.iterrows():
    feature_aoi = ee.Geometry(row.geometry.__geo_interface__)
    feature_name = row.get('name', f'Feature_{idx}')

    print(f"Processing: {feature_name}")

    result = orchestrator.analyze(
        aoi=feature_aoi,
        periods=['1990s', 'present'],
        indices=['ndvi']
    )

    results.append({
        'name': feature_name,
        'statistics': result['statistics']
    })

# Combine results
import pandas as pd
df = pd.DataFrame(results)
```

### Batch Processing

```python
from pathlib import Path

# Process all AOI files in a directory
aoi_dir = Path('aois/')

for aoi_file in aoi_dir.glob('*.geojson'):
    site_name = aoi_file.stem

    print(f"\n{'='*50}")
    print(f"Processing: {site_name}")
    print('='*50)

    gdf = load_aoi(str(aoi_file))
    aoi = aoi_to_ee_geometry(gdf)

    results = orchestrator.analyze(
        aoi=aoi,
        periods=['1990s', 'present'],
        indices=['ndvi']
    )

    # Save results
    output_file = f'results/{site_name}_statistics.json'
    with open(output_file, 'w') as f:
        json.dump(results['statistics'], f, indent=2)
```

---

## Geometry Operations

### Buffering

```python
from engine.io.aoi import create_buffered_aoi

# Add buffer to AOI
gdf_buffered = create_buffered_aoi(gdf, buffer_distance=500)  # meters
aoi = aoi_to_ee_geometry(gdf_buffered)

# Or in Earth Engine
aoi = aoi.buffer(500)  # meters
```

### Simplification

For complex polygons that slow down processing:

```python
# Simplify in GeoPandas (meters tolerance)
gdf_simple = gdf.copy()
gdf_simple.geometry = gdf_simple.geometry.simplify(100)  # 100m tolerance

# Or in Earth Engine
aoi = aoi.simplify(100)

# Check vertex count reduction
print(f"Original vertices: {original_count}")
print(f"Simplified vertices: {simplified_count}")
```

### Bounding Box

```python
# Get bounding box of complex geometry
bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
bbox = ee.Geometry.Rectangle(list(bounds))

# Useful for initial data filtering
collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
    .filterBounds(bbox)  # Fast filter
    .filterDate('2023-01-01', '2023-12-31'))

# Then clip to exact AOI
image = collection.median().clip(aoi)  # Precise clip
```

### Convex Hull

```python
# Create convex hull of scattered points
hull = gdf.geometry.unary_union.convex_hull
aoi = ee.Geometry(hull.__geo_interface__)
```

---

## Working with Administrative Boundaries

### From Natural Earth

```python
import geopandas as gpd

# Download country boundaries
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# Select country
brazil = world[world.name == 'Brazil']
aoi = aoi_to_ee_geometry(brazil)
```

### From GADM (via Earth Engine)

```python
# Load administrative boundaries from Earth Engine
gadm = ee.FeatureCollection('FAO/GAUL/2015/level1')

# Filter by name
amazonas = gadm.filter(ee.Filter.eq('ADM1_NAME', 'Amazonas'))
aoi = amazonas.geometry()
```

### From OpenStreetMap

```python
import osmnx as ox

# Download place boundary
gdf = ox.geocode_to_gdf('Manaus, Brazil')
aoi = aoi_to_ee_geometry(gdf)
```

---

## Optimizing Large AOIs

### Strategy 1: Tile-Based Processing

```python
def create_grid(aoi, tile_size_degrees=1.0):
    """Create grid of tiles covering AOI."""
    bounds = aoi.bounds().getInfo()['coordinates'][0]
    minx = min(c[0] for c in bounds)
    miny = min(c[1] for c in bounds)
    maxx = max(c[0] for c in bounds)
    maxy = max(c[1] for c in bounds)

    tiles = []
    x = minx
    while x < maxx:
        y = miny
        while y < maxy:
            tile = ee.Geometry.Rectangle([x, y, x + tile_size_degrees, y + tile_size_degrees])
            tile = tile.intersection(aoi)
            if tile.area().getInfo() > 0:
                tiles.append(tile)
            y += tile_size_degrees
        x += tile_size_degrees

    return tiles

# Process tiles
tiles = create_grid(aoi, tile_size_degrees=0.5)
print(f"Created {len(tiles)} tiles")

all_results = []
for i, tile in enumerate(tiles):
    print(f"Processing tile {i+1}/{len(tiles)}")
    result = orchestrator.analyze(aoi=tile, ...)
    all_results.append(result)

# Merge results
total_stats = merge_statistics(all_results)
```

### Strategy 2: Coarser Resolution

```python
# Use coarser scale for large areas
results = orchestrator.analyze(
    aoi=large_aoi,
    periods=['1990s', 'present'],
    indices=['ndvi'],
    config={'export_scale': 100}  # 100m instead of 30m
)
```

### Strategy 3: Sample-Based Analysis

```python
# Generate random sample points
points = ee.FeatureCollection.randomPoints(aoi, 1000)

# Sample composite at points
samples = composite.sampleRegions(
    collection=points,
    scale=30,
    geometries=True
)

# Analyze sample statistics
sample_stats = samples.aggregate_stats('ndvi').getInfo()
```

---

## Validation and Troubleshooting

### Check Geometry Validity

```python
from shapely.validation import make_valid

# Fix invalid geometries
gdf['geometry'] = gdf['geometry'].apply(lambda g: make_valid(g) if not g.is_valid else g)

# Check for issues
print(f"Valid geometries: {gdf.geometry.is_valid.all()}")
print(f"Empty geometries: {gdf.geometry.is_empty.any()}")
```

### Coordinate System Issues

```python
# Ensure WGS84 for Earth Engine
if gdf.crs != 'EPSG:4326':
    gdf = gdf.to_crs('EPSG:4326')
    print(f"Reprojected from {gdf.crs} to EPSG:4326")
```

### Large Geometry Errors

```python
# If getting "geometry too large" errors
try:
    aoi = aoi_to_ee_geometry(gdf)
except Exception as e:
    print(f"Error: {e}")

    # Simplify geometry
    gdf.geometry = gdf.geometry.simplify(500)
    aoi = aoi_to_ee_geometry(gdf)
```

---

## Complete Example: Protected Area Analysis

```python
"""
Analyze vegetation change in protected areas
"""

import ee
import geopandas as gpd
import pandas as pd
from engine.io.aoi import load_aoi, aoi_to_ee_geometry
from services.change_orchestrator import ChangeOrchestrator

ee.Initialize()

# Load protected areas
protected_areas = load_aoi('protected_areas.gpkg')
print(f"Loaded {len(protected_areas)} protected areas")

# Initialize orchestrator
orchestrator = ChangeOrchestrator()

# Analyze each protected area
results = []

for idx, row in protected_areas.iterrows():
    name = row['name']
    category = row['category']

    print(f"\nAnalyzing: {name} ({category})")

    try:
        aoi = ee.Geometry(row.geometry.__geo_interface__)

        analysis = orchestrator.analyze(
            aoi=aoi,
            periods=['1990s', 'present'],
            indices=['ndvi'],
            reference_period='1990s'
        )

        stats = analysis['statistics']['1990s_to_present_ndvi']

        results.append({
            'name': name,
            'category': category,
            'area_ha': row.geometry.area / 10000,
            'loss_ha': stats['area_by_class'].get('Strong Loss', 0) +
                      stats['area_by_class'].get('Moderate Loss', 0),
            'gain_ha': stats['area_by_class'].get('Strong Gain', 0) +
                      stats['area_by_class'].get('Moderate Gain', 0),
            'stable_ha': stats['area_by_class'].get('Stable', 0)
        })

    except Exception as e:
        print(f"  Error: {e}")
        results.append({'name': name, 'category': category, 'error': str(e)})

# Create summary DataFrame
df = pd.DataFrame(results)
df['loss_percent'] = df['loss_ha'] / df['area_ha'] * 100
df['gain_percent'] = df['gain_ha'] / df['area_ha'] * 100

# Sort by loss percentage
df_sorted = df.sort_values('loss_percent', ascending=False)

print("\n" + "="*60)
print("PROTECTED AREAS RANKED BY VEGETATION LOSS")
print("="*60)
print(df_sorted[['name', 'category', 'loss_percent', 'gain_percent']].to_string())

# Save results
df.to_csv('protected_areas_analysis.csv', index=False)
```

---

## Exercises

1. **Multi-Site Comparison**: Load 3-5 different protected areas and compare vegetation change
2. **Buffer Analysis**: Compare change inside vs outside a protected area (using buffers)
3. **Administrative Analysis**: Analyze change by municipality or district

---

## Next Steps

- [Tutorial 4: API Integration](04-api-integration.md) - Automate with REST API
