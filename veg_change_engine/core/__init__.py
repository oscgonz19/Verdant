"""
Core analysis modules for vegetation change detection.

Note:
    This module provides backward-compatible re-exports from engine/.
    For new code, prefer importing directly from engine.composites,
    engine.indices, and engine.change.
"""

# Re-export from engine modules
from engine.composites import (
    create_landsat_composite,
    create_sentinel_composite,
    create_fused_composite,
    create_all_period_composites,
    apply_cloud_mask_landsat,
    apply_cloud_mask_sentinel,
    harmonize_bands,
)

from engine.indices import (
    add_ndvi,
    add_nbr,
    add_all_indices,
    calculate_delta_indices,
)

from engine.change import (
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
