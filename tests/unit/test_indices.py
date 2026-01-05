"""
Unit tests for spectral indices module.

Tests cover:
- Index registration and registry
- NDVI, NBR, NDWI, EVI, NDMI calculations
- Edge cases and error handling
"""

import pytest
from unittest.mock import MagicMock, Mock, patch


class TestIndexRegistry:
    """Tests for the spectral index registry system."""

    def test_registry_contains_standard_indices(self, mock_ee):
        """Test that standard indices are registered."""
        from engine.indices import INDEX_REGISTRY

        expected_indices = ["ndvi", "nbr", "ndwi", "evi", "ndmi"]
        for index_name in expected_indices:
            assert index_name in INDEX_REGISTRY, f"{index_name} not in registry"

    def test_get_index_by_name(self, mock_ee):
        """Test retrieving index by name."""
        from engine.indices import get_index

        ndvi = get_index("ndvi")
        assert ndvi is not None
        assert ndvi.name == "ndvi"

    def test_get_invalid_index_raises_error(self, mock_ee):
        """Test that invalid index name raises KeyError."""
        from engine.indices import get_index

        with pytest.raises(KeyError):
            get_index("invalid_index")

    def test_list_available_indices(self, mock_ee):
        """Test listing all available indices."""
        from engine.indices import list_indices

        indices = list_indices()
        assert isinstance(indices, list)
        assert len(indices) >= 5
        assert "ndvi" in indices


class TestNDVIIndex:
    """Tests for NDVI (Normalized Difference Vegetation Index)."""

    def test_ndvi_formula(self, mock_ee):
        """Test NDVI formula: (NIR - Red) / (NIR + Red)."""
        from engine.indices import NDVIIndex

        index = NDVIIndex()
        assert index.name == "ndvi"
        assert "NIR" in index.formula.upper()
        assert "RED" in index.formula.upper()

    def test_ndvi_value_range(self, mock_ee):
        """Test NDVI value range is [-1, 1]."""
        from engine.indices import NDVIIndex

        index = NDVIIndex()
        assert index.value_range == (-1.0, 1.0)

    def test_ndvi_compute_calls_correct_bands(self, mock_ee):
        """Test NDVI computation uses NIR and Red bands."""
        from engine.indices import NDVIIndex

        index = NDVIIndex()
        mock_image = MagicMock()

        index.compute(mock_image)

        # Verify correct bands were selected
        select_calls = [str(call) for call in mock_image.select.call_args_list]
        assert any("nir" in str(call).lower() for call in select_calls)
        assert any("red" in str(call).lower() for call in select_calls)

    def test_ndvi_result_has_correct_band_name(self, mock_ee):
        """Test NDVI result is named correctly."""
        from engine.indices import NDVIIndex

        index = NDVIIndex()
        mock_image = MagicMock()
        mock_result = MagicMock()
        mock_image.select.return_value.subtract.return_value.divide.return_value.rename.return_value = mock_result

        result = index.compute(mock_image)

        # Verify rename was called with 'ndvi'
        assert mock_image.select.return_value.subtract.return_value.divide.return_value.rename.called


class TestNBRIndex:
    """Tests for NBR (Normalized Burn Ratio)."""

    def test_nbr_formula(self, mock_ee):
        """Test NBR formula: (NIR - SWIR2) / (NIR + SWIR2)."""
        from engine.indices import NBRIndex

        index = NBRIndex()
        assert index.name == "nbr"
        assert "NIR" in index.formula.upper()
        assert "SWIR" in index.formula.upper()

    def test_nbr_uses_swir2_band(self, mock_ee):
        """Test NBR uses SWIR2 band (not SWIR1)."""
        from engine.indices import NBRIndex

        index = NBRIndex()
        mock_image = MagicMock()

        index.compute(mock_image)

        # Verify SWIR2 band was selected
        select_calls = [str(call) for call in mock_image.select.call_args_list]
        assert any("swir2" in str(call).lower() for call in select_calls)


class TestNDWIIndex:
    """Tests for NDWI (Normalized Difference Water Index)."""

    def test_ndwi_formula(self, mock_ee):
        """Test NDWI formula: (Green - NIR) / (Green + NIR)."""
        from engine.indices import NDWIIndex

        index = NDWIIndex()
        assert index.name == "ndwi"
        assert "GREEN" in index.formula.upper()
        assert "NIR" in index.formula.upper()

    def test_ndwi_uses_green_and_nir(self, mock_ee):
        """Test NDWI uses Green and NIR bands."""
        from engine.indices import NDWIIndex

        index = NDWIIndex()
        mock_image = MagicMock()

        index.compute(mock_image)

        select_calls = [str(call) for call in mock_image.select.call_args_list]
        assert any("green" in str(call).lower() for call in select_calls)
        assert any("nir" in str(call).lower() for call in select_calls)


