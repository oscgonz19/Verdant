"""
Band harmonization and scaling functions for satellite imagery.

Provides functions to:
- Apply scaling factors to surface reflectance
- Harmonize band names across different sensors
"""

import ee

from engine.config import get_band_mapping


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
