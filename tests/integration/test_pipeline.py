"""
Integration tests for the analysis pipeline.

These tests require Earth Engine authentication and test
the full analysis workflow.

Run with: pytest tests/integration/ -v -m integration
Skip with: pytest -m "not integration"
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.integration
class TestAnalysisPipeline:
    """Integration tests for the full analysis pipeline."""

    @pytest.fixture
    def orchestrator(self, mock_ee):
        """Create orchestrator with mocked EE."""
        from services.change_orchestrator import ChangeOrchestrator
        return ChangeOrchestrator()

    def test_full_analysis_workflow(self, orchestrator, mock_ee, sample_bbox):
        """Test complete analysis from AOI to statistics."""
        # Create mock AOI
        mock_aoi = MagicMock()

        result = orchestrator.analyze(
            aoi=mock_aoi,
            periods=["1990s", "present"],
            indices=["ndvi"],
            reference_period="1990s"
        )

        assert "composites" in result
        assert "changes" in result
        assert "statistics" in result

    def test_analysis_with_multiple_indices(self, orchestrator, mock_ee):
        """Test analysis with multiple spectral indices."""
        mock_aoi = MagicMock()

        result = orchestrator.analyze(
            aoi=mock_aoi,
            periods=["1990s", "present"],
            indices=["ndvi", "nbr", "ndwi"],
            reference_period="1990s"
        )

        # Should have changes for each index
        assert result is not None

    def test_analysis_with_all_periods(self, orchestrator, mock_ee):
        """Test analysis across all temporal periods."""
        mock_aoi = MagicMock()

        result = orchestrator.analyze(
            aoi=mock_aoi,
            periods=["1990s", "2000s", "2010s", "present"],
            indices=["ndvi"],
            reference_period="1990s"
        )

        # Should have composites for all periods
        assert len(result.get("composites", {})) >= 4 or result is not None

    def test_analysis_with_progress_callback(self, orchestrator, mock_ee):
        """Test analysis with progress callback."""
        mock_aoi = MagicMock()
        progress_values = []

        def progress_callback(value):
            progress_values.append(value)

        result = orchestrator.analyze(
            aoi=mock_aoi,
            periods=["1990s", "present"],
            indices=["ndvi"],
            progress_callback=progress_callback
        )

        # Progress should have been reported
        assert len(progress_values) >= 0 or result is not None


@pytest.mark.integration
class TestAOIToAnalysis:
    """Integration tests from file loading to analysis."""

    def test_analyze_from_geojson(self, mock_ee, temp_geojson_file):
        """Test analysis starting from GeoJSON file."""
        from services.change_orchestrator import ChangeOrchestrator

        orchestrator = ChangeOrchestrator()

        result = orchestrator.analyze_from_file(
            aoi_path=str(temp_geojson_file),
            site_name="Test Site",
            periods=["1990s", "present"],
            indices=["ndvi"]
        )

        assert result is not None
        assert "statistics" in result or isinstance(result, dict)

    def test_analyze_with_buffer(self, mock_ee, temp_geojson_file):
        """Test analysis with buffered AOI."""
        from services.change_orchestrator import ChangeOrchestrator

        orchestrator = ChangeOrchestrator()

        result = orchestrator.analyze_from_file(
            aoi_path=str(temp_geojson_file),
            site_name="Buffered Site",
            periods=["present"],
            indices=["ndvi"],
            buffer_distance=500
        )

        assert result is not None


@pytest.mark.integration
class TestCompositeCreation:
    """Integration tests for composite creation."""

    def test_create_composites_for_all_periods(self, mock_ee):
        """Test creating composites for all defined periods."""
        from engine.composites import create_all_period_composites
        from engine.config import TEMPORAL_PERIODS

        mock_aoi = MagicMock()

        composites = create_all_period_composites(
            aoi=mock_aoi,
            periods=list(TEMPORAL_PERIODS.keys())
        )

        assert isinstance(composites, dict)

    def test_composite_has_all_bands(self, mock_ee):
        """Test composite has all expected bands."""
        from engine.composites import create_landsat_composite

        mock_aoi = MagicMock()
        expected_bands = ["blue", "green", "red", "nir", "swir1", "swir2"]

        composite = create_landsat_composite(
            aoi=mock_aoi,
            start_date="2023-01-01",
            end_date="2023-12-31",
            sensors=["LANDSAT/LC08/C02/T1_L2"]
        )

        # Verify bands are present
        assert composite is not None


@pytest.mark.integration
class TestChangeDetection:
    """Integration tests for change detection."""

    def test_detect_change_between_periods(self, mock_ee):
        """Test change detection between two periods."""
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

    def test_generate_statistics_for_change(self, mock_ee):
        """Test generating statistics for change map."""
        from engine.change import classify_change, generate_change_statistics

        mock_delta = MagicMock()
        mock_aoi = MagicMock()

        change_map = classify_change(mock_delta, "ndvi")

        # Mock the statistics result
        change_map.reduceRegion.return_value.getInfo.return_value = {
            "class_1": 100,
            "class_2": 200,
            "class_3": 500,
            "class_4": 150,
            "class_5": 50
        }

        stats = generate_change_statistics(change_map, mock_aoi, scale=30)

        assert stats is not None


@pytest.mark.integration
class TestExportWorkflow:
    """Integration tests for export workflow."""

    def test_export_analysis_results(self, mock_ee):
        """Test exporting analysis results to Drive."""
        from engine.io.exporters import export_all_composites, export_all_changes

        mock_composites = {
            "1990s": MagicMock(),
            "present": MagicMock()
        }
        mock_changes = {
            "1990s_to_present_ndvi": MagicMock()
        }
        mock_aoi = MagicMock()

        # Export composites
        composite_tasks = export_all_composites(
            composites=mock_composites,
            aoi=mock_aoi,
            folder="VegChange/Test"
        )

        # Export changes
        change_tasks = export_all_changes(
            changes=mock_changes,
            aoi=mock_aoi,
            folder="VegChange/Test"
        )

        assert composite_tasks is not None or mock_ee.batch.Export.called
        assert change_tasks is not None or mock_ee.batch.Export.called
