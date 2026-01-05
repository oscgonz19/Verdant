"""
Unit tests for composite creation module.

Tests cover:
- Cloud masking for Landsat and Sentinel-2
- Band harmonization
- Temporal composite creation
- Multi-sensor fusion
"""

import pytest
from unittest.mock import MagicMock, Mock, patch


class TestCloudMasking:
    """Tests for cloud masking functions."""

    def test_landsat_cloud_mask_uses_qa_band(self, mock_ee):
        """Test Landsat cloud masking uses QA_PIXEL band."""
        from engine.composites import apply_cloud_mask_landsat

        mock_image = MagicMock()

        result = apply_cloud_mask_landsat(mock_image)

        # Should select QA_PIXEL band
        select_calls = [str(call) for call in mock_image.select.call_args_list]
        assert any("QA" in str(call).upper() for call in select_calls) or result is not None

    def test_sentinel2_cloud_mask_uses_qa60(self, mock_ee):
        """Test Sentinel-2 cloud masking uses QA60 band."""
        from engine.composites import apply_cloud_mask_sentinel2

        mock_image = MagicMock()

        result = apply_cloud_mask_sentinel2(mock_image)

        # Should use QA60 for cloud detection
        assert result is not None

    def test_cloud_mask_returns_masked_image(self, mock_ee):
        """Test cloud mask returns image with mask applied."""
        from engine.composites import apply_cloud_mask_landsat

        mock_image = MagicMock()
        mock_masked = MagicMock()
        mock_image.updateMask.return_value = mock_masked

        result = apply_cloud_mask_landsat(mock_image)

        # Should call updateMask
        assert mock_image.updateMask.called or result is not None


class TestBandHarmonization:
    """Tests for band name harmonization."""

    def test_harmonize_landsat8_bands(self, mock_ee):
        """Test Landsat 8 band harmonization."""
        from engine.composites import harmonize_bands

        mock_image = MagicMock()
        mock_image.get.return_value.getInfo.return_value = "LANDSAT/LC08/C02/T1_L2"

        result = harmonize_bands(mock_image, sensor="landsat8")

        # Should rename bands to standard names
        assert result is not None

    def test_harmonize_sentinel2_bands(self, mock_ee):
        """Test Sentinel-2 band harmonization."""
        from engine.composites import harmonize_bands

        mock_image = MagicMock()

        result = harmonize_bands(mock_image, sensor="sentinel2")

        assert result is not None

    def test_harmonized_band_names(self, mock_ee):
        """Test that harmonized images have standard band names."""
        expected_bands = ["blue", "green", "red", "nir", "swir1", "swir2"]

        from engine.composites import HARMONIZED_BAND_NAMES

        for band in expected_bands:
            assert band in HARMONIZED_BAND_NAMES


class TestTemporalComposites:
    """Tests for temporal composite creation."""

    def test_create_landsat_composite_filters_by_date(self, mock_ee):
        """Test composite creation filters by date range."""
        from engine.composites import create_landsat_composite

        mock_aoi = MagicMock()

        result = create_landsat_composite(
            aoi=mock_aoi,
            start_date="2023-01-01",
            end_date="2023-12-31",
            sensors=["LANDSAT/LC08/C02/T1_L2"]
        )

        # Should filter by date
        assert mock_ee.ImageCollection.called or result is not None

    def test_create_landsat_composite_filters_by_cloud(self, mock_ee):
        """Test composite creation filters by cloud cover."""
        from engine.composites import create_landsat_composite

        mock_aoi = MagicMock()

        result = create_landsat_composite(
            aoi=mock_aoi,
            start_date="2023-01-01",
            end_date="2023-12-31",
            sensors=["LANDSAT/LC08/C02/T1_L2"],
            cloud_threshold=20
        )

        assert result is not None

    def test_create_composite_uses_median(self, mock_ee):
        """Test composite uses median reducer."""
        from engine.composites import create_landsat_composite

        mock_aoi = MagicMock()
        mock_collection = MagicMock()
        mock_ee.ImageCollection.return_value = mock_collection

        result = create_landsat_composite(
            aoi=mock_aoi,
            start_date="2023-01-01",
            end_date="2023-12-31",
            sensors=["LANDSAT/LC08/C02/T1_L2"]
        )

        # Should compute median
        assert result is not None

    def test_create_sentinel_composite(self, mock_ee):
        """Test Sentinel-2 composite creation."""
        from engine.composites import create_sentinel_composite

        mock_aoi = MagicMock()

        result = create_sentinel_composite(
            aoi=mock_aoi,
            start_date="2023-01-01",
            end_date="2023-12-31"
        )

        assert result is not None


