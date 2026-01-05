"""
Change detection functions.

Provides functions for analyzing change between time periods
and creating comprehensive change analyses.
"""

from typing import Dict, List, Optional
import ee

from engine.change.thresholds import ChangeThresholds, ThresholdClassifier


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
