"""
Change detection and classification module.

Follows SOLID principles:
- Single Responsibility: Each function handles one aspect of change detection
- Open/Closed: Threshold configurations are injectable
- Dependency Inversion: Depends on abstractions (config) not concrete values
"""

from engine.change.thresholds import (
    ChangeThresholds,
    ChangeClassifier,
    ThresholdClassifier,
)

from engine.change.detection import (
    classify_change,
    analyze_period_change,
    create_change_analysis,
    create_sequential_change,
)

from engine.change.statistics import (
    generate_change_statistics,
    calculate_area_by_class,
    get_class_info,
    summarize_change,
)

__all__ = [
    # Thresholds and classifiers
    "ChangeThresholds",
    "ChangeClassifier",
    "ThresholdClassifier",
    # Detection functions
    "classify_change",
    "analyze_period_change",
    "create_change_analysis",
    "create_sequential_change",
    # Statistics functions
    "generate_change_statistics",
    "calculate_area_by_class",
    "get_class_info",
    "summarize_change",
]
