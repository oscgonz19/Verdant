"""
Input/Output module for vegetation change analysis.

Provides:
- AOI loading from multiple formats (KMZ, GeoJSON, Shapefile, etc.)
- Export to Google Drive, EE Assets, Cloud Storage
- Caching for repeated analyses
"""

from engine.io.aoi import (
    AOILoader,
    GeoPackageLoader,
    ShapefileLoader,
    GeoJSONLoader,
    KMZLoader,
    KMLLoader,
    LOADER_REGISTRY,
    register_loader,
    get_loader,
    load_aoi,
    kmz_to_geodataframe,
    validate_geometry,
    geodataframe_to_ee,
    aoi_to_ee_geometry,
    create_buffered_aoi,
    get_aoi_bounds,
    get_aoi_centroid,
    get_aoi_area,
)

from engine.io.exporters import (
    ExportConfig,
    Exporter,
    DriveExporter,
    AssetExporter,
    CloudStorageExporter,
    export_to_drive,
    export_composite,
    export_change_map,
    export_all_composites,
    export_all_changes,
    get_task_status,
    monitor_tasks,
    wait_for_tasks,
)

from engine.io.cache import (
    AssetCache,
    LocalCache,
    CachedAnalysis,
    setup_cache,
)

__all__ = [
    # AOI Loaders
    "AOILoader",
    "GeoPackageLoader",
    "ShapefileLoader",
    "GeoJSONLoader",
    "KMZLoader",
    "KMLLoader",
    "LOADER_REGISTRY",
    "register_loader",
    "get_loader",
    # AOI Functions
    "load_aoi",
    "kmz_to_geodataframe",
    "validate_geometry",
    "geodataframe_to_ee",
    "aoi_to_ee_geometry",
    "create_buffered_aoi",
    "get_aoi_bounds",
    "get_aoi_centroid",
    "get_aoi_area",
    # Exporters
    "ExportConfig",
    "Exporter",
    "DriveExporter",
    "AssetExporter",
    "CloudStorageExporter",
    "export_to_drive",
    "export_composite",
    "export_change_map",
    "export_all_composites",
    "export_all_changes",
    "get_task_status",
    "monitor_tasks",
    "wait_for_tasks",
    # Cache
    "AssetCache",
    "LocalCache",
    "CachedAnalysis",
    "setup_cache",
]
