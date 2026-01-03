"""
Area of Interest (AOI) loading and processing module.

Supports multiple input formats:
- KMZ/KML files (Google Earth)
- GeoJSON
- Shapefile
- GeoPackage

Follows SOLID principles:
- Single Responsibility: Each function handles one format/operation
- Open/Closed: New formats can be added via the loader registry
- Interface Segregation: Separate interfaces for different operations
"""

from typing import Dict, Optional, Union, Callable
from pathlib import Path
from abc import ABC, abstractmethod
import json
import zipfile
import tempfile

import geopandas as gpd
from shapely.geometry import shape, mapping
import ee


# =============================================================================
# ABSTRACT LOADER (Dependency Inversion)
# =============================================================================

class AOILoader(ABC):
    """Abstract base class for AOI loaders."""

    @abstractmethod
    def load(self, filepath: str) -> gpd.GeoDataFrame:
        """Load AOI from file."""
        pass

    @abstractmethod
    def supports(self, filepath: str) -> bool:
        """Check if this loader supports the file format."""
        pass


# =============================================================================
# CONCRETE LOADERS
# =============================================================================

class GeoPackageLoader(AOILoader):
    """Load AOI from GeoPackage format."""

    def supports(self, filepath: str) -> bool:
        return filepath.lower().endswith(".gpkg")

    def load(self, filepath: str) -> gpd.GeoDataFrame:
        return gpd.read_file(filepath)


class ShapefileLoader(AOILoader):
    """Load AOI from Shapefile format."""

    def supports(self, filepath: str) -> bool:
        return filepath.lower().endswith(".shp")

    def load(self, filepath: str) -> gpd.GeoDataFrame:
        return gpd.read_file(filepath)


class GeoJSONLoader(AOILoader):
    """Load AOI from GeoJSON format."""

    def supports(self, filepath: str) -> bool:
        ext = filepath.lower()
        return ext.endswith(".geojson") or ext.endswith(".json")

    def load(self, filepath: str) -> gpd.GeoDataFrame:
        return gpd.read_file(filepath)


class KMZLoader(AOILoader):
    """
    Load AOI from KMZ (compressed KML) format.

    Extracts KML from the KMZ archive and parses it.
    """

    def supports(self, filepath: str) -> bool:
        return filepath.lower().endswith(".kmz")

    def load(self, filepath: str) -> gpd.GeoDataFrame:
        return kmz_to_geodataframe(filepath)


class KMLLoader(AOILoader):
    """Load AOI from KML format."""

    def supports(self, filepath: str) -> bool:
        return filepath.lower().endswith(".kml")

    def load(self, filepath: str) -> gpd.GeoDataFrame:
        # Enable KML driver
        gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
        return gpd.read_file(filepath, driver="KML")


# =============================================================================
# LOADER REGISTRY
# =============================================================================

LOADER_REGISTRY: list[AOILoader] = [
    GeoPackageLoader(),
    ShapefileLoader(),
    GeoJSONLoader(),
    KMZLoader(),
    KMLLoader(),
]


def register_loader(loader: AOILoader) -> None:
    """Register a custom AOI loader."""
    LOADER_REGISTRY.append(loader)


