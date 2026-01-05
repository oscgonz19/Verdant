"""
Vegetation Change Intelligence Platform - Engine Module

Core Google Earth Engine processing logic for vegetation change analysis.
This module provides the foundation for satellite imagery processing,
spectral index calculation, and change detection.

Submodules:
    - composites: Temporal composite generation from satellite imagery
    - indices: Spectral index calculation (NDVI, NBR, etc.)
    - change: Change detection and classification
    - io: Input/output operations (AOI loading, export, caching)
    - config: Configuration and constants
    - ee_init: Earth Engine initialization
    - alphaearth: Google satellite embedding integration
"""

__version__ = "1.0.0"

# Configuration
from engine.config import (
    VegChangeConfig,
    DEFAULT_CONFIG,
    TEMPORAL_PERIODS,
    BAND_MAPPINGS,
    CLOUD_MASK_CONFIG,
    CHANGE_THRESHOLDS,
    CHANGE_CLASSES,
    VIS_PARAMS,
    get_config,
    get_period_info,
    get_band_mapping,
)

# Earth Engine initialization
from engine.ee_init import (
    initialize_ee,
    is_ee_initialized,
    get_ee_status,
    authenticate_ee,
    init_ee_streamlit,
    EEAuthenticationError,
    EEInitializer,
    EECredentials,
)

# AlphaEarth embeddings
from engine.alphaearth import (
    AlphaEarthClient,
    EmbeddingConfig,
    ALPHAEARTH_COLLECTION,
    EMBEDDING_DIM,
    AVAILABLE_YEARS,
    get_alphaearth_embedding,
    detect_semantic_change,
    combine_with_spectral_change,
)

__all__ = [
    # Config
    "VegChangeConfig",
    "DEFAULT_CONFIG",
    "TEMPORAL_PERIODS",
    "BAND_MAPPINGS",
    "CLOUD_MASK_CONFIG",
    "CHANGE_THRESHOLDS",
    "CHANGE_CLASSES",
    "VIS_PARAMS",
    "get_config",
    "get_period_info",
    "get_band_mapping",
    # EE Init
    "initialize_ee",
    "is_ee_initialized",
    "get_ee_status",
    "authenticate_ee",
    "init_ee_streamlit",
    "EEAuthenticationError",
    "EEInitializer",
    "EECredentials",
    # AlphaEarth
    "AlphaEarthClient",
    "EmbeddingConfig",
    "ALPHAEARTH_COLLECTION",
    "EMBEDDING_DIM",
    "AVAILABLE_YEARS",
    "get_alphaearth_embedding",
    "detect_semantic_change",
    "combine_with_spectral_change",
]
