"""
Temporal composite generation from satellite imagery.

Note:
    This module provides backward-compatible re-exports from engine/composites/.
    For new code, prefer importing directly from engine.composites.
"""

# Re-export everything from engine.composites
from engine.composites import (
    # Cloud masking
    apply_cloud_mask_landsat,
    apply_cloud_mask_sentinel,
    # Band harmonization
    scale_landsat,
    scale_sentinel,
    harmonize_bands,
    # Temporal composites
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
    # Temporal composites
    "create_landsat_composite",
    "create_sentinel_composite",
    "create_fused_composite",
    "create_all_period_composites",
    "get_image_count",
]
