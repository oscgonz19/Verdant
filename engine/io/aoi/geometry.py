"""
Geometry conversion and manipulation functions for AOI.

Provides functions for:
- Converting GeoDataFrame to Earth Engine geometry
- Buffering AOI
- Extracting metadata (bounds, centroid, area)
"""

from typing import Dict, Optional
import json

import geopandas as gpd
from shapely.geometry import mapping
import ee


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
