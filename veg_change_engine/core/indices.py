"""
Spectral index calculation module.

Follows Single Responsibility Principle - each function calculates one index.
Extensible (Open/Closed) - new indices can be added without modifying existing code.

Supported indices:
- NDVI (Normalized Difference Vegetation Index)
- NBR (Normalized Burn Ratio)
- NDWI (Normalized Difference Water Index)
- EVI (Enhanced Vegetation Index)
"""

from typing import Callable, Dict, List, Optional
from abc import ABC, abstractmethod
import ee


# =============================================================================
# ABSTRACT BASE (Dependency Inversion Principle)
# =============================================================================

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


# =============================================================================
# CONCRETE INDEX IMPLEMENTATIONS
# =============================================================================

class NDVIIndex(SpectralIndex):
    """
    Normalized Difference Vegetation Index.

    NDVI = (NIR - Red) / (NIR + Red)

    Values range from -1 to 1:
    - Negative: Water, bare soil
    - 0-0.2: Sparse vegetation
    - 0.2-0.4: Moderate vegetation
    - 0.4-0.6: Dense vegetation
    - 0.6+: Very dense vegetation
    """

    @property
    def name(self) -> str:
        return "ndvi"

    @property
    def description(self) -> str:
        return "Normalized Difference Vegetation Index"

    def calculate(self, image: ee.Image) -> ee.Image:
        """Calculate NDVI from harmonized bands."""
        nir = image.select("nir")
        red = image.select("red")
        ndvi = nir.subtract(red).divide(nir.add(red)).rename(self.name)
        return image.addBands(ndvi)


class NBRIndex(SpectralIndex):
    """
    Normalized Burn Ratio.

    NBR = (NIR - SWIR2) / (NIR + SWIR2)

    Used for burn severity assessment:
    - Low values: Burned areas
    - High values: Healthy vegetation
    """

    @property
    def name(self) -> str:
        return "nbr"

    @property
    def description(self) -> str:
        return "Normalized Burn Ratio"

    def calculate(self, image: ee.Image) -> ee.Image:
        """Calculate NBR from harmonized bands."""
        nir = image.select("nir")
        swir2 = image.select("swir2")
        nbr = nir.subtract(swir2).divide(nir.add(swir2)).rename(self.name)
        return image.addBands(nbr)


class NDWIIndex(SpectralIndex):
    """
    Normalized Difference Water Index.

    NDWI = (Green - NIR) / (Green + NIR)

    Used for water body detection:
    - Positive: Water bodies
    - Negative: Vegetation/soil
    """

    @property
    def name(self) -> str:
        return "ndwi"

    @property
    def description(self) -> str:
        return "Normalized Difference Water Index"

    def calculate(self, image: ee.Image) -> ee.Image:
        """Calculate NDWI from harmonized bands."""
        green = image.select("green")
        nir = image.select("nir")
        ndwi = green.subtract(nir).divide(green.add(nir)).rename(self.name)
        return image.addBands(ndwi)


class EVIIndex(SpectralIndex):
    """
    Enhanced Vegetation Index.

    EVI = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)

    More sensitive in high-biomass regions than NDVI.
    """

    @property
    def name(self) -> str:
        return "evi"

    @property
    def description(self) -> str:
        return "Enhanced Vegetation Index"

    def calculate(self, image: ee.Image) -> ee.Image:
        """Calculate EVI from harmonized bands."""
        nir = image.select("nir")
        red = image.select("red")
        blue = image.select("blue")

        evi = nir.subtract(red).multiply(2.5).divide(
            nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)
        ).rename(self.name)

        return image.addBands(evi)


class NDMIIndex(SpectralIndex):
    """
    Normalized Difference Moisture Index.

    NDMI = (NIR - SWIR1) / (NIR + SWIR1)

    Sensitive to vegetation water content.
    """

    @property
    def name(self) -> str:
        return "ndmi"

    @property
    def description(self) -> str:
        return "Normalized Difference Moisture Index"

    def calculate(self, image: ee.Image) -> ee.Image:
        """Calculate NDMI from harmonized bands."""
        nir = image.select("nir")
        swir1 = image.select("swir1")
        ndmi = nir.subtract(swir1).divide(nir.add(swir1)).rename(self.name)
        return image.addBands(ndmi)


# =============================================================================
# INDEX REGISTRY (Open/Closed Principle)
# =============================================================================

