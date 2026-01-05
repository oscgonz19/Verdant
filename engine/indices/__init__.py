"""
Spectral index calculation module.

Follows Single Responsibility Principle - each function calculates one index.
Extensible (Open/Closed) - new indices can be added without modifying existing code.

Supported indices:
- NDVI (Normalized Difference Vegetation Index)
- NBR (Normalized Burn Ratio)
- NDWI (Normalized Difference Water Index)
- EVI (Enhanced Vegetation Index)
- NDMI (Normalized Difference Moisture Index)
"""

from engine.indices.base import (
    SpectralIndex,
    INDEX_REGISTRY,
    register_index,
    get_available_indices,
)

from engine.indices.vegetation import NDVIIndex, EVIIndex
from engine.indices.burn import NBRIndex
from engine.indices.water import NDWIIndex, NDMIIndex

from engine.indices.convenience import (
    add_ndvi,
    add_nbr,
    add_ndwi,
    add_evi,
    add_ndmi,
    add_index,
    add_all_indices,
    calculate_delta_index,
    calculate_delta_indices,
    calculate_relative_change,
)

# Auto-register indices
INDEX_REGISTRY["ndvi"] = NDVIIndex()
INDEX_REGISTRY["nbr"] = NBRIndex()
INDEX_REGISTRY["ndwi"] = NDWIIndex()
INDEX_REGISTRY["evi"] = EVIIndex()
INDEX_REGISTRY["ndmi"] = NDMIIndex()

__all__ = [
    # Base
    "SpectralIndex",
    "INDEX_REGISTRY",
    "register_index",
    "get_available_indices",
    # Index classes
    "NDVIIndex",
    "EVIIndex",
    "NBRIndex",
    "NDWIIndex",
    "NDMIIndex",
    # Convenience functions
    "add_ndvi",
    "add_nbr",
    "add_ndwi",
    "add_evi",
    "add_ndmi",
    "add_index",
    "add_all_indices",
    # Delta calculations
    "calculate_delta_index",
    "calculate_delta_indices",
    "calculate_relative_change",
]
