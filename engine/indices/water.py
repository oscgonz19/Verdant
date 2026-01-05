"""
Water and moisture-related spectral indices.

Provides NDWI and NDMI implementations.
"""

import ee

from engine.indices.base import SpectralIndex


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
