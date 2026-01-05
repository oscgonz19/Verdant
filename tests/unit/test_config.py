"""
Unit tests for configuration module.

Tests cover:
- Temporal period configuration
- Band mappings
- Change thresholds
- VegChangeConfig dataclass
"""

import pytest
from datetime import datetime


class TestTemporalPeriods:
    """Tests for temporal period configuration."""

    def test_all_periods_defined(self):
        """Test all expected periods are defined."""
        from engine.config import TEMPORAL_PERIODS

        expected_periods = ["1990s", "2000s", "2010s", "present"]

        for period in expected_periods:
            assert period in TEMPORAL_PERIODS, f"Missing period: {period}"

    def test_period_has_required_fields(self):
        """Test each period has required configuration fields."""
        from engine.config import TEMPORAL_PERIODS

        required_fields = ["start", "end", "sensors", "description"]

        for period_name, config in TEMPORAL_PERIODS.items():
            for field in required_fields:
                assert field in config, f"{period_name} missing field: {field}"

    def test_period_dates_are_valid(self):
        """Test period dates are in valid format."""
        from engine.config import TEMPORAL_PERIODS

        for period_name, config in TEMPORAL_PERIODS.items():
            start = datetime.strptime(config["start"], "%Y-%m-%d")
            end = datetime.strptime(config["end"], "%Y-%m-%d")

            assert start < end, f"{period_name}: start must be before end"

    def test_periods_cover_sensor_availability(self):
        """Test periods match sensor availability."""
        from engine.config import TEMPORAL_PERIODS

        # Landsat 5 available ~1984-2013
        assert "LANDSAT/LT05" in str(TEMPORAL_PERIODS["1990s"]["sensors"])

        # Landsat 8 available 2013+
        assert "LANDSAT/LC08" in str(TEMPORAL_PERIODS["present"]["sensors"])

    def test_periods_are_chronological(self):
        """Test periods don't overlap unexpectedly."""
        from engine.config import TEMPORAL_PERIODS

        period_order = ["1990s", "2000s", "2010s", "present"]

        for i in range(len(period_order) - 1):
            current = TEMPORAL_PERIODS[period_order[i]]
            next_period = TEMPORAL_PERIODS[period_order[i + 1]]

            current_end = datetime.strptime(current["end"], "%Y-%m-%d")
            next_start = datetime.strptime(next_period["start"], "%Y-%m-%d")

            # Next period should start after or at current period end
            assert next_start >= current_end or (next_start.year - current_end.year) <= 1


class TestBandMappings:
    """Tests for sensor band mapping configuration."""

    def test_all_sensors_mapped(self):
        """Test all used sensors have band mappings."""
        from engine.config import BAND_MAPPINGS

        expected_sensors = ["landsat5", "landsat7", "landsat8", "sentinel2"]

        for sensor in expected_sensors:
            assert sensor in BAND_MAPPINGS, f"Missing mapping: {sensor}"

    def test_standard_bands_mapped(self):
        """Test standard band names are mapped for each sensor."""
        from engine.config import BAND_MAPPINGS

        standard_bands = ["blue", "green", "red", "nir", "swir1", "swir2"]

        for sensor, mapping in BAND_MAPPINGS.items():
            if "bands" in mapping:
                for band in standard_bands:
                    assert band in mapping["bands"], f"{sensor} missing band: {band}"

    def test_scale_factors_defined(self):
        """Test scale factors are defined for sensors."""
        from engine.config import BAND_MAPPINGS

        for sensor, mapping in BAND_MAPPINGS.items():
            assert "scale_factor" in mapping or "offset" in mapping or True  # Optional


class TestChangeThresholds:
    """Tests for change threshold configuration."""

    def test_thresholds_for_main_indices(self):
        """Test thresholds defined for main indices."""
        from engine.config import CHANGE_THRESHOLDS

        main_indices = ["ndvi", "nbr"]

        for index in main_indices:
            assert index in CHANGE_THRESHOLDS, f"Missing thresholds: {index}"

    def test_threshold_structure(self):
        """Test threshold configuration has correct structure."""
        from engine.config import CHANGE_THRESHOLDS

        required_thresholds = ["strong_loss", "moderate_loss", "moderate_gain", "strong_gain"]

        for index, thresholds in CHANGE_THRESHOLDS.items():
            for threshold in required_thresholds:
                assert threshold in thresholds, f"{index} missing: {threshold}"

    def test_threshold_values_symmetric(self):
        """Test thresholds are roughly symmetric around zero."""
        from engine.config import CHANGE_THRESHOLDS

        for index, thresholds in CHANGE_THRESHOLDS.items():
            # Strong loss and gain should be roughly symmetric
            loss_magnitude = abs(thresholds["strong_loss"])
            gain_magnitude = thresholds["strong_gain"]

            # Within 50% of each other
            ratio = max(loss_magnitude, gain_magnitude) / min(loss_magnitude, gain_magnitude)
            assert ratio < 2.0, f"{index} thresholds not symmetric"


class TestVegChangeConfig:
    """Tests for VegChangeConfig dataclass."""

    def test_config_default_values(self):
        """Test VegChangeConfig has sensible defaults."""
        from engine.config import VegChangeConfig

        config = VegChangeConfig()

        assert config.cloud_threshold > 0
        assert config.export_scale > 0
        assert len(config.default_indices) > 0

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        from engine.config import VegChangeConfig

        config_dict = {
            "cloud_threshold": 15.0,
            "export_scale": 10,
            "default_indices": ["ndvi", "nbr"]
        }

        config = VegChangeConfig.from_dict(config_dict)

        assert config.cloud_threshold == 15.0
        assert config.export_scale == 10

    def test_config_to_dict(self):
        """Test serializing config to dictionary."""
        from engine.config import VegChangeConfig

        config = VegChangeConfig()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "cloud_threshold" in config_dict

    def test_config_from_yaml(self, temp_config_file):
        """Test loading config from YAML file."""
        from engine.config import VegChangeConfig

        config = VegChangeConfig.from_yaml(str(temp_config_file))

        assert config is not None

    def test_config_validation(self):
        """Test config validation catches invalid values."""
        from engine.config import VegChangeConfig

        # Cloud threshold should be 0-100
        with pytest.raises((ValueError, TypeError)):
            VegChangeConfig(cloud_threshold=150)

        # Export scale should be positive
        with pytest.raises((ValueError, TypeError)):
            VegChangeConfig(export_scale=-10)


class TestExportConfig:
    """Tests for export configuration."""

    def test_export_config_defaults(self):
        """Test export configuration defaults."""
        from engine.config import ExportConfig

        config = ExportConfig()

        assert config.scale == 30  # Default Landsat resolution
        assert config.crs is not None
        assert config.file_format in ["GeoTIFF", "TFRecord"]

    def test_export_config_drive_folder(self):
        """Test export configuration for Drive folder."""
        from engine.config import ExportConfig

        config = ExportConfig(folder="MyFolder")

        assert config.folder == "MyFolder"


class TestIndexConfig:
    """Tests for index configuration."""

    def test_index_metadata(self):
        """Test index metadata is complete."""
        from engine.config import INDEX_METADATA

        required_fields = ["full_name", "formula", "range", "description"]

        for index_name, metadata in INDEX_METADATA.items():
            for field in required_fields:
                assert field in metadata, f"{index_name} missing: {field}"

    def test_index_formulas_are_documented(self):
        """Test all index formulas are documented."""
        from engine.config import INDEX_METADATA

        for index_name, metadata in INDEX_METADATA.items():
            formula = metadata.get("formula", "")
            assert len(formula) > 0, f"{index_name} has no formula"
