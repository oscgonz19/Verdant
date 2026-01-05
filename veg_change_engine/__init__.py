"""
Vegetation Change Intelligence Platform

A Google Earth Engine-based satellite analysis platform for detecting
and quantifying vegetation change over multi-decadal time periods.

Features:
- Multi-sensor fusion (Landsat 5/7/8, Sentinel-2)
- Automated cloud masking
- Spectral indices (NDVI, NBR)
- Temporal composites (median aggregation)
- Change detection and classification
- Export to GeoTIFF/Drive

Example:
    >>> import ee
    >>> ee.Initialize()
    >>> from veg_change_engine import analyze_vegetation_change
    >>> results = analyze_vegetation_change(aoi, periods=['1990s', '2000s', '2010s', 'present'])

Note:
    This module provides backward-compatible re-exports from the new
    modular architecture. For new code, prefer importing directly from
    engine/ and services/ packages.
"""

__version__ = "1.0.0"
__author__ = "Oscar Gonzalez"

# =============================================================================
# Re-exports from engine/ (new modular structure)
# =============================================================================

# Core analysis functions - Composites
from engine.composites import (
    create_landsat_composite,
    create_sentinel_composite,
    create_fused_composite,
    create_all_period_composites,
)

# Core analysis functions - Indices
from engine.indices import (
    add_ndvi,
    add_nbr,
    add_all_indices,
    calculate_delta_indices,
)

# Core analysis functions - Change detection
from engine.change import (
    classify_change,
    analyze_period_change,
    create_change_analysis,
    generate_change_statistics,
)

# IO functions - AOI
from engine.io.aoi import (
    kmz_to_geodataframe,
    geodataframe_to_ee,
    create_buffered_aoi,
    load_aoi,
)

# IO functions - Exporters
from engine.io.exporters import (
    export_to_drive,
    export_composite,
    export_change_map,
)

# Configuration
from engine.config import (
    VegChangeConfig,
    DEFAULT_CONFIG,
    TEMPORAL_PERIODS,
    CHANGE_THRESHOLDS,
)

# =============================================================================
# Re-exports from services/ (orchestration layer)
# =============================================================================

from services.change_orchestrator import (
    analyze_vegetation_change,
    run_full_analysis,
)

# =============================================================================
# Local modules (not migrated)
# =============================================================================

# Visualization (stays in veg_change_engine)
from veg_change_engine.viz.maps import (
    create_folium_map,
    add_composite_layer,
    add_change_layer,
)

from veg_change_engine.viz.colors import (
    NDVI_VIS_PARAMS,
    NBR_VIS_PARAMS,
    CHANGE_VIS_PARAMS,
    RGB_VIS_PARAMS,
)

__all__ = [
    # Version
    "__version__",
    # Composites
    "create_landsat_composite",
    "create_sentinel_composite",
    "create_fused_composite",
    "create_all_period_composites",
    # Indices
    "add_ndvi",
    "add_nbr",
    "add_all_indices",
    "calculate_delta_indices",
    # Change detection
    "classify_change",
    "analyze_period_change",
    "create_change_analysis",
    "generate_change_statistics",
    # IO
    "kmz_to_geodataframe",
    "geodataframe_to_ee",
    "create_buffered_aoi",
    "load_aoi",
    "export_to_drive",
    "export_composite",
    "export_change_map",
    # Visualization
    "create_folium_map",
    "add_composite_layer",
    "add_change_layer",
    "NDVI_VIS_PARAMS",
    "NBR_VIS_PARAMS",
    "CHANGE_VIS_PARAMS",
    "RGB_VIS_PARAMS",
    # Configuration
    "VegChangeConfig",
    "DEFAULT_CONFIG",
    "TEMPORAL_PERIODS",
    "CHANGE_THRESHOLDS",
    # Pipeline
    "analyze_vegetation_change",
    "run_full_analysis",
]
