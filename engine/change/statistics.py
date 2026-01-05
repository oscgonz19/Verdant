"""
Change statistics and summary functions.

Provides functions for generating statistics and summaries
from change classification results.
"""

from typing import Dict, List
import ee

from engine.config import CHANGE_CLASSES


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
