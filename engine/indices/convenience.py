"""
Convenience functions for spectral index operations.

Provides easy-to-use functions for adding indices to images
and calculating change between time periods.
"""

from typing import List, Optional
import ee

from engine.indices.base import INDEX_REGISTRY, get_available_indices


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
