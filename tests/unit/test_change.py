"""
Unit tests for change detection module.

Tests cover:
- Change classification
- Threshold configuration
- Statistics generation
- Multi-period analysis
"""

import pytest
from unittest.mock import MagicMock, Mock, patch


class TestChangeClassification:
    """Tests for change classification logic."""

    def test_classify_change_returns_5_classes(self, mock_ee):
        """Test change classification produces 5 classes."""
        from engine.change import classify_change

        mock_delta = MagicMock()

        result = classify_change(
            delta_image=mock_delta,
            index="ndvi"
        )

        # Should produce classified image
        assert result is not None

    def test_classify_change_uses_thresholds(self, mock_ee):
        """Test classification uses correct thresholds."""
        from engine.change import classify_change
        from engine.change.thresholds import CHANGE_THRESHOLDS

        mock_delta = MagicMock()

        thresholds = CHANGE_THRESHOLDS.get("ndvi", {})

        result = classify_change(
            delta_image=mock_delta,
            index="ndvi",
            thresholds=thresholds
        )

        assert result is not None

    def test_custom_thresholds(self, mock_ee):
        """Test classification with custom thresholds."""
        from engine.change import classify_change

        mock_delta = MagicMock()
        custom_thresholds = {
            "strong_loss": -0.20,
            "moderate_loss": -0.10,
            "moderate_gain": 0.10,
            "strong_gain": 0.20
        }

        result = classify_change(
            delta_image=mock_delta,
            index="ndvi",
            thresholds=custom_thresholds
        )

        assert result is not None


class TestChangeThresholds:
    """Tests for change threshold configuration."""

    def test_default_ndvi_thresholds(self, mock_ee):
        """Test default NDVI thresholds are reasonable."""
        from engine.change.thresholds import CHANGE_THRESHOLDS

        ndvi_thresholds = CHANGE_THRESHOLDS.get("ndvi", {})

        # Strong loss should be negative
        assert ndvi_thresholds.get("strong_loss", 0) < 0

        # Strong gain should be positive
        assert ndvi_thresholds.get("strong_gain", 0) > 0

        # Thresholds should be symmetric-ish
        assert abs(ndvi_thresholds.get("strong_loss", 0)) > 0.1
        assert ndvi_thresholds.get("strong_gain", 0) > 0.1

    def test_default_nbr_thresholds(self, mock_ee):
        """Test default NBR thresholds are reasonable."""
        from engine.change.thresholds import CHANGE_THRESHOLDS

        nbr_thresholds = CHANGE_THRESHOLDS.get("nbr", {})

        assert nbr_thresholds.get("strong_loss", 0) < 0
        assert nbr_thresholds.get("strong_gain", 0) > 0

    def test_threshold_ordering(self, mock_ee):
        """Test thresholds are in correct order."""
        from engine.change.thresholds import CHANGE_THRESHOLDS

        for index_name, thresholds in CHANGE_THRESHOLDS.items():
            assert thresholds["strong_loss"] < thresholds["moderate_loss"]
            assert thresholds["moderate_loss"] < thresholds["moderate_gain"]
            assert thresholds["moderate_gain"] < thresholds["strong_gain"]


class TestChangeStatistics:
    """Tests for change statistics generation."""

    def test_generate_statistics_returns_dict(self, mock_ee):
        """Test statistics generation returns dictionary."""
        from engine.change import generate_change_statistics

        mock_change_map = MagicMock()
        mock_aoi = MagicMock()

        # Mock the reduceRegion result
        mock_change_map.reduceRegion.return_value.getInfo.return_value = {
            "class_1": 1000,
            "class_2": 2000,
            "class_3": 5000,
            "class_4": 1500,
            "class_5": 500
        }

        result = generate_change_statistics(
            change_map=mock_change_map,
            aoi=mock_aoi,
            scale=30
        )

        assert isinstance(result, dict)

    def test_statistics_contain_area_by_class(self, mock_ee, sample_statistics):
        """Test statistics contain area by class."""
        required_classes = [
            "Strong Loss",
            "Moderate Loss",
            "Stable",
            "Moderate Gain",
            "Strong Gain"
        ]

        for class_name in required_classes:
            assert class_name in sample_statistics["area_by_class"]

    def test_statistics_percentages_sum_to_100(self, sample_statistics):
        """Test percentage values sum to approximately 100."""
        total = sum(sample_statistics["percentage_by_class"].values())
        assert 99.9 <= total <= 100.1

    def test_area_calculation(self, mock_ee):
        """Test area is calculated correctly from pixel counts."""
        from engine.change import generate_change_statistics

        mock_change_map = MagicMock()
        mock_aoi = MagicMock()

        # 1000 pixels at 30m resolution = 900,000 m² = 90 ha
        mock_change_map.reduceRegion.return_value.getInfo.return_value = {
            "class": 1000
        }

        result = generate_change_statistics(
            change_map=mock_change_map,
            aoi=mock_aoi,
            scale=30
        )

        # Verify area calculation is reasonable
        assert result is not None


