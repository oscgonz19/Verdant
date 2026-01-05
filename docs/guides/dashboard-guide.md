# Dashboard User Guide

Complete guide to using the Streamlit-based web dashboard for vegetation change analysis.

## Overview

The dashboard provides an interactive web interface for:

- Visual AOI selection and upload
- Real-time analysis configuration
- Interactive map visualization
- Results exploration and export

## Starting the Dashboard

```bash
# Using Streamlit directly
streamlit run app/Home.py

# Using make
make app

# With custom port
streamlit run app/Home.py --server.port 8502
```

The dashboard will open at `http://localhost:8501`

---

## Home Page

The home page provides an overview of the platform and quick links to main features.

### Features

- Platform introduction and capabilities
- Quick start links to analysis pages
- Recent analyses (if any)
- System status (Earth Engine connection)

---

## Analysis Page

The main analysis interface for running vegetation change detection.

### Step 1: Define Area of Interest

#### Option A: Upload File

Supported formats:
- **GeoJSON** (.geojson, .json)
- **GeoPackage** (.gpkg)
- **KML/KMZ** (.kml, .kmz)
- **Shapefile** (.shp with .shx, .dbf)

```
[Upload AOI File]  [Browse...]
```

#### Option B: Draw on Map

1. Click the polygon tool in the map toolbar
2. Click points to define vertices
3. Double-click to complete the polygon
4. Use the edit tool to modify

#### Option C: Enter Coordinates

```
Bounding Box:
  Min Longitude: [-62.5    ]
  Max Longitude: [-62.0    ]
  Min Latitude:  [-4.0     ]
  Max Latitude:  [-3.5     ]
```

### Step 2: Configure Analysis

#### Site Name
```
Site Name: [Amazon Forest Reserve    ]
```

#### Temporal Periods

Select periods to analyze:

```
[ ] 1990s (1985-1999) - Landsat 5
[x] 2000s (2000-2012) - Landsat 5/7
[x] 2010s (2013-2020) - Landsat 8
[x] Present (2021-2024) - Landsat 8 + Sentinel-2
```

#### Spectral Indices

```
[x] NDVI - Vegetation greenness
[x] NBR - Burn/disturbance severity
[ ] NDWI - Water content
[ ] EVI - Enhanced vegetation
[ ] NDMI - Moisture stress
```

#### Reference Period

```
Reference Period: [1990s ▼]
  Compare all periods against this baseline
```

### Step 3: Advanced Options

Expand for additional settings:

```
▼ Advanced Options

Cloud Threshold: [20] %
  Higher values include more images but may have cloud artifacts

Buffer Distance: [0] meters
  Buffer around AOI boundary

Export Options:
  [ ] Export to Google Drive
  Export Scale: [30] meters
  Drive Folder: [VegChange]
```

### Step 4: Run Analysis

```
[🚀 Run Analysis]
```

Progress indicators show:
- Loading AOI geometry
- Creating composites for each period
- Calculating spectral indices
- Detecting changes
- Generating statistics

---

## Results Visualization

After analysis completes, results are displayed in tabs:

### Map Tab

Interactive map with layer controls:

```
Layers:
  [x] Present NDVI
  [ ] 1990s NDVI
  [x] Change Map (NDVI)
  [ ] Change Map (NBR)

Basemap:
  (•) Satellite
  ( ) Street
  ( ) Terrain
```

**Map Features:**
- Zoom/pan controls
- Layer opacity slider
- Legend for change classes
- Click for pixel values

### Statistics Tab

Summary statistics table:

```
Change Statistics: 1990s to Present (NDVI)
┌─────────────────┬──────────┬──────────┬─────────┐
│ Change Class    │ Pixels   │ Area (ha)│ Percent │
├─────────────────┼──────────┼──────────┼─────────┤
│ Strong Loss     │ 12,456   │ 1,121.0  │ 4.5%    │
│ Moderate Loss   │ 34,567   │ 3,111.0  │ 12.4%   │
│ Stable          │ 189,234  │ 17,031.1 │ 68.0%   │
│ Moderate Gain   │ 32,456   │ 2,921.0  │ 11.7%   │
│ Strong Gain     │ 9,456    │ 851.0    │ 3.4%    │
└─────────────────┴──────────┴──────────┴─────────┘
Total Area: 25,035.1 ha
```

