"""
Vegetation spectral indices.

Provides NDVI and EVI implementations.
"""

import ee

from engine.indices.base import SpectralIndex


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