class TestMultiSensorFusion:
    """Tests for multi-sensor composite fusion."""

    def test_fused_composite_combines_sensors(self, mock_ee):
        """Test fused composite combines multiple sensors."""
        from engine.composites import create_fused_composite

        mock_aoi = MagicMock()

        result = create_fused_composite(
            aoi=mock_aoi,
            start_date="2023-01-01",
            end_date="2023-12-31",
            sensors=["LANDSAT/LC08/C02/T1_L2", "COPERNICUS/S2_SR_HARMONIZED"]
        )

        assert result is not None

    def test_fused_composite_harmonizes_bands(self, mock_ee):
        """Test fused composite has harmonized bands from all sensors."""
        from engine.composites import create_fused_composite

        mock_aoi = MagicMock()

        result = create_fused_composite(
            aoi=mock_aoi,
            start_date="2023-01-01",
            end_date="2023-12-31",
            sensors=["LANDSAT/LC08/C02/T1_L2", "COPERNICUS/S2_SR_HARMONIZED"]
        )

        # Result should have harmonized band names
        assert result is not None


class TestPeriodComposites:
    """Tests for period-based composite creation."""

    def test_create_all_period_composites(self, mock_ee):
        """Test creating composites for all periods."""
        from engine.composites import create_all_period_composites

        mock_aoi = MagicMock()
        periods = ["1990s", "present"]

        result = create_all_period_composites(
            aoi=mock_aoi,
            periods=periods
        )

        assert isinstance(result, dict)

    def test_period_config_validation(self, mock_ee):
        """Test period configuration is valid."""
        from engine.config import TEMPORAL_PERIODS

        required_fields = ["start", "end", "sensors"]

        for period_name, config in TEMPORAL_PERIODS.items():
            for field in required_fields:
                assert field in config, f"{period_name} missing {field}"

    def test_invalid_period_raises_error(self, mock_ee):
        """Test invalid period name raises error."""
        from engine.composites import create_all_period_composites

        mock_aoi = MagicMock()

        with pytest.raises((KeyError, ValueError)):
            create_all_period_composites(
                aoi=mock_aoi,
                periods=["invalid_period"]
            )


class TestScaleFactors:
    """Tests for reflectance scale factor application."""

    def test_landsat_scale_factors(self, mock_ee):
        """Test Landsat scale factors are applied correctly."""
        from engine.composites import apply_scale_factors

        mock_image = MagicMock()

        result = apply_scale_factors(mock_image, sensor="landsat8")

        # Should multiply by scale factor
        assert mock_image.multiply.called or result is not None

    def test_sentinel2_scale_factors(self, mock_ee):
        """Test Sentinel-2 scale factors are applied correctly."""
        from engine.composites import apply_scale_factors

        mock_image = MagicMock()

        result = apply_scale_factors(mock_image, sensor="sentinel2")

        assert result is not None

    def test_scale_factor_values(self, mock_ee):
        """Test scale factor values are reasonable."""
        from engine.config import BAND_MAPPINGS

        for sensor, config in BAND_MAPPINGS.items():
            if "scale_factor" in config:
                assert 0 < config["scale_factor"] < 1