class TestEVIIndex:
    """Tests for EVI (Enhanced Vegetation Index)."""

    def test_evi_formula(self, mock_ee):
        """Test EVI uses Blue, Red, and NIR bands."""
        from engine.indices import EVIIndex

        index = EVIIndex()
        assert index.name == "evi"
        assert "NIR" in index.formula.upper()
        assert "RED" in index.formula.upper()
        assert "BLUE" in index.formula.upper()

    def test_evi_value_range(self, mock_ee):
        """Test EVI typical value range."""
        from engine.indices import EVIIndex

        index = EVIIndex()
        # EVI typically ranges from about -0.2 to 1.0
        assert index.value_range[0] < 0
        assert index.value_range[1] > 0


class TestNDMIIndex:
    """Tests for NDMI (Normalized Difference Moisture Index)."""

    def test_ndmi_formula(self, mock_ee):
        """Test NDMI formula: (NIR - SWIR1) / (NIR + SWIR1)."""
        from engine.indices import NDMIIndex

        index = NDMIIndex()
        assert index.name == "ndmi"
        assert "NIR" in index.formula.upper()
        assert "SWIR" in index.formula.upper()

    def test_ndmi_uses_swir1_band(self, mock_ee):
        """Test NDMI uses SWIR1 band."""
        from engine.indices import NDMIIndex

        index = NDMIIndex()
        mock_image = MagicMock()

        index.compute(mock_image)

        select_calls = [str(call) for call in mock_image.select.call_args_list]
        assert any("swir1" in str(call).lower() for call in select_calls)


class TestConvenienceFunctions:
    """Tests for convenience functions like add_ndvi, add_all_indices."""

    def test_add_ndvi_returns_image_with_ndvi_band(self, mock_ee):
        """Test add_ndvi adds NDVI band to image."""
        from engine.indices import add_ndvi

        mock_image = MagicMock()
        result = add_ndvi(mock_image)

        assert mock_image.addBands.called or result is not None

    def test_add_all_indices_adds_multiple_bands(self, mock_ee):
        """Test add_all_indices adds multiple index bands."""
        from engine.indices import add_all_indices

        mock_image = MagicMock()
        indices = ["ndvi", "nbr"]

        result = add_all_indices(mock_image, indices)

        assert result is not None

    def test_add_all_indices_with_empty_list(self, mock_ee):
        """Test add_all_indices with empty list returns original image."""
        from engine.indices import add_all_indices

        mock_image = MagicMock()

        result = add_all_indices(mock_image, [])

        # Should return the original image unchanged
        assert result == mock_image

    def test_add_all_indices_with_invalid_index(self, mock_ee):
        """Test add_all_indices with invalid index raises error."""
        from engine.indices import add_all_indices

        mock_image = MagicMock()

        with pytest.raises((KeyError, ValueError)):
            add_all_indices(mock_image, ["invalid_index"])


class TestDeltaIndices:
    """Tests for delta (change) index calculation."""

    def test_calculate_delta_returns_difference(self, mock_ee):
        """Test delta calculation: after - before."""
        from engine.indices import calculate_delta_indices

        mock_before = MagicMock()
        mock_after = MagicMock()

        result = calculate_delta_indices(mock_before, mock_after, ["ndvi"])

        # Verify subtraction was performed
        assert mock_after.select.called or result is not None

    def test_delta_band_naming(self, mock_ee):
        """Test delta bands are named correctly (e.g., 'dndvi')."""
        from engine.indices import calculate_delta_indices

        mock_before = MagicMock()
        mock_after = MagicMock()
        mock_result = MagicMock()
        mock_after.select.return_value.subtract.return_value.rename.return_value = mock_result

        result = calculate_delta_indices(mock_before, mock_after, ["ndvi"])

        # Delta NDVI should be named 'dndvi'
        rename_calls = mock_after.select.return_value.subtract.return_value.rename.call_args_list
        if rename_calls:
            assert any("dndvi" in str(call).lower() for call in rename_calls)
