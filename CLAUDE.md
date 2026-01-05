# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Vegetation Change Intelligence Platform is a Google Earth Engine-based satellite analysis system for detecting and quantifying vegetation change over multi-decadal time periods. It processes Landsat 5/7/8 and Sentinel-2 imagery to identify areas of vegetation loss, recovery, and stability.

## Development Commands

### Installation
```bash
# Install core package
pip install -e .

# Install with all dependencies (dev + app)
pip install -e ".[all]"

# Or use make
make install       # Core only
make dev-install   # Everything
```

### Testing and Linting
```bash
# Run tests with coverage
pytest tests/ -v --cov=veg_change_engine
# Or: make test

# Lint code
ruff check veg_change_engine/ cli/ app/
mypy veg_change_engine/
# Or: make lint

# Format code
black veg_change_engine/ cli/ app/
isort veg_change_engine/ cli/ app/
# Or: make format
```

### Running the Application
```bash
# Run Streamlit dashboard
streamlit run app/Home.py
# Or: make app

# Run CLI demo
python -m cli.main run-demo
# Or: make demo

# CLI commands
veg-change analyze --aoi area.geojson --periods 1990s,present --indices ndvi,nbr
veg-change preview --aoi area.geojson --period present --index ndvi
veg-change periods  # List available periods
veg-change indices  # List available indices
```

### Earth Engine Authentication
```bash
earthengine authenticate
# Or: make auth
```

## Architecture

### Core Modules (`veg_change_engine/core/`)

**composites.py** - Temporal composite generation
- `apply_cloud_mask_landsat()`: QA-based cloud masking for Landsat Collection 2
- `apply_cloud_mask_sentinel2()`: QA60-based cloud masking for Sentinel-2
- `harmonize_bands()`: Normalizes different sensors to common band names (blue, green, red, nir, swir1, swir2)
- `create_landsat_composite()`: Creates median composite from single Landsat sensor
- `create_sentinel_composite()`: Creates median composite from Sentinel-2
- `create_fused_composite()`: Fuses multiple sensors (e.g., Landsat 8 + Sentinel-2 for "present" period)
- `create_all_period_composites()`: Orchestrates composite creation for all periods

**indices.py** - Spectral index calculation
- Supports: NDVI, NBR, NDWI, EVI, NDMI
- `add_ndvi()`, `add_nbr()`, etc.: Add individual indices to ee.Image
- `add_all_indices()`: Batch add multiple indices
- `calculate_delta_indices()`: Compute change between two periods (e.g., dNDVI = NDVI_present - NDVI_1990s)

**change.py** - Change detection and classification
- `classify_change()`: Classifies delta indices into 5 categories (strong loss, moderate loss, stable, moderate gain, strong gain)
- `analyze_period_change()`: Compares two periods for a single index
- `create_change_analysis()`: Creates all period-to-period comparisons
- `generate_change_statistics()`: Calculates pixel counts and area statistics for each change class

### IO Modules (`veg_change_engine/io/`)

**aoi.py** - Area of interest loading
- Supports: GeoPackage (.gpkg), GeoJSON, Shapefile, KMZ, KML
- `load_aoi()`: Load any supported format to GeoDataFrame
- `aoi_to_ee_geometry()`: Convert GeoDataFrame to ee.Geometry
- `create_buffered_aoi()`: Apply buffer around AOI
- `get_aoi_centroid()`, `get_aoi_area()`: Metadata extraction

**exporters.py** - Export to Google Drive and EE Assets
- `export_to_drive()`: Core GeoTIFF export function
- `export_composite()`: Export single temporal composite
- `export_change_map()`: Export single change detection map
- `export_all_composites()`, `export_all_changes()`: Batch export functions
- Uses `ExportConfig` dataclass for configuration

**cache.py** - Data persistence to avoid repeated API calls
- `AssetCache`: Saves processed composites as EE Assets for reuse
- Significantly reduces API consumption and speeds up repeated analyses
- Key methods: `get_composite()`, `save_composite()`, `exists()`
- Cache keys generated from AOI geometry + period + indices hash

### Configuration (`veg_change_engine/config.py`)

**TEMPORAL_PERIODS** - Defines 4 temporal periods:
- `1990s`: 1985-1999 (Landsat 5 TM)
- `2000s`: 2000-2012 (Landsat 5/7)
- `2010s`: 2013-2020 (Landsat 8 OLI)
- `present`: 2021-2024 (Landsat 8 + Sentinel-2)

**BAND_MAPPINGS** - Sensor-specific band names and scaling factors
- Maps sensor-specific names to common names (e.g., SR_B4 -> nir for Landsat 8)
- Includes scale_factor and offset for surface reflectance conversion

