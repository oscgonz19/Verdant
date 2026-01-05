"""
Configuration module for Vegetation Change Intelligence Platform.

Note:
    This module provides backward-compatible re-exports from engine/config.py.
    For new code, prefer importing directly from engine.config.
"""

# Re-export everything from engine.config
from engine.config import (
    # Temporal periods
    TEMPORAL_PERIODS,
    # Sensor configurations
    BAND_MAPPINGS,
    # Cloud masking
    CLOUD_MASK_CONFIG,
    # Visualization parameters
    VIS_PARAMS,
    # Change detection thresholds
    CHANGE_THRESHOLDS,
    CHANGE_CLASSES,
    # Configuration class
    VegChangeConfig,
    DEFAULT_CONFIG,
    # Helper functions
    get_config,
    get_period_info,
    get_band_mapping,
)

__all__ = [
    "TEMPORAL_PERIODS",
    "BAND_MAPPINGS",
    "CLOUD_MASK_CONFIG",
    "VIS_PARAMS",
    "CHANGE_THRESHOLDS",
    "CHANGE_CLASSES",
    "VegChangeConfig",
    "DEFAULT_CONFIG",
    "get_config",
    "get_period_info",
    "get_band_mapping",
]
