# Jupyter Notebooks Guide

Guide to using the educational Jupyter notebooks included with the platform.

## Overview

The platform includes educational notebooks that teach:

- Remote sensing fundamentals
- Spectral index calculation
- Change detection methodology
- Platform API usage

## Available Notebooks

```
notebooks/
├── 001_intro_ndvi.ipynb          # NDVI fundamentals
├── 002_change_detection.ipynb    # Change detection workflow
└── 003_train_rf_model.ipynb      # Machine learning (placeholder)
```

---

## Getting Started

### Installation

```bash
# Install Jupyter support
pip install -e ".[notebooks]"

# Or manually
pip install jupyter ipykernel geemap
```

### Starting Jupyter

```bash
# Launch Jupyter Lab (recommended)
jupyter lab

# Or classic notebook
jupyter notebook

# Navigate to notebooks/ directory
```

### Earth Engine Setup

Each notebook includes setup cells:

```python
import ee

# Initialize Earth Engine
try:
    ee.Initialize()
except:
    ee.Authenticate()
    ee.Initialize()

print("Earth Engine initialized!")
```

---

## Notebook 001: Introduction to NDVI

**File:** `001_intro_ndvi.ipynb`

### Learning Objectives

- Understand NDVI theory and formula
- Load Landsat imagery in Earth Engine
- Calculate NDVI from scratch
- Compare manual vs platform calculation
- Visualize results with folium

### Sections

#### 1. What is NDVI?

Theoretical background on the Normalized Difference Vegetation Index:

```python
# NDVI Formula
# NDVI = (NIR - Red) / (NIR + Red)

# Values range from -1 to 1:
# - Dense vegetation: 0.6 - 0.9
# - Sparse vegetation: 0.2 - 0.4
# - Bare soil: 0.0 - 0.2
# - Water: < 0 (negative)
```

#### 2. Loading Landsat Imagery

```python
import ee

# Define area of interest
aoi = ee.Geometry.Rectangle([-62.5, -4.0, -62.0, -3.5])

# Load Landsat 8 Collection 2
collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
    .filterBounds(aoi)
    .filterDate('2023-01-01', '2023-12-31')
    .filter(ee.Filter.lt('CLOUD_COVER', 20)))

print(f"Found {collection.size().getInfo()} images")
```

#### 3. Manual NDVI Calculation

```python
# Get a single image
image = collection.median()

# Apply scale factors
def apply_scale(img):
    optical = img.select('SR_B.').multiply(0.0000275).add(-0.2)
    return img.addBands(optical, overwrite=True)

image = apply_scale(image)

# Calculate NDVI manually
nir = image.select('SR_B5')
red = image.select('SR_B4')
ndvi_manual = nir.subtract(red).divide(nir.add(red)).rename('ndvi')
```

#### 4. Using the Platform

```python
from engine.indices import add_ndvi

# Much simpler!
ndvi_platform = add_ndvi(image)
```

#### 5. Visualization

```python
import geemap

# Create map
Map = geemap.Map(center=[-3.75, -62.25], zoom=10)

# Add NDVI layer
vis_params = {
    'min': -0.2,
    'max': 0.8,
    'palette': ['red', 'yellow', 'green', 'darkgreen']
}
Map.addLayer(ndvi_manual, vis_params, 'NDVI')
Map
```

### Exercises

1. Calculate NDVI for a different region
2. Compare NDVI between wet and dry seasons
3. Create an NDVI time series animation

---

## Notebook 002: Change Detection

**File:** `002_change_detection.ipynb`

### Learning Objectives

- Understand change detection concepts
- Create multi-temporal composites
- Calculate delta indices
- Classify changes into categories
- Generate change statistics

### Sections

#### 1. Change Detection Concepts

```python
# Change = After - Before
#
# For NDVI:
#   Negative change = Vegetation loss
#   Positive change = Vegetation gain
#
# Classification thresholds:
#   Strong Loss:    dNDVI < -0.15
#   Moderate Loss:  -0.15 <= dNDVI < -0.05
#   Stable:         -0.05 <= dNDVI <= 0.05
#   Moderate Gain:  0.05 < dNDVI <= 0.15
#   Strong Gain:    dNDVI > 0.15
```

#### 2. Creating Temporal Composites

```python
from engine.composites import create_landsat_composite
from engine.config import TEMPORAL_PERIODS

aoi = ee.Geometry.Rectangle([-62.5, -4.0, -62.0, -3.5])

# Create composites for two periods
composite_1990s = create_landsat_composite(
    aoi=aoi,
    start_date=TEMPORAL_PERIODS['1990s']['start'],
    end_date=TEMPORAL_PERIODS['1990s']['end'],
    sensors=TEMPORAL_PERIODS['1990s']['sensors']
)

composite_present = create_landsat_composite(
    aoi=aoi,
    start_date=TEMPORAL_PERIODS['present']['start'],
    end_date=TEMPORAL_PERIODS['present']['end'],
    sensors=TEMPORAL_PERIODS['present']['sensors']
)
```

#### 3. Calculating Delta Indices

