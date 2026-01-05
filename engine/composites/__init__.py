"""
Temporal composite generation from satellite imagery.

This module handles:
- Cloud masking for Landsat and Sentinel-2
- Band harmonization across sensors
- Median composite generation
- Multi-sensor fusion
"""

from engine.composites.cloud_masking import (
    apply_cloud_mask_landsat,
    apply_cloud_mask_sentinel,
)

from engine.composites.band_harmonization import (
    scale_landsat,
    scale_sentinel,
    harmonize_bands,
)

from engine.composites.temporal import (
    create_landsat_composite,
    create_sentinel_composite,
    create_fused_composite,
    create_all_period_composites,
    get_image_count,
)

__all__ = [
    # Cloud masking
    "apply_cloud_mask_landsat",
    "apply_cloud_mask_sentinel",
    # Band harmonization
    "scale_landsat",
    "scale_sentinel",
    "harmonize_bands",
    # Composite creation
    "create_landsat_composite",
    "create_sentinel_composite",
    "create_fused_composite",
    "create_all_period_composites",
    "get_image_count",
]
