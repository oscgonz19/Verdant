"""
Burn/fire-related spectral indices.

Provides NBR implementation.
"""

import ee

from engine.indices.base import SpectralIndex


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