```python
from engine.indices import add_ndvi, calculate_delta_indices

# Add NDVI to both composites
composite_1990s = add_ndvi(composite_1990s)
composite_present = add_ndvi(composite_present)

# Calculate change
delta = calculate_delta_indices(
    before=composite_1990s,
    after=composite_present,
    indices=['ndvi']
)

# delta contains 'dndvi' band
```

#### 4. Classifying Changes

```python
from engine.change import classify_change

change_map = classify_change(
    delta_image=delta,
    index='ndvi',
    thresholds={
        'strong_loss': -0.15,
        'moderate_loss': -0.05,
        'moderate_gain': 0.05,
        'strong_gain': 0.15
    }
)

# Result: Image with values 1-5
# 1 = Strong Loss (red)
# 2 = Moderate Loss (orange)
# 3 = Stable (yellow)
# 4 = Moderate Gain (light green)
# 5 = Strong Gain (dark green)
```

#### 5. Generating Statistics

```python
from engine.change import generate_change_statistics

stats = generate_change_statistics(
    change_map=change_map,
    aoi=aoi,
    scale=30
)

# Output:
# {
#     'total_pixels': 125000,
#     'area_by_class': {
#         'Strong Loss': 1234.5,    # hectares
#         'Moderate Loss': 2345.6,
#         'Stable': 15000.2,
#         'Moderate Gain': 4567.8,
#         'Strong Gain': 1852.4
#     }
# }
```

#### 6. Full Workflow with Platform

```python
from services.change_orchestrator import ChangeOrchestrator

orchestrator = ChangeOrchestrator()

results = orchestrator.analyze(
    aoi=aoi,
    periods=['1990s', 'present'],
    indices=['ndvi', 'nbr'],
    reference_period='1990s'
)

print(results['statistics'])
```

### Exercises

1. Analyze a known deforestation area
2. Compare NDVI and NBR change detection
3. Create a time series of changes across all periods

---

## Notebook 003: Random Forest Classification

**File:** `003_train_rf_model.ipynb` (Placeholder)

### Planned Content

- Supervised classification concepts
- Preparing training data
- Feature engineering with spectral indices
- Training Random Forest in Earth Engine
- Accuracy assessment
- Integration with platform

---

## Creating Your Own Notebooks

### Template

```python
"""
Notebook: Custom Analysis
Author: Your Name
Date: 2024-01-15

Description:
    Your analysis description here.
"""

# %% [markdown]
# # Custom Analysis Notebook

# %% Setup
import ee
import geemap
from engine.composites import create_all_period_composites
from engine.indices import add_all_indices
from engine.change import create_change_analysis, generate_change_statistics

# Initialize Earth Engine
ee.Initialize()

# %% Define AOI
aoi = ee.Geometry.Rectangle([...])

# %% Analysis
# Your code here...

# %% Visualization
# Map creation...

# %% Export
# Export results...
```

### Best Practices

1. **Clear Section Headers**: Use markdown cells to organize
2. **Incremental Execution**: Test cells one at a time
3. **Avoid .getInfo() Loops**: Very slow - batch operations instead
4. **Save Intermediate Results**: Cache expensive computations
5. **Document Parameters**: Explain what each parameter does

---

## Interactive Widgets

### Using ipywidgets

```python
import ipywidgets as widgets
from IPython.display import display

# Period selector
period_widget = widgets.Dropdown(
    options=['1990s', '2000s', '2010s', 'present'],
    value='present',
    description='Period:'
)

# Index selector
index_widget = widgets.Dropdown(
    options=['ndvi', 'nbr', 'ndwi'],
    value='ndvi',
    description='Index:'
)

# Run button
run_button = widgets.Button(description='Run Analysis')

def on_click(b):
    period = period_widget.value
    index = index_widget.value
    # Run analysis...

run_button.on_click(on_click)

display(period_widget, index_widget, run_button)
```

### Using geemap

```python
import geemap

Map = geemap.Map()

# Add drawing controls
Map.add_draw_control()

# Get drawn features
def get_drawn_aoi():
    features = Map.draw_features
    if features:
        return ee.Geometry(features[0]['geometry'])
    return None

Map
```

---

## Troubleshooting

### Kernel Issues

```bash
# Reinstall kernel
python -m ipykernel install --user --name vegchange

# Select kernel in Jupyter
# Kernel > Change Kernel > vegchange
```

### Memory Issues

```python
# For large computations
import ee

# Use smaller region
aoi = aoi.buffer(-1000)  # Shrink AOI

# Use coarser scale
stats = image.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=aoi,
    scale=100,  # Increase scale
    maxPixels=1e8
)
```

### Visualization Issues

```python
# If map doesn't display
import geemap
geemap.set_proxy(port=1080)  # If behind proxy

# Alternative: use folium directly
import folium
m = folium.Map(location=[-3.75, -62.25], zoom_start=10)
```

---

## Resources

- [Google Earth Engine Docs](https://developers.google.com/earth-engine)
- [geemap Documentation](https://geemap.org)
- [Jupyter Lab Guide](https://jupyterlab.readthedocs.io)
