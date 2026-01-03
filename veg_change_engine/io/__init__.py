"""
Input/Output module for vegetation change analysis.

- aoi: Area of Interest loading (KMZ, GeoJSON, Shapefile)
- exporters: Export to Google Drive, local GeoTIFF
- cache: Data persistence to avoid repeated API consumption
"""

from veg_change_engine.io.aoi import (
    kmz_to_geodataframe,
    geodataframe_to_ee,
    create_buffered_aoi,
    load_aoi,
    validate_geometry,
)

from veg_change_engine.io.exporters import (
    export_to_drive,
    export_composite,
    export_change_map,
    ExportConfig,
)

from veg_change_engine.io.cache import (
    AssetCache,
    LocalCache,
    CachedAnalysis,
    setup_cache,
)

__all__ = [
    # AOI
    "kmz_to_geodataframe",
    "geodataframe_to_ee",
    "create_buffered_aoi",
    "load_aoi",
    "validate_geometry",
    # Exporters
    "export_to_drive",
    "export_composite",
    "export_change_map",
    "ExportConfig",
    # Cache
    "AssetCache",
    "LocalCache",
    "CachedAnalysis",
    "setup_cache",
]