# Registry of available indices - extend by adding new entries
INDEX_REGISTRY: Dict[str, SpectralIndex] = {
    "ndvi": NDVIIndex(),
    "nbr": NBRIndex(),
    "ndwi": NDWIIndex(),
    "evi": EVIIndex(),
    "ndmi": NDMIIndex(),
}


def register_index(index: SpectralIndex) -> None:
    """Register a custom index in the registry."""
    INDEX_REGISTRY[index.name] = index


def get_available_indices() -> List[str]:
    """Get list of available index names."""
    return list(INDEX_REGISTRY.keys())


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def add_ndvi(image: ee.Image) -> ee.Image:
    """Add NDVI band to image."""
    return INDEX_REGISTRY["ndvi"].calculate(image)


def add_nbr(image: ee.Image) -> ee.Image:
    """Add NBR band to image."""
    return INDEX_REGISTRY["nbr"].calculate(image)


def add_ndwi(image: ee.Image) -> ee.Image:
    """Add NDWI band to image."""
    return INDEX_REGISTRY["ndwi"].calculate(image)


def add_evi(image: ee.Image) -> ee.Image:
    """Add EVI band to image."""
    return INDEX_REGISTRY["evi"].calculate(image)


def add_ndmi(image: ee.Image) -> ee.Image:
    """Add NDMI band to image."""
    return INDEX_REGISTRY["ndmi"].calculate(image)


def add_index(image: ee.Image, index_name: str) -> ee.Image:
    """
    Add a specific index band to image.

    Args:
        image: ee.Image with harmonized bands
        index_name: Name of index to add

    Returns:
        ee.Image with index band added

    Raises:
        ValueError: If index_name is not registered
    """
    if index_name not in INDEX_REGISTRY:
        available = ", ".join(get_available_indices())
        raise ValueError(f"Unknown index: {index_name}. Available: {available}")

    return INDEX_REGISTRY[index_name].calculate(image)


def add_all_indices(
    image: ee.Image,
    indices: Optional[List[str]] = None,
) -> ee.Image:
    """
    Add multiple index bands to image.

    Args:
        image: ee.Image with harmonized bands
        indices: List of index names (default: ndvi, nbr)

    Returns:
        ee.Image with all specified index bands
    """
    if indices is None:
        indices = ["ndvi", "nbr"]

    result = image
    for index_name in indices:
        result = add_index(result, index_name)

    return result


# =============================================================================
# CHANGE INDEX CALCULATION
# =============================================================================

def calculate_delta_index(
    before: ee.Image,
    after: ee.Image,
    index_name: str,
) -> ee.Image:
    """
    Calculate the change (delta) in an index between two images.

    delta = after - before

    Positive values indicate increase (e.g., vegetation growth)
    Negative values indicate decrease (e.g., vegetation loss)

    Args:
        before: Earlier time period image
        after: Later time period image
        index_name: Name of the index band

    Returns:
        ee.Image with delta_{index_name} band
    """
    before_index = before.select(index_name)
    after_index = after.select(index_name)

    delta = after_index.subtract(before_index).rename(f"d{index_name}")

    return delta


def calculate_delta_indices(
    before: ee.Image,
    after: ee.Image,
    indices: Optional[List[str]] = None,
) -> ee.Image:
    """
    Calculate change for multiple indices.

    Args:
        before: Earlier time period composite
        after: Later time period composite
        indices: List of index names (default: ndvi, nbr)

    Returns:
        ee.Image with delta bands for each index
    """
    if indices is None:
        indices = ["ndvi", "nbr"]

    delta_bands = []
    for index_name in indices:
        delta = calculate_delta_index(before, after, index_name)
        delta_bands.append(delta)

    # Combine all delta bands
    if len(delta_bands) == 1:
        return delta_bands[0]

    result = delta_bands[0]
    for band in delta_bands[1:]:
        result = result.addBands(band)

    return result


def calculate_relative_change(
    before: ee.Image,
    after: ee.Image,
    index_name: str,
) -> ee.Image:
    """
    Calculate relative (percentage) change in an index.

    relative_change = (after - before) / before * 100

    Args:
        before: Earlier time period image
        after: Later time period image
        index_name: Name of the index band

    Returns:
        ee.Image with relative change as percentage
    """
    before_index = before.select(index_name)
    after_index = after.select(index_name)

    # Avoid division by zero
    safe_before = before_index.where(before_index.eq(0), 0.001)

    relative = after_index.subtract(before_index).divide(safe_before).multiply(100)

    return relative.rename(f"rel_d{index_name}")
