"""
Cloud masking functions for satellite imagery.

Provides QA-based cloud masking for:
- Landsat Collection 2 (QA_PIXEL band)
- Sentinel-2 (QA60 band)
"""

import ee

from engine.config import CLOUD_MASK_CONFIG


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
