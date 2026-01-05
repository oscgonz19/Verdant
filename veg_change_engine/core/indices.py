"""
Spectral index calculation module.

Note:
    This module provides backward-compatible re-exports from engine/indices/.
    For new code, prefer importing directly from engine.indices.
"""

# Re-export everything from engine.indices
from engine.indices import (
    # Abstract base
    SpectralIndex,
    # Index registry
    INDEX_REGISTRY,
    register_index,
    get_available_indices,
    # Index implementations
    NDVIIndex,
    EVIIndex,
    NBRIndex,
    NDWIIndex,
    NDMIIndex,
    # Convenience functions
    add_ndvi,
    add_nbr,
    add_index,
    add_all_indices,
    calculate_delta_index,
    calculate_delta_indices,
    calculate_relative_change,
)

__all__ = [
    # Abstract base
    "SpectralIndex",
    # Index registry
    "INDEX_REGISTRY",
    "register_index",
    "get_available_indices",
    # Index implementations
    "NDVIIndex",
    "EVIIndex",
    "NBRIndex",
    "NDWIIndex",
    "NDMIIndex",
    # Convenience functions
    "add_ndvi",
    "add_nbr",
    "add_index",
    "add_all_indices",
    "calculate_delta_index",
    "calculate_delta_indices",
    "calculate_relative_change",
]
