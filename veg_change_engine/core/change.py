"""
Change detection and classification module.

Follows SOLID principles:
- Single Responsibility: Each function handles one aspect of change detection
- Open/Closed: Threshold configurations are injectable
- Dependency Inversion: Depends on abstractions (config) not concrete values
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import ee

from veg_change_engine.config import CHANGE_THRESHOLDS, CHANGE_CLASSES


# =============================================================================
# CLASSIFICATION STRATEGY (Strategy Pattern)
# =============================================================================

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


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def classify_change(
    delta_image: ee.Image,
    thresholds: Optional[ChangeThresholds] = None,
    index_name: str = "dndvi",
) -> ee.Image:
    """
    Classify change delta into discrete categories.

    Args:
        delta_image: ee.Image with delta values
        thresholds: Custom thresholds (default: from config)
        index_name: Index name for default thresholds

    Returns:
        ee.Image with change_class band (1-5)
    """
    if thresholds is None:
        thresholds = ChangeThresholds.from_config(index_name.replace("d", ""))

    classifier = ThresholdClassifier(thresholds)
    return classifier.classify(delta_image)


def analyze_period_change(
    before: ee.Image,
    after: ee.Image,
    index_name: str = "ndvi",
    thresholds: Optional[ChangeThresholds] = None,
) -> ee.Image:
    """
    Analyze change between two time periods.

    Calculates delta and classifies into change categories.

    Args:
        before: Earlier period composite with index band
        after: Later period composite with index band
        index_name: Name of the index to analyze
        thresholds: Custom thresholds

    Returns:
        ee.Image with delta and change_class bands
    """
    # Calculate delta
    before_index = before.select(index_name)
    after_index = after.select(index_name)
    delta = after_index.subtract(before_index).rename(f"d{index_name}")

    # Classify change
    classified = classify_change(delta, thresholds, f"d{index_name}")

    # Combine bands
    return delta.addBands(classified)


def create_change_analysis(
    composites: Dict[str, ee.Image],
    indices: Optional[List[str]] = None,
    reference_period: str = "1990s",
) -> Dict[str, ee.Image]:
    """
    Create comprehensive change analysis across all periods.

    Compares each period to the reference (baseline) period.

    Args:
        composites: Dictionary of period composites
        indices: List of indices to analyze (default: ndvi, nbr)
        reference_period: Baseline period for comparison

    Returns:
        Dictionary mapping period pairs to change images
    """
    if indices is None:
        indices = ["ndvi", "nbr"]

    if reference_period not in composites:
        raise ValueError(f"Reference period '{reference_period}' not in composites")

    baseline = composites[reference_period]
    change_images = {}

    # Analyze change from baseline to each subsequent period
    for period_name, composite in composites.items():
        if period_name == reference_period:
            continue

        period_changes = []

        for index_name in indices:
            change = analyze_period_change(baseline, composite, index_name)
            period_changes.append(change)

        # Combine all index changes
        combined = period_changes[0]
        for change_img in period_changes[1:]:
            combined = combined.addBands(change_img)

        # Set metadata
        combined = combined.set({
            "reference_period": reference_period,
            "comparison_period": period_name,
            "indices": indices,
        })

        key = f"{reference_period}_to_{period_name}"
        change_images[key] = combined

    return change_images


def create_sequential_change(
    composites: Dict[str, ee.Image],
    period_order: List[str],
    index_name: str = "ndvi",
) -> Dict[str, ee.Image]:
    """
    Create sequential change analysis between consecutive periods.

    Args:
        composites: Dictionary of period composites
        period_order: Ordered list of periods
        index_name: Index to analyze

    Returns:
        Dictionary of change images for consecutive period pairs
    """
    change_images = {}

    for i in range(len(period_order) - 1):
        before_period = period_order[i]
        after_period = period_order[i + 1]

        if before_period not in composites or after_period not in composites:
            continue

        change = analyze_period_change(
            composites[before_period],
            composites[after_period],
            index_name,
        )

        key = f"{before_period}_to_{after_period}"
        change_images[key] = change

    return change_images


# =============================================================================
# STATISTICS
# =============================================================================

def generate_change_statistics(
    change_image: ee.Image,
    aoi: ee.Geometry,
    scale: int = 30,
) -> Dict:
    """
    Generate statistics for change classification.

    Args:
        change_image: ee.Image with change_class band
        aoi: Area of interest
        scale: Analysis scale in meters

    Returns:
        Dictionary with class counts and percentages
    """
    # Count pixels per class
    class_band = change_image.select("change_class")

    # Calculate histogram
    histogram = class_band.reduceRegion(
        reducer=ee.Reducer.frequencyHistogram(),
        geometry=aoi,
        scale=scale,
        maxPixels=1e9,
    )

    return histogram


def calculate_area_by_class(
    change_image: ee.Image,
    aoi: ee.Geometry,
    scale: int = 30,
) -> ee.Dictionary:
    """
    Calculate area (in hectares) for each change class.

    Args:
        change_image: ee.Image with change_class band
        aoi: Area of interest
        scale: Analysis scale in meters

    Returns:
        ee.Dictionary with class areas in hectares
    """
    class_band = change_image.select("change_class")
    pixel_area = ee.Image.pixelArea()

    # Area per class in square meters
    area_image = class_band.addBands(pixel_area)

    areas = area_image.reduceRegion(
        reducer=ee.Reducer.sum().group(
            groupField=0,
            groupName="class",
        ),
        geometry=aoi,
        scale=scale,
        maxPixels=1e9,
    )

    return areas


def get_class_info(class_value: int, language: str = "en") -> Dict:
    """
    Get human-readable information for a change class.

    Args:
        class_value: Integer class (1-5)
        language: Language code ("en" or "es")

    Returns:
        Dictionary with label and color
    """
    if class_value not in CHANGE_CLASSES:
        raise ValueError(f"Invalid class: {class_value}. Valid: 1-5")

    info = CHANGE_CLASSES[class_value]
    label_key = "label" if language == "en" else "label_es"

    return {
        "class": class_value,
        "label": info[label_key],
        "color": info["color"],
    }


def summarize_change(
    change_image: ee.Image,
    aoi: ee.Geometry,
    scale: int = 30,
    language: str = "en",
) -> List[Dict]:
    """
    Generate human-readable change summary.

    Args:
        change_image: ee.Image with change_class band
        aoi: Area of interest
        scale: Analysis scale
        language: Output language

    Returns:
        List of dictionaries with class info and statistics
    """
    stats = generate_change_statistics(change_image, aoi, scale)

    summary = []
    for class_value in range(1, 6):
        info = get_class_info(class_value, language)
        summary.append(info)

    return summary