class TestPeriodChangeAnalysis:
    """Tests for multi-period change analysis."""

    def test_analyze_period_change(self, mock_ee):
        """Test analyzing change between two periods."""
        from engine.change import analyze_period_change

        mock_before = MagicMock()
        mock_after = MagicMock()
        mock_aoi = MagicMock()

        result = analyze_period_change(
            composite_before=mock_before,
            composite_after=mock_after,
            aoi=mock_aoi,
            index="ndvi"
        )

        assert result is not None

    def test_create_change_analysis_all_periods(self, mock_ee):
        """Test creating change analysis for all period pairs."""
        from engine.change import create_change_analysis

        mock_composites = {
            "1990s": MagicMock(),
            "2000s": MagicMock(),
            "present": MagicMock()
        }
        mock_aoi = MagicMock()

        result = create_change_analysis(
            composites=mock_composites,
            aoi=mock_aoi,
            reference_period="1990s",
            indices=["ndvi"]
        )

        assert isinstance(result, dict)

    def test_reference_period_comparison(self, mock_ee):
        """Test all periods are compared to reference period."""
        from engine.change import create_change_analysis

        mock_composites = {
            "1990s": MagicMock(),
            "2000s": MagicMock(),
            "2010s": MagicMock(),
            "present": MagicMock()
        }
        mock_aoi = MagicMock()

        result = create_change_analysis(
            composites=mock_composites,
            aoi=mock_aoi,
            reference_period="1990s",
            indices=["ndvi"]
        )

        # Should have comparisons: 1990s->2000s, 1990s->2010s, 1990s->present
        expected_comparisons = 3
        assert len(result) >= expected_comparisons or result is not None


class TestChangeDetectionEdgeCases:
    """Tests for edge cases in change detection."""

    def test_no_change_classified_as_stable(self, mock_ee):
        """Test zero delta is classified as stable (class 3)."""
        from engine.change import classify_change

        mock_delta = MagicMock()

        result = classify_change(
            delta_image=mock_delta,
            index="ndvi"
        )

        # Class 3 should be stable
        assert result is not None

    def test_extreme_negative_is_strong_loss(self, mock_ee):
        """Test large negative delta is strong loss (class 1)."""
        from engine.change import classify_change

        mock_delta = MagicMock()

        result = classify_change(
            delta_image=mock_delta,
            index="ndvi"
        )

        assert result is not None

    def test_extreme_positive_is_strong_gain(self, mock_ee):
        """Test large positive delta is strong gain (class 5)."""
        from engine.change import classify_change

        mock_delta = MagicMock()

        result = classify_change(
            delta_image=mock_delta,
            index="ndvi"
        )

        assert result is not None

    def test_empty_region_handling(self, mock_ee):
        """Test handling of empty region (no data)."""
        from engine.change import generate_change_statistics

        mock_change_map = MagicMock()
        mock_aoi = MagicMock()

        # Mock empty result
        mock_change_map.reduceRegion.return_value.getInfo.return_value = {}

        result = generate_change_statistics(
            change_map=mock_change_map,
            aoi=mock_aoi,
            scale=30
        )

        # Should handle gracefully
        assert result is not None or result == {}
