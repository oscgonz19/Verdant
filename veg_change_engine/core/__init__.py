"""
Core analysis modules for vegetation change detection.

- composites: Temporal composite generation from satellite imagery
- indices: Spectral index calculation (NDVI, NBR)
- change: Change detection and classification
"""

from veg_change_engine.core.composites import (
    create_landsat_composite,
    create_sentinel_composite,
    create_fused_composite,
    create_all_period_composites,
    apply_cloud_mask_landsat,
    apply_cloud_mask_sentinel,
    harmonize_bands,
)

from veg_change_engine.core.indices import (
    add_ndvi,
    add_nbr,
    add_all_indices,
    calculate_delta_indices,
)

from veg_change_engine.core.change import (
    classify_change,
    analyze_period_change,
    create_change_analysis,
    generate_change_statistics,
)

__all__ = [
    # Composites
    "create_landsat_composite",
    "create_sentinel_composite",
    "create_fused_composite",
    "create_all_period_composites",
    "apply_cloud_mask_landsat",
    "apply_cloud_mask_sentinel",
    "harmonize_bands",
    # Indices
    "add_ndvi",
    "add_nbr",
    "add_all_indices",
    "calculate_delta_indices",
    # Change detection
    "classify_change",
    "analyze_period_change",
    "create_change_analysis",
    "generate_change_statistics",
]
