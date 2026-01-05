"""
Area of Interest (AOI) loading and processing module.

Supports multiple input formats:
- KMZ/KML files (Google Earth)
- GeoJSON
- Shapefile
- GeoPackage
"""

from engine.io.aoi.loaders import (
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
)

from engine.io.aoi.geometry import (
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
