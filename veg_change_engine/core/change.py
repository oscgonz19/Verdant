"""
Change detection and classification module.

Note:
    This module provides backward-compatible re-exports from engine/change/.
    For new code, prefer importing directly from engine.change.
"""

# Re-export everything from engine.change
from engine.change import (
    # Thresholds
    ChangeThresholds,
    # Classifiers
    ChangeClassifier,
    ThresholdClassifier,
    # Detection functions
    classify_change,
    analyze_period_change,
    create_change_analysis,
    create_sequential_change,
    # Statistics
    generate_change_statistics,
    calculate_area_by_class,
    get_class_info,
    summarize_change,
)

__all__ = [
    # Thresholds
    "ChangeThresholds",
    # Classifiers
    "ChangeClassifier",
    "ThresholdClassifier",
    # Detection functions
    "classify_change",
    "analyze_period_change",
    "create_change_analysis",
    "create_sequential_change",
    # Statistics
    "generate_change_statistics",
    "calculate_area_by_class",
    "get_class_info",
    "summarize_change",
]