def get_loader(filepath: str) -> AOILoader:
    """Get appropriate loader for file format."""
    for loader in LOADER_REGISTRY:
        if loader.supports(filepath):
            return loader
    raise ValueError(f"No loader found for file: {filepath}")


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def kmz_to_geodataframe(kmz_path: str) -> gpd.GeoDataFrame:
    """
    Extract and parse KMZ file to GeoDataFrame.

    KMZ files are ZIP archives containing a doc.kml file.

    Args:
        kmz_path: Path to KMZ file

    Returns:
        GeoDataFrame with geometries from the KMZ
    """
    # Enable KML driver
    gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract KMZ (it's a ZIP file)
        with zipfile.ZipFile(kmz_path, "r") as zf:
            zf.extractall(tmpdir)

        # Find the KML file
        kml_path = Path(tmpdir) / "doc.kml"
        if not kml_path.exists():
            # Try to find any KML file
            kml_files = list(Path(tmpdir).glob("*.kml"))
            if not kml_files:
                raise ValueError(f"No KML file found in KMZ: {kmz_path}")
            kml_path = kml_files[0]

        # Read KML
        gdf = gpd.read_file(str(kml_path), driver="KML")

    return gdf


def load_aoi(filepath: str) -> gpd.GeoDataFrame:
    """
    Load AOI from any supported format.

    Automatically detects format and uses appropriate loader.

    Args:
        filepath: Path to AOI file

    Returns:
        GeoDataFrame with AOI geometry

    Raises:
        ValueError: If format is not supported
    """
    loader = get_loader(filepath)
    gdf = loader.load(filepath)

    # Ensure CRS is set (default to WGS84 if missing)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)

    return gdf


def validate_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Validate and fix geometries.

    - Fixes invalid geometries with buffer(0)
    - Removes empty geometries
    - Ensures consistent geometry types

    Args:
        gdf: Input GeoDataFrame

    Returns:
        Cleaned GeoDataFrame
    """
    gdf = gdf.copy()

    # Fix invalid geometries
    gdf["geometry"] = gdf["geometry"].apply(
        lambda g: g.buffer(0) if g is not None and not g.is_valid else g
    )

    # Remove empty geometries
    gdf = gdf[~gdf["geometry"].is_empty]
    gdf = gdf[gdf["geometry"].notna()]

    return gdf


def geodataframe_to_ee(
    gdf: gpd.GeoDataFrame,
    simplify_tolerance: Optional[float] = None,
) -> ee.FeatureCollection:
    """
    Convert GeoDataFrame to Earth Engine FeatureCollection.

    Args:
        gdf: Input GeoDataFrame
        simplify_tolerance: Optional geometry simplification tolerance

    Returns:
        ee.FeatureCollection
    """
    # Ensure WGS84 for GEE
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # Simplify if requested
    if simplify_tolerance:
        gdf = gdf.copy()
        gdf["geometry"] = gdf["geometry"].simplify(simplify_tolerance)

    # Convert to GeoJSON
    geojson = json.loads(gdf.to_json())

    # Create EE features
    features = []
    for feature in geojson["features"]:
        # Convert geometry
        geom = ee.Geometry(feature["geometry"])

        # Convert properties (handle None values)
        props = {}
        for key, value in feature.get("properties", {}).items():
            if value is not None:
                props[key] = value

        ee_feature = ee.Feature(geom, props)
        features.append(ee_feature)

    return ee.FeatureCollection(features)


def create_buffered_aoi(
    gdf: gpd.GeoDataFrame,
    buffer_distance: float,
    cap_style: int = 1,
) -> gpd.GeoDataFrame:
    """
    Create buffered AOI for analysis extent.

    Args:
        gdf: Input GeoDataFrame
        buffer_distance: Buffer distance in meters
        cap_style: Buffer cap style (1=round, 2=flat, 3=square)

    Returns:
        Buffered GeoDataFrame
    """
    # Convert to projected CRS for buffering
    original_crs = gdf.crs

    # Use UTM for accurate buffering
    centroid = gdf.unary_union.centroid
    utm_zone = int((centroid.x + 180) / 6) + 1
    hemisphere = "north" if centroid.y >= 0 else "south"
    utm_crs = f"+proj=utm +zone={utm_zone} +{hemisphere} +datum=WGS84"

    gdf_utm = gdf.to_crs(utm_crs)

    # Apply buffer
    gdf_buffered = gdf_utm.copy()
    gdf_buffered["geometry"] = gdf_utm.geometry.buffer(
        buffer_distance, cap_style=cap_style
    )

    # Convert back to original CRS
    return gdf_buffered.to_crs(original_crs)


def aoi_to_ee_geometry(gdf: gpd.GeoDataFrame) -> ee.Geometry:
    """
    Convert AOI GeoDataFrame to single ee.Geometry.

    Dissolves all features into one geometry.

    Args:
        gdf: Input GeoDataFrame

    Returns:
        ee.Geometry
    """
    # Ensure WGS84
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # Dissolve to single geometry
    dissolved = gdf.unary_union

    # Convert to GeoJSON dict
    geojson = mapping(dissolved)

    return ee.Geometry(geojson)


def get_aoi_bounds(gdf: gpd.GeoDataFrame) -> Dict:
    """
    Get bounding box of AOI.

    Args:
        gdf: Input GeoDataFrame

    Returns:
        Dictionary with minx, miny, maxx, maxy
    """
    bounds = gdf.total_bounds
    return {
        "minx": bounds[0],
        "miny": bounds[1],
        "maxx": bounds[2],
        "maxy": bounds[3],
    }


def get_aoi_centroid(gdf: gpd.GeoDataFrame) -> Dict:
    """
    Get centroid of AOI.

    Args:
        gdf: Input GeoDataFrame

    Returns:
        Dictionary with lat, lon
    """
    centroid = gdf.unary_union.centroid
    return {
        "lon": centroid.x,
        "lat": centroid.y,
    }


def get_aoi_area(gdf: gpd.GeoDataFrame) -> float:
    """
    Calculate area of AOI in hectares.

    Args:
        gdf: Input GeoDataFrame

    Returns:
        Area in hectares
    """
    # Project to equal-area CRS
    gdf_projected = gdf.to_crs("+proj=eck4")
    area_m2 = gdf_projected.unary_union.area
    return area_m2 / 10000  # Convert to hectares
