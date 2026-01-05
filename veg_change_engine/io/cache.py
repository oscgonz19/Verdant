"""
Caching module for Earth Engine data persistence.

Note:
    This module provides backward-compatible re-exports from engine/io/cache.py.
    For new code, prefer importing directly from engine.io.cache.
"""

# Re-export everything from engine.io.cache
from engine.io.cache import (
    # Asset caching
    AssetCache,
    # Local caching
    LocalCache,
    # Combined cache wrapper
    CachedAnalysis,
    # Convenience function
    setup_cache,
)

__all__ = [
    "AssetCache",
    "LocalCache",
    "CachedAnalysis",
    "setup_cache",
]
