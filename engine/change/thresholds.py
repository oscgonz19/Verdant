"""
Threshold configuration and classification strategies.

Provides configurable thresholds and the strategy pattern
for change classification.
"""

from dataclasses import dataclass
from abc import ABC, abstractmethod
import ee

from engine.config import CHANGE_THRESHOLDS


@dataclass
class ChangeThresholds:
    """
    Configurable thresholds for change classification.

    Implements Dependency Inversion - injectable thresholds.
    """
    strong_loss: float
    moderate_loss: float
    stable_min: float
    stable_max: float
    moderate_gain: float
    strong_gain: float

    @classmethod
    def from_config(cls, index_name: str) -> "ChangeThresholds":
        """Create thresholds from default configuration."""
        config = CHANGE_THRESHOLDS.get(f"d{index_name}", CHANGE_THRESHOLDS["dndvi"])
        return cls(
            strong_loss=config["strong_loss"],
            moderate_loss=config["moderate_loss"],
            stable_min=config["stable_min"],
            stable_max=config["stable_max"],
            moderate_gain=config["moderate_gain"],
            strong_gain=config["strong_gain"],
        )


class ChangeClassifier(ABC):
    """Abstract base class for change classification strategies."""

    @abstractmethod
    def classify(self, delta_image: ee.Image) -> ee.Image:
        """Classify change into discrete categories."""
        pass


class ThresholdClassifier(ChangeClassifier):
    """
    Classify change using threshold-based rules.

    Classes:
    1 = Strong Loss
    2 = Moderate Loss
    3 = Stable
    4 = Moderate Gain
    5 = Strong Gain
    """

    def __init__(self, thresholds: ChangeThresholds):
        self.thresholds = thresholds

    def classify(self, delta_image: ee.Image) -> ee.Image:
        """
        Apply threshold classification to delta image.

        Args:
            delta_image: ee.Image with delta index values

        Returns:
            ee.Image with integer class values (1-5)
        """
        t = self.thresholds

        # Start with class 3 (stable)
        classified = ee.Image.constant(3)

        # Apply thresholds in order
        classified = classified.where(
            delta_image.lte(t.strong_loss), 1  # Strong loss
        )
        classified = classified.where(
            delta_image.gt(t.strong_loss).And(delta_image.lte(t.moderate_loss)), 2  # Moderate loss
        )
        classified = classified.where(
            delta_image.gte(t.moderate_gain).And(delta_image.lt(t.strong_gain)), 4  # Moderate gain
        )
        classified = classified.where(
            delta_image.gte(t.strong_gain), 5  # Strong gain
        )

        return classified.rename("change_class").toUint8()