### Charts Tab

Visual representations:

- **Bar Chart**: Area by change class
- **Pie Chart**: Percentage distribution
- **Time Series**: Index values over periods
- **Heatmap**: Change intensity

### Export Tab

Download options:

```
Export Results:

[📥 Download Statistics (CSV)]
[📥 Download Report (JSON)]
[📥 Download GeoTIFF]

Google Drive Export:
  [🚀 Start Export to Drive]
```

---

## Comparison Page

Side-by-side comparison of periods or indices.

### Usage

1. Select two periods or indices to compare
2. Use synchronized maps for visual comparison
3. Swipe or toggle between views

```
Left Panel:              Right Panel:
Period: [1990s ▼]        Period: [Present ▼]
Index:  [NDVI  ▼]        Index:  [NDVI    ▼]
```

---

## Time Series Page

Analyze temporal trends for specific locations.

### Point Selection

1. Click on map to select a point
2. Or enter coordinates manually

```
Coordinates:
  Longitude: [-62.25  ]
  Latitude:  [-3.75   ]
```

### Time Series Plot

Shows index values across all available dates:

```
NDVI Time Series at (-62.25, -3.75)

1.0 │     ○  ○
    │   ○ ○○ ○○○○    ○○
0.8 │  ○      ○   ○○    ○○○
    │                       ○○
0.6 │                         ○ ← Disturbance
    │                          ○○
0.4 │                            ○○○ ← Recovery
    │
0.2 │
    └────────────────────────────────
    1990    2000    2010    2020
```

### Trend Analysis

```
Trend Statistics:
  Mean NDVI: 0.72
  Trend: -0.08 per decade
  Max Change: -0.35 (2015)
  Recovery Rate: +0.12/year
```

---

## Settings Page

Configure dashboard preferences.

### Earth Engine Settings

```
Project ID: [your-project-id    ]
[Test Connection]

Status: ✓ Connected
```

### Display Settings

```
Default Basemap: [Satellite ▼]
Color Palette:   [RdYlGn    ▼]
Map Height:      [600      ] px
```

### Cache Settings

```
Enable Caching: [x]
Cache Location: [~/.vegchange/cache]
[Clear Cache]
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Run analysis |
| `Esc` | Cancel operation |
| `R` | Reset map view |
| `L` | Toggle layers panel |
| `F` | Toggle fullscreen map |

---

## Tips and Best Practices

### 1. Start with Preview

Before running full analysis:
- Use the preview mode for quick visualization
- Verify AOI is correctly loaded
- Check image availability for selected periods

### 2. Optimize Performance

- Start with small AOIs to test
- Use fewer periods for initial exploration
- Select only needed indices

### 3. Interpret Results Carefully

- Consider seasonal effects
- Validate with high-resolution imagery
- Use multiple indices for confirmation

### 4. Save Your Work

- Export statistics before closing
- Save configuration as YAML
- Download GeoTIFFs for GIS software

---

## Troubleshooting

### Dashboard Won't Start

```bash
# Check Streamlit installation
pip install streamlit --upgrade

# Check port availability
lsof -i :8501
```

### Map Not Loading

- Check internet connection
- Verify Earth Engine authentication
- Clear browser cache

### Analysis Timeout

- Reduce AOI size
- Increase cloud threshold
- Try single period/index first

### Export Fails

- Check Google Drive quota
- Verify Earth Engine permissions
- Try smaller export scale

---

## Screenshots

### Main Analysis Interface

```
┌─────────────────────────────────────────────────────────┐
│  🌿 Vegetation Change Intelligence Platform             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ Configuration   │  │                             │  │
│  │                 │  │         Map View            │  │
│  │ Site: Amazon    │  │                             │  │
│  │ Periods: [x][x] │  │    [Interactive Map]        │  │
│  │ Indices: [x][ ] │  │                             │  │
│  │                 │  │                             │  │
│  │ [Run Analysis]  │  │                             │  │
│  └─────────────────┘  └─────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Results: Map | Statistics | Charts | Export     │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```
