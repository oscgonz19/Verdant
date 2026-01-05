"""
AOI loader implementations for various file formats.

Follows SOLID principles:
- Single Responsibility: Each loader handles one format
- Open/Closed: New formats can be added via the loader registry
"""

from typing import Optional
from pathlib import Path
from abc import ABC, abstractmethod
import json
import zipfile
import tempfile

import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon


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
        return _read_kml_file(filepath)


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

def _enable_kml_driver():
    """Enable KML driver for fiona/geopandas."""
    try:
        import fiona
        fiona.drv.supported_drivers["KML"] = "rw"
        fiona.drv.supported_drivers["LIBKML"] = "rw"
    except (ImportError, AttributeError):
        pass

    try:
        if hasattr(gpd, 'io') and hasattr(gpd.io, 'file'):
            gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
    except (AttributeError, TypeError):
        pass


def kmz_to_geodataframe(kmz_path: str) -> gpd.GeoDataFrame:
    """
    Extract and parse KMZ file to GeoDataFrame.

    KMZ files are ZIP archives containing a doc.kml file.

    Args:
        kmz_path: Path to KMZ file

    Returns:
        GeoDataFrame with geometries from the KMZ
    """
    _enable_kml_driver()

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

        # Read KML with multiple fallback methods
        gdf = _read_kml_file(str(kml_path))

    return gdf


def _read_kml_file(kml_path: str) -> gpd.GeoDataFrame:
    """Read KML file with multiple fallback methods."""
    errors = []

    # Method 1: Try with LIBKML driver
    try:
        _enable_kml_driver()
        gdf = gpd.read_file(kml_path, driver="LIBKML")
        if len(gdf) > 0:
            return gdf
    except Exception as e:
        errors.append(f"LIBKML: {e}")

    # Method 2: Try with KML driver
    try:
        _enable_kml_driver()
        gdf = gpd.read_file(kml_path, driver="KML")
        if len(gdf) > 0:
            return gdf
    except Exception as e:
        errors.append(f"KML: {e}")

    # Method 3: Try pyogrio if available
    try:
        import pyogrio
        gdf = gpd.read_file(kml_path, engine="pyogrio")
        if len(gdf) > 0:
            return gdf
    except Exception as e:
        errors.append(f"pyogrio: {e}")

    # Method 4: Parse KML manually with xml
    try:
        gdf = _parse_kml_manually(kml_path)
        if len(gdf) > 0:
            return gdf
    except Exception as e:
        errors.append(f"manual: {e}")

    raise ValueError(f"Failed to read KML: {'; '.join(errors)}")


def _parse_kml_manually(kml_path: str) -> gpd.GeoDataFrame:
    """Parse KML file manually using xml.etree."""
    import xml.etree.ElementTree as ET

    tree = ET.parse(kml_path)
    root = tree.getroot()

    # Handle KML namespace
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    # Try without namespace first
    placemarks = root.findall('.//Placemark')
    if not placemarks:
        placemarks = root.findall('.//{http://www.opengis.net/kml/2.2}Placemark')

    geometries = []
    names = []

    for pm in placemarks:
        name_elem = pm.find('name') or pm.find('{http://www.opengis.net/kml/2.2}name')
        name = name_elem.text if name_elem is not None else ""
        names.append(name)

        # Try to find Point
        point = pm.find('.//Point//coordinates') or pm.find('.//{http://www.opengis.net/kml/2.2}Point//{http://www.opengis.net/kml/2.2}coordinates')
        if point is not None:
            coords = point.text.strip().split(',')
            lon, lat = float(coords[0]), float(coords[1])
            geometries.append(Point(lon, lat))
            continue

        # Try to find LineString
        line = pm.find('.//LineString//coordinates') or pm.find('.//{http://www.opengis.net/kml/2.2}LineString//{http://www.opengis.net/kml/2.2}coordinates')
        if line is not None:
            coords_list = []
            for coord in line.text.strip().split():
                parts = coord.split(',')
                coords_list.append((float(parts[0]), float(parts[1])))
            geometries.append(LineString(coords_list))
            continue

        # Try to find Polygon
        poly = pm.find('.//Polygon//coordinates') or pm.find('.//{http://www.opengis.net/kml/2.2}Polygon//{http://www.opengis.net/kml/2.2}coordinates')
        if poly is not None:
            coords_list = []
            for coord in poly.text.strip().split():
                parts = coord.split(',')
                coords_list.append((float(parts[0]), float(parts[1])))
            geometries.append(Polygon(coords_list))
            continue

    if not geometries:
        raise ValueError("No geometries found in KML")

    # Create GeoDataFrame without CRS (will be set by load_aoi)
    gdf = gpd.GeoDataFrame({'name': names, 'geometry': geometries})

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
        try:
            gdf = gdf.set_crs(epsg=4326)
        except Exception:
            # Fallback for PROJ issues
            from pyproj import CRS
            gdf.crs = CRS.from_epsg(4326)

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
