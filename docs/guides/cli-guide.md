# CLI User Guide

Complete guide to using the Vegetation Change Intelligence Platform command-line interface.

## Overview

The CLI provides a powerful interface for running vegetation change analyses from the terminal. It's ideal for:

- Batch processing multiple AOIs
- Automation and scripting
- Integration with other tools
- Quick previews and exploration

## Installation

The CLI is installed automatically with the package:

```bash
pip install -e .

# Verify installation
veg-change --help
```

## Commands

### Main Commands

```
veg-change [OPTIONS] COMMAND [ARGS]

Commands:
  analyze   Run vegetation change analysis
  preview   Generate quick preview
  periods   List available temporal periods
  indices   List available spectral indices
  export    Export results to Google Drive
  status    Check Earth Engine task status
```

---

## analyze

Run a complete vegetation change analysis.

### Basic Usage

```bash
# Minimal example
veg-change analyze --aoi area.geojson

# Full analysis with options
veg-change analyze \
  --aoi area.geojson \
  --name "Amazon Site 1" \
  --periods 1990s,present \
  --indices ndvi,nbr \
  --reference 1990s \
  --output results/
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--aoi` | `-a` | PATH | Required | Path to AOI file |
| `--name` | `-n` | TEXT | "Analysis" | Site name for outputs |
| `--periods` | `-p` | TEXT | "1990s,present" | Comma-separated periods |
| `--indices` | `-i` | TEXT | "ndvi" | Comma-separated indices |
| `--reference` | `-r` | TEXT | "1990s" | Reference period for change |
| `--output` | `-o` | PATH | "./output" | Output directory |
| `--cloud-threshold` | `-c` | FLOAT | 20.0 | Max cloud cover % |
| `--buffer` | `-b` | FLOAT | 0.0 | Buffer distance in meters |
| `--export-drive` | | FLAG | False | Export to Google Drive |
| `--export-scale` | | INT | 30 | Export resolution (meters) |
| `--verbose` | `-v` | FLAG | False | Show detailed progress |
| `--quiet` | `-q` | FLAG | False | Suppress output |

### Examples

```bash
# Analyze with multiple periods
veg-change analyze \
  --aoi forest_reserve.gpkg \
  --periods 1990s,2000s,2010s,present \
  --indices ndvi,nbr

# High-resolution export for small area
veg-change analyze \
  --aoi small_farm.geojson \
  --export-drive \
  --export-scale 10

# Batch processing with script
for aoi in sites/*.geojson; do
  name=$(basename "$aoi" .geojson)
  veg-change analyze --aoi "$aoi" --name "$name" --output "results/$name"
done
```

### Output Files

```
output/
├── composites/
│   ├── 1990s_composite.json      # Metadata
│   ├── present_composite.json
├── changes/
│   ├── 1990s_to_present_ndvi.json
│   └── 1990s_to_present_nbr.json
├── statistics/
│   └── change_statistics.json
└── analysis_report.json          # Full report
```

---

## preview

Generate a quick preview for a single period and index.

### Usage

```bash
veg-change preview \
  --aoi area.geojson \
  --period present \
  --index ndvi
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--aoi` | `-a` | PATH | Required | Path to AOI file |
| `--period` | `-p` | TEXT | "present" | Temporal period |
| `--index` | `-i` | TEXT | "ndvi" | Spectral index |
| `--output` | `-o` | PATH | None | Save preview image |

### Output

Returns a tile URL for visualization and optionally saves a PNG preview.

---

## periods

List available temporal periods with their date ranges and sensors.

### Usage

```bash
veg-change periods
```

### Output

```
Available Temporal Periods:
===========================

  1990s (1985-01-01 to 1999-12-31)
    Sensors: Landsat 5 TM
    Description: Pre-2000 baseline

  2000s (2000-01-01 to 2012-12-31)
    Sensors: Landsat 5 TM, Landsat 7 ETM+
    Description: Early 2000s era

  2010s (2013-01-01 to 2020-12-31)
    Sensors: Landsat 8 OLI
    Description: Landsat 8 era

  present (2021-01-01 to 2024-12-31)
    Sensors: Landsat 8 OLI, Sentinel-2 MSI
    Description: Current conditions (fused)
```

---

## indices

List available spectral indices with formulas.

### Usage

```bash
veg-change indices

# Show detailed information
veg-change indices --verbose
```

### Output