**CHANGE_THRESHOLDS** - Classification thresholds for dNDVI and dNBR
- Strong loss: < -0.15 (dNDVI), < -0.20 (dNBR)
- Moderate loss: -0.15 to -0.05 (dNDVI)
- Stable: -0.05 to +0.05 (dNDVI)
- Moderate gain: +0.05 to +0.15 (dNDVI)
- Strong gain: > +0.15 (dNDVI)

**VegChangeConfig** - Dataclass for analysis configuration
- Can be loaded from/saved to YAML
- Controls periods, indices, cloud threshold, export settings

### Pipeline Orchestration (`veg_change_engine/pipeline.py`)

**analyze_vegetation_change()** - Main programmatic entry point
- Takes ee.Geometry and returns composites + changes + statistics
- 4 steps: composites -> indices -> change detection -> statistics

**run_full_analysis()** - Complete workflow from file
- Loads AOI from file path, runs analysis, optionally exports to Drive
- Adds metadata (centroid, area, etc.)
- Primary function used by CLI and dashboard

**quick_preview()** - Fast preview for testing
- Single period, single index composite generation

## Data Flow

1. **AOI Loading**: File (GeoJSON/KMZ/etc.) -> GeoDataFrame -> ee.Geometry
2. **Composite Creation**: ee.Geometry + Period -> Image Collection -> Cloud masking -> Band harmonization -> Median composite
3. **Index Calculation**: Composite -> Add spectral indices (NDVI, NBR, etc.)
4. **Change Detection**: Composite_t1 + Composite_t2 -> Delta indices -> Classification (1-5)
5. **Export**: ee.Image -> Export task -> Google Drive GeoTIFF

## Key Patterns

### Multi-Sensor Fusion
For the "present" period, `create_fused_composite()` merges Landsat 8 and Sentinel-2 by:
1. Creating separate composites for each sensor
2. Harmonizing bands to common names
3. Merging into single ImageCollection
4. Computing median across all images

### Cloud Masking
Uses QA bands with bitwise operations:
- Landsat: QA_PIXEL band (bits 1,3,4,5)
- Sentinel-2: QA60 band (bits 10,11)

### Change Classification
Delta indices are classified using `ee.Image.where()` chaining:
```python
# Example pattern from change.py
change_class = (
    ee.Image(3)  # Start with stable
    .where(delta.lt(strong_loss), 1)
    .where(delta.gte(strong_loss).And(delta.lt(moderate_loss)), 2)
    .where(delta.gt(moderate_gain).And(delta.lte(strong_gain)), 4)
    .where(delta.gt(strong_gain), 5)
)
```

## Important Notes

### Earth Engine Initialization
The platform expects Earth Engine to be initialized before use:
```python
import ee
ee.Initialize()
```

The `veg_change_engine/ee_init.py` module can handle this automatically.

### Caching Strategy
For repeated analyses on the same AOI:
1. Set up AssetCache with your EE asset folder
2. First run: composites are computed and saved to assets
3. Subsequent runs: composites load from cache (much faster)
4. Cache invalidation: Change AOI geometry, period, or indices list

### Export Task Management
Export functions return `ee.batch.Export.Task` objects but don't wait for completion:
- Tasks must be monitored via Earth Engine Task Manager
- Check status with `task.status()`
- Results appear in Google Drive after task completes (may take minutes to hours)

### Code Style
- Line length: 100 characters (enforced by black/ruff)
- Type hints encouraged (mypy configured but imports ignored)
- Docstrings: Google style with Args/Returns sections
- Import order: stdlib -> third-party -> local (enforced by isort)

### Testing
- Tests in `tests/` directory
- Run with coverage: `pytest --cov=veg_change_engine`
- Focus tests on core modules (composites, indices, change)
- Mock Earth Engine calls for unit tests

## Common Pitfalls

1. **Not waiting for .getInfo()**: Earth Engine operations are lazy. Use `.getInfo()` to force computation (but avoid in loops - very slow).

2. **Large AOI exports**: Keep export_scale at 30m for Landsat, use smaller AOIs or increase scale for large regions.

3. **Empty composites**: If cloud_threshold is too restrictive, no images pass filtering. Increase threshold or check data availability for that period/location.

4. **Sensor availability**: Landsat 5 ends ~2013, Landsat 8 starts 2013, Sentinel-2 starts 2015. The period definitions in config.py account for this.

5. **Band name confusion**: Always use harmonized names (blue, green, red, nir, swir1, swir2) after calling harmonize_bands(). Raw sensor band names vary (SR_B4 vs B8 vs SR_B4).
