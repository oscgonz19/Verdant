"""
Input/Output module for vegetation change analysis.

Note:
    This module provides backward-compatible re-exports from engine/io/.
    For new code, prefer importing directly from engine.io.
"""

# Re-export from engine.io modules
from engine.io.aoi import (
    kmz_to_geodataframe,
    geodataframe_to_ee,
    aoi_to_ee_geometry,
    create_buffered_aoi,
    load_aoi,
    validate_geometry,
    get_aoi_bounds,
    get_aoi_centroid,
    get_aoi_area,
)

from engine.io.exporters import (
    export_to_drive,
    export_composite,
    export_change_map,
    export_all_composites,
    export_all_changes,
    ExportConfig,
    Exporter,
    DriveExporter,
    AssetExporter,
    CloudStorageExporter,
)

from engine.io.cache import (
    AssetCache,
    LocalCache,
    CachedAnalysis,
    setup_cache,
)

__all__ = [
    # AOI
    "kmz_to_geodataframe",
    "geodataframe_to_ee",
    "aoi_to_ee_geometry",
    "create_buffered_aoi",
    "load_aoi",
    "validate_geometry",
    "get_aoi_bounds",
    "get_aoi_centroid",
    "get_aoi_area",
    # Exporters
    "export_to_drive",
    "export_composite",
    "export_change_map",
    "export_all_composites",
    "export_all_changes",
    "ExportConfig",
    "Exporter",
    "DriveExporter",
    "AssetExporter",
    "CloudStorageExporter",
    # Cache
    "AssetCache",
    "LocalCache",
    "CachedAnalysis",
    "setup_cache",
]
