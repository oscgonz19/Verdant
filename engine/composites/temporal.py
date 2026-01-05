"""
Temporal composite creation functions.

Provides functions to create cloud-free median composites from:
- Individual Landsat sensors
- Sentinel-2
- Multi-sensor fusion
"""

from typing import Dict, List, Optional
import ee

from engine.config import TEMPORAL_PERIODS, get_period_info
from engine.composites.cloud_masking import (
    apply_cloud_mask_landsat,
    apply_cloud_mask_sentinel,
)
from engine.composites.band_harmonization import (
    scale_landsat,
    scale_sentinel,
    harmonize_bands,
)


def create_landsat_composite(
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
    sensor: str,
    cloud_threshold: float = 20.0,
) -> ee.Image:
    """
    Create a cloud-free median composite from Landsat imagery.

    Args:
        aoi: Area of interest as ee.Geometry
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        sensor: Landsat sensor identifier
        cloud_threshold: Maximum cloud cover percentage

    Returns:
        Median composite ee.Image with harmonized bands
    """
    # Load and filter collection
    collection = (
        ee.ImageCollection(sensor)
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUD_COVER", cloud_threshold))
    )

    # Apply cloud mask and scaling
    def preprocess(image):
        masked = apply_cloud_mask_landsat(image)
        scaled = scale_landsat(masked, sensor)
        harmonized = harmonize_bands(scaled, sensor)
        return harmonized

    processed = collection.map(preprocess)

    # Create median composite
    composite = processed.median().clip(aoi)

    # Add metadata
    composite = composite.set({
        "sensor": sensor,
        "start_date": start_date,
        "end_date": end_date,
        "image_count": collection.size(),
    })

    return composite


def create_sentinel_composite(
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
    cloud_threshold: float = 20.0,
) -> ee.Image:
    """
    Create a cloud-free median composite from Sentinel-2 imagery.

    Args:
        aoi: Area of interest as ee.Geometry
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        cloud_threshold: Maximum cloud cover percentage

    Returns:
        Median composite ee.Image with harmonized bands
    """
    sensor = "COPERNICUS/S2_SR_HARMONIZED"

    # Load and filter collection
    collection = (
        ee.ImageCollection(sensor)
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
    )

    # Apply cloud mask and scaling
    def preprocess(image):
        masked = apply_cloud_mask_sentinel(image)
        scaled = scale_sentinel(masked)
        harmonized = harmonize_bands(scaled, sensor)
        return harmonized

    processed = collection.map(preprocess)

    # Create median composite
    composite = processed.median().clip(aoi)

    # Add metadata
    composite = composite.set({
        "sensor": sensor,
        "start_date": start_date,
        "end_date": end_date,
        "image_count": collection.size(),
    })

    return composite


def create_fused_composite(
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
    sensors: List[str],
    cloud_threshold: float = 20.0,
) -> ee.Image:
    """
    Create a fused median composite from multiple sensors.

    Merges collections from different sensors into a single composite,
    useful for periods with limited imagery from individual sensors.

    Args:
        aoi: Area of interest as ee.Geometry
        start_date: Start date string
        end_date: End date string
        sensors: List of sensor identifiers
        cloud_threshold: Maximum cloud cover percentage

    Returns:
        Fused median composite ee.Image
    """
    merged_collection = None

    for sensor in sensors:
        if "S2" in sensor or "COPERNICUS" in sensor:
            # Sentinel-2
            collection = (
                ee.ImageCollection(sensor)
                .filterBounds(aoi)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
            )

            def preprocess_s2(image):
                masked = apply_cloud_mask_sentinel(image)
                scaled = scale_sentinel(masked)
                return harmonize_bands(scaled, sensor)

            processed = collection.map(preprocess_s2)

        else:
            # Landsat
            collection = (
                ee.ImageCollection(sensor)
                .filterBounds(aoi)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt("CLOUD_COVER", cloud_threshold))
            )

            def make_preprocess_landsat(s):
                def preprocess_ls(image):
                    masked = apply_cloud_mask_landsat(image)
                    scaled = scale_landsat(masked, s)
                    return harmonize_bands(scaled, s)
                return preprocess_ls

            processed = collection.map(make_preprocess_landsat(sensor))

        # Merge collections
        if merged_collection is None:
            merged_collection = processed
        else:
            merged_collection = merged_collection.merge(processed)

    # Create median composite from merged collection
    composite = merged_collection.median().clip(aoi)

    # Add metadata
    composite = composite.set({
        "sensors": sensors,
        "start_date": start_date,
        "end_date": end_date,
    })

    return composite


def create_all_period_composites(
    aoi: ee.Geometry,
    periods: Optional[List[str]] = None,
    cloud_threshold: float = 20.0,
) -> Dict[str, ee.Image]:
    """
    Create composites for all specified temporal periods.

    Args:
        aoi: Area of interest as ee.Geometry
        periods: List of period names (default: all periods)
        cloud_threshold: Maximum cloud cover percentage

    Returns:
        Dictionary mapping period names to composite images
    """
    if periods is None:
        periods = list(TEMPORAL_PERIODS.keys())

    composites = {}

    for period_name in periods:
        period_info = get_period_info(period_name)

        composite = create_fused_composite(
            aoi=aoi,
            start_date=period_info["start"],
            end_date=period_info["end"],
            sensors=period_info["sensors"],
            cloud_threshold=cloud_threshold,
        )

        # Add period name to metadata
        composite = composite.set("period", period_name)
        composites[period_name] = composite

    return composites


def get_image_count(
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
    sensor: str,
    cloud_threshold: float = 20.0,
) -> ee.Number:
    """
    Get the number of available images for a sensor and date range.

    Args:
        aoi: Area of interest
        start_date: Start date string
        end_date: End date string
        sensor: Sensor identifier
        cloud_threshold: Maximum cloud cover

    Returns:
        ee.Number with image count
    """
    if "S2" in sensor or "COPERNICUS" in sensor:
        cloud_property = "CLOUDY_PIXEL_PERCENTAGE"
    else:
        cloud_property = "CLOUD_COVER"

    count = (
        ee.ImageCollection(sensor)
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt(cloud_property, cloud_threshold))
        .size()
    )

    return count
