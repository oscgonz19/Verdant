"""
Area of Interest (AOI) loading and processing module.

Note:
    This module provides backward-compatible re-exports from engine/io/aoi/.
    For new code, prefer importing directly from engine.io.aoi.
"""

# Re-export everything from engine.io.aoi
from engine.io.aoi import (
    # Loaders
    AOILoader,
    GeoPackageLoader,
    ShapefileLoader,
    GeoJSONLoader,
    KMZLoader,
    KMLLoader,
    LOADER_REGISTRY,
    register_loader,
    get_loader,
    # Core functions
    load_aoi,
    kmz_to_geodataframe,
    validate_geometry,
    # Geometry functions
    geodataframe_to_ee,
    aoi_to_ee_geometry,
    create_buffered_aoi,
    get_aoi_bounds,
    get_aoi_centroid,
    get_aoi_area,
)

__all__ = [
    # Loaders
    "AOILoader",
    "GeoPackageLoader",
    "ShapefileLoader",
    "GeoJSONLoader",
    "KMZLoader",
    "KMLLoader",
    "LOADER_REGISTRY",
    "register_loader",
    "get_loader",
    # Core functions
    "load_aoi",
    "kmz_to_geodataframe",
    "validate_geometry",
    # Geometry functions
    "geodataframe_to_ee",
    "aoi_to_ee_geometry",
    "create_buffered_aoi",
    "get_aoi_bounds",
    "get_aoi_centroid",
    "get_aoi_area",
]
