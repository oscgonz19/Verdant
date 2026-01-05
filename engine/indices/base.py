"""
Base classes and registry for spectral indices.

Provides the abstract base class for index implementations
and the registry pattern for extensibility.
"""

from typing import Dict, List
from abc import ABC, abstractmethod
import ee


class SpectralIndex(ABC):
    """Abstract base class for spectral indices."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Index name for band naming."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        pass

    @abstractmethod
    def calculate(self, image: ee.Image) -> ee.Image:
        """Calculate the index and add as a band."""
        pass


# Registry of available indices - extend by adding new entries
INDEX_REGISTRY: Dict[str, SpectralIndex] = {}


def register_index(index: SpectralIndex) -> None:
    """Register a custom index in the registry."""
    INDEX_REGISTRY[index.name] = index


def get_available_indices() -> List[str]:
    """Get list of available index names."""
    return list(INDEX_REGISTRY.keys())