```
Available Spectral Indices:
===========================

  ndvi - Normalized Difference Vegetation Index
    Formula: (NIR - Red) / (NIR + Red)
    Range: -1.0 to 1.0

  nbr - Normalized Burn Ratio
    Formula: (NIR - SWIR2) / (NIR + SWIR2)
    Range: -1.0 to 1.0

  ndwi - Normalized Difference Water Index
    Formula: (Green - NIR) / (Green + NIR)
    Range: -1.0 to 1.0

  evi - Enhanced Vegetation Index
    Formula: 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)
    Range: -0.2 to 1.0

  ndmi - Normalized Difference Moisture Index
    Formula: (NIR - SWIR1) / (NIR + SWIR1)
    Range: -1.0 to 1.0
```

---

## export

Export results to Google Drive.

### Usage

```bash
# Export from previous analysis
veg-change export \
  --job-id abc12345 \
  --folder "VegChange/MyAnalysis"

# Export specific layers
veg-change export \
  --job-id abc12345 \
  --layers composites,changes \
  --scale 30
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--job-id` | TEXT | Required | Analysis job ID |
| `--folder` | TEXT | "VegChange" | Drive folder name |
| `--layers` | TEXT | "all" | Layers to export |
| `--scale` | INT | 30 | Resolution in meters |

---

## status

Check Earth Engine task status.

### Usage

```bash
# Check all recent tasks
veg-change status

# Check specific task
veg-change status --task-id TASK123

# Watch tasks in real-time
veg-change status --watch
```

---

## Configuration File

Create a `.vegchange.yaml` file for default options:

```yaml
# ~/.vegchange.yaml or ./.vegchange.yaml

defaults:
  periods:
    - 1990s
    - present
  indices:
    - ndvi
    - nbr
  cloud_threshold: 20.0
  export_scale: 30

output:
  directory: ./results
  export_to_drive: false
  drive_folder: VegChange

thresholds:
  ndvi:
    strong_loss: -0.15
    moderate_loss: -0.05
    moderate_gain: 0.05
    strong_gain: 0.15
```

Load with:

```bash
veg-change analyze --aoi area.geojson --config .vegchange.yaml
```

---

## Environment Variables

```bash
# Earth Engine project
export EE_PROJECT="your-project-id"

# Default output directory
export VEGCHANGE_OUTPUT="./results"

# Verbosity level (0-2)
export VEGCHANGE_VERBOSITY=1
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | File not found |
| 4 | Earth Engine error |
| 5 | Export failed |

---

## Scripting Examples

### Batch Analysis

```bash
#!/bin/bash
# analyze_all.sh

AOI_DIR="./aois"
OUTPUT_DIR="./results"
PERIODS="1990s,2010s,present"
INDICES="ndvi,nbr"

for aoi in "$AOI_DIR"/*.geojson; do
    name=$(basename "$aoi" .geojson)
    echo "Processing: $name"

    veg-change analyze \
        --aoi "$aoi" \
        --name "$name" \
        --periods "$PERIODS" \
        --indices "$INDICES" \
        --output "$OUTPUT_DIR/$name" \
        --quiet

    if [ $? -eq 0 ]; then
        echo "  Success"
    else
        echo "  Failed"
    fi
done
```

### JSON Output Processing

```bash
# Get statistics as JSON
veg-change analyze --aoi area.geojson --output-format json > results.json

# Parse with jq
jq '.statistics.area_by_class' results.json
```

### Integration with Python

```python
import subprocess
import json

def run_analysis(aoi_path, periods):
    result = subprocess.run(
        ['veg-change', 'analyze',
         '--aoi', aoi_path,
         '--periods', ','.join(periods),
         '--output-format', 'json'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        raise Exception(result.stderr)
```

---

## Troubleshooting

### Common Issues

**1. "Earth Engine not authenticated"**
```bash
earthengine authenticate
```

**2. "AOI file not found"**
- Check file path is correct
- Ensure file format is supported (.geojson, .gpkg, .kml, .kmz, .shp)

**3. "No images found for period"**
- Check if AOI is within sensor coverage
- Try increasing cloud threshold
- Verify period dates match sensor availability

**4. "Export task failed"**
- Check Google Drive quota
- Reduce export scale for large areas
- Verify Earth Engine project permissions

### Debug Mode

```bash
# Enable debug output
veg-change analyze --aoi area.geojson --debug

# Check Earth Engine queries
veg-change analyze --aoi area.geojson --dry-run
```
