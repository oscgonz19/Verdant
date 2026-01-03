"""
Temporal composite generation from satellite imagery.

This module handles:
- Cloud masking for Landsat and Sentinel-2
- Band harmonization across sensors
- Median composite generation
- Multi-sensor fusion
"""

from typing import Dict, List, Optional, Tuple
import ee

from veg_change_engine.config import (
    BAND_MAPPINGS,
    CLOUD_MASK_CONFIG,
    TEMPORAL_PERIODS,
    get_period_info,
    get_band_mapping,
)


def apply_cloud_mask_landsat(image: ee.Image) -> ee.Image:
    """
    Apply cloud mask to Landsat Collection 2 imagery.

    Uses QA_PIXEL band bit flags to mask:
    - Clouds (bit 3)
    - Cloud shadows (bit 4)
    - Dilated clouds (bit 1)
    - Snow (bit 5)

    Args:
        image: Landsat ee.Image with QA_PIXEL band

    Returns:
        Cloud-masked ee.Image
    """
    qa = image.select("QA_PIXEL")

    # Bit positions for Collection 2
    cloud_bit = CLOUD_MASK_CONFIG["landsat"]["cloud_bit"]
    shadow_bit = CLOUD_MASK_CONFIG["landsat"]["cloud_shadow_bit"]
    dilated_bit = CLOUD_MASK_CONFIG["landsat"]["dilated_cloud_bit"]
    snow_bit = CLOUD_MASK_CONFIG["landsat"]["snow_bit"]

    # Create masks for each condition
    cloud_mask = qa.bitwiseAnd(1 << cloud_bit).eq(0)
    shadow_mask = qa.bitwiseAnd(1 << shadow_bit).eq(0)
    dilated_mask = qa.bitwiseAnd(1 << dilated_bit).eq(0)
    snow_mask = qa.bitwiseAnd(1 << snow_bit).eq(0)

    # Combine all masks
    mask = cloud_mask.And(shadow_mask).And(dilated_mask).And(snow_mask)

    return image.updateMask(mask)


def apply_cloud_mask_sentinel(image: ee.Image) -> ee.Image:
    """
    Apply cloud mask to Sentinel-2 imagery.

    Uses QA60 band bit flags to mask:
    - Opaque clouds (bit 10)
    - Cirrus clouds (bit 11)

    Args:
        image: Sentinel-2 ee.Image with QA60 band

    Returns:
        Cloud-masked ee.Image
    """
    qa = image.select("QA60")

    # Bit positions for QA60
    cloud_bit = CLOUD_MASK_CONFIG["sentinel2"]["cloud_bit"]
    cirrus_bit = CLOUD_MASK_CONFIG["sentinel2"]["cirrus_bit"]

    # Create masks
    cloud_mask = qa.bitwiseAnd(1 << cloud_bit).eq(0)
    cirrus_mask = qa.bitwiseAnd(1 << cirrus_bit).eq(0)

    # Combine masks
    mask = cloud_mask.And(cirrus_mask)

    return image.updateMask(mask)


def scale_landsat(image: ee.Image, sensor: str) -> ee.Image:
    """
    Apply scaling factors to Landsat Collection 2 surface reflectance.

    Formula: reflectance = DN * scale_factor + offset

    Args:
        image: Landsat ee.Image
        sensor: Sensor identifier string

    Returns:
        Scaled ee.Image with reflectance values [0, 1]
    """
    band_config = get_band_mapping(sensor)
    scale = band_config["scale_factor"]
    offset = band_config["offset"]

    # Select optical bands (exclude QA bands)
    optical_bands = image.select("SR_B.*")

    # Apply scaling
    scaled = optical_bands.multiply(scale).add(offset)

    # Clip to valid range
    scaled = scaled.clamp(0, 1)

    # Copy over other bands and properties
    return image.addBands(scaled, overwrite=True)


def scale_sentinel(image: ee.Image) -> ee.Image:
    """
    Apply scaling factor to Sentinel-2 surface reflectance.

    Args:
        image: Sentinel-2 ee.Image

    Returns:
        Scaled ee.Image with reflectance values [0, 1]
    """
    band_config = get_band_mapping("COPERNICUS/S2_SR_HARMONIZED")
    scale = band_config["scale_factor"]

    # Select optical bands
    optical_bands = image.select("B.*")

    # Apply scaling
    scaled = optical_bands.multiply(scale)

    # Clip to valid range
    scaled = scaled.clamp(0, 1)

    return image.addBands(scaled, overwrite=True)


def harmonize_bands(image: ee.Image, sensor: str) -> ee.Image:
    """
    Rename bands to common names across sensors.

    Harmonizes band names to: blue, green, red, nir, swir1, swir2

    Args:
        image: ee.Image from any supported sensor
        sensor: Sensor identifier string

    Returns:
        ee.Image with harmonized band names
    """
    band_config = get_band_mapping(sensor)

    # Original band names for this sensor
    original_bands = [
        band_config["blue"],
        band_config["green"],
        band_config["red"],
        band_config["nir"],
        band_config["swir1"],
        band_config["swir2"],
    ]

    # Common band names
    common_bands = ["blue", "green", "red", "nir", "swir1", "swir2"]

    return image.select(original_bands, common_bands)


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
