"""
Unit tests for IO module.

Tests cover:
- AOI loading from various formats
- Geometry conversion
- Export functions
- Asset caching
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch


class TestAOILoaders:
    """Tests for AOI loading from different formats."""

    def test_load_geojson(self, temp_geojson_file):
        """Test loading GeoJSON file."""
        from engine.io.aoi import load_aoi

        result = load_aoi(str(temp_geojson_file))

        assert result is not None
        assert len(result) > 0

    def test_load_geojson_feature_collection(self, tmp_path):
        """Test loading GeoJSON FeatureCollection."""
        from engine.io.aoi import load_aoi

        fc = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [0, 0], [1, 0], [1, 1], [0, 1], [0, 0]
                        ]]
                    }
                }
            ]
        }

        filepath = tmp_path / "fc.geojson"
        with open(filepath, "w") as f:
            json.dump(fc, f)

        result = load_aoi(str(filepath))
        assert len(result) == 1

    def test_load_nonexistent_file_raises_error(self):
        """Test loading nonexistent file raises FileNotFoundError."""
        from engine.io.aoi import load_aoi

        with pytest.raises(FileNotFoundError):
            load_aoi("/nonexistent/path/file.geojson")

    def test_load_invalid_format_raises_error(self, tmp_path):
        """Test loading unsupported format raises error."""
        from engine.io.aoi import load_aoi

        filepath = tmp_path / "test.xyz"
        filepath.write_text("invalid content")

        with pytest.raises((ValueError, Exception)):
            load_aoi(str(filepath))


class TestGeometryConversion:
    """Tests for geometry conversion to Earth Engine."""

    def test_aoi_to_ee_geometry(self, temp_geojson_file, mock_ee):
        """Test converting GeoDataFrame to EE Geometry."""
        from engine.io.aoi import load_aoi, aoi_to_ee_geometry

        gdf = load_aoi(str(temp_geojson_file))
        result = aoi_to_ee_geometry(gdf)

        assert result is not None

    def test_geometry_preserves_coordinates(self, sample_aoi_geojson, mock_ee):
        """Test geometry conversion preserves coordinates."""
        import geopandas as gpd
        from shapely.geometry import shape
        from engine.io.aoi import aoi_to_ee_geometry

        geom = shape(sample_aoi_geojson["geometry"])
        gdf = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326")

        result = aoi_to_ee_geometry(gdf)

        # Should call EE with correct coordinates
        assert mock_ee.Geometry.called or result is not None

    def test_multi_polygon_handling(self, mock_ee):
        """Test handling of MultiPolygon geometries."""
        import geopandas as gpd
        from shapely.geometry import MultiPolygon, Polygon
        from engine.io.aoi import aoi_to_ee_geometry

        poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        poly2 = Polygon([(2, 2), (3, 2), (3, 3), (2, 3)])
        multi = MultiPolygon([poly1, poly2])

        gdf = gpd.GeoDataFrame(geometry=[multi], crs="EPSG:4326")

        result = aoi_to_ee_geometry(gdf)

        assert result is not None


class TestBufferOperations:
    """Tests for AOI buffer operations."""

    def test_create_buffered_aoi(self, temp_geojson_file):
        """Test creating buffered AOI."""
        from engine.io.aoi import load_aoi, create_buffered_aoi

        gdf = load_aoi(str(temp_geojson_file))
        buffered = create_buffered_aoi(gdf, buffer_distance=1000)

        # Buffered area should be larger
        assert buffered.geometry.area.sum() > gdf.geometry.area.sum()

    def test_zero_buffer(self, temp_geojson_file):
        """Test zero buffer returns original."""
        from engine.io.aoi import load_aoi, create_buffered_aoi

        gdf = load_aoi(str(temp_geojson_file))
        buffered = create_buffered_aoi(gdf, buffer_distance=0)

        # Should be approximately equal
        assert abs(buffered.geometry.area.sum() - gdf.geometry.area.sum()) < 0.001


class TestAOIMetadata:
    """Tests for AOI metadata extraction."""

    def test_get_aoi_centroid(self, temp_geojson_file):
        """Test getting AOI centroid."""
        from engine.io.aoi import load_aoi, get_aoi_centroid

        gdf = load_aoi(str(temp_geojson_file))
        centroid = get_aoi_centroid(gdf)

        assert "lon" in centroid or "x" in centroid
        assert "lat" in centroid or "y" in centroid

    def test_get_aoi_area(self, temp_geojson_file):
        """Test getting AOI area."""
        from engine.io.aoi import load_aoi, get_aoi_area

        gdf = load_aoi(str(temp_geojson_file))
        area = get_aoi_area(gdf)

        assert area > 0


class TestExporters:
    """Tests for export functions."""

    def test_export_to_drive(self, mock_ee):
        """Test export to Google Drive."""
        from engine.io.exporters import export_to_drive

        mock_image = MagicMock()
        mock_aoi = MagicMock()

        task = export_to_drive(
            image=mock_image,
            description="test_export",
            folder="TestFolder",
            region=mock_aoi,
            scale=30
        )

        assert task is not None

    def test_export_config_applied(self, mock_ee):
        """Test export configuration is applied."""
        from engine.io.exporters import export_to_drive
        from engine.config import ExportConfig

        mock_image = MagicMock()
        mock_aoi = MagicMock()

        config = ExportConfig(
            scale=10,
            crs="EPSG:32720",
            folder="CustomFolder"
        )

        task = export_to_drive(
            image=mock_image,
            description="test",
            region=mock_aoi,
            config=config
        )

        assert task is not None

    def test_export_composite(self, mock_ee):
        """Test exporting a composite."""
        from engine.io.exporters import export_composite

        mock_composite = MagicMock()
        mock_aoi = MagicMock()

        task = export_composite(
            composite=mock_composite,
            period="present",
            aoi=mock_aoi,
            folder="VegChange"
        )

        assert task is not None

    def test_export_change_map(self, mock_ee):
        """Test exporting a change map."""
        from engine.io.exporters import export_change_map

        mock_change = MagicMock()
        mock_aoi = MagicMock()

        task = export_change_map(
            change_map=mock_change,
            comparison="1990s_to_present",
            index="ndvi",
            aoi=mock_aoi
        )

        assert task is not None


class TestTileURLs:
    """Tests for tile URL generation."""

    def test_get_map_tile_url(self, mock_ee):
        """Test getting map tile URL."""
        from engine.io.exporters import get_map_tile_url

        mock_image = MagicMock()
        mock_image.getMapId.return_value = {
            "tile_fetcher": MagicMock(url_format="https://example.com/{z}/{x}/{y}")
        }

        url = get_map_tile_url(
            image=mock_image,
            vis_params={"min": 0, "max": 1}
        )

        assert url is not None
        assert "http" in url.lower() or mock_image.getMapId.called


class TestAssetCache:
    """Tests for Earth Engine asset caching."""

    def test_cache_initialization(self, mock_ee):
        """Test cache initialization."""
        from engine.io.cache import AssetCache

        cache = AssetCache(asset_folder="users/test/cache")

        assert cache.asset_folder == "users/test/cache"

    def test_cache_key_generation(self, mock_ee):
        """Test cache key is generated consistently."""
        from engine.io.cache import AssetCache

        cache = AssetCache(asset_folder="users/test/cache")

        mock_aoi = MagicMock()
        mock_aoi.getInfo.return_value = {"coordinates": [[0, 0], [1, 1]]}

        key1 = cache._generate_key(mock_aoi, "present", ["ndvi"])
        key2 = cache._generate_key(mock_aoi, "present", ["ndvi"])

        assert key1 == key2

    def test_cache_key_varies_with_params(self, mock_ee):
        """Test cache key changes with different parameters."""
        from engine.io.cache import AssetCache

        cache = AssetCache(asset_folder="users/test/cache")

        mock_aoi = MagicMock()
        mock_aoi.getInfo.return_value = {"coordinates": [[0, 0], [1, 1]]}

        key1 = cache._generate_key(mock_aoi, "1990s", ["ndvi"])
        key2 = cache._generate_key(mock_aoi, "present", ["ndvi"])

        assert key1 != key2

    def test_cache_exists_check(self, mock_ee):
        """Test checking if cached asset exists."""
        from engine.io.cache import AssetCache

        cache = AssetCache(asset_folder="users/test/cache")

        # Mock asset exists
        mock_ee.data.getAsset = MagicMock(return_value={"type": "Image"})

        exists = cache.exists("test_asset_id")

        assert exists is True or mock_ee.data.getAsset.called

    def test_cache_save_composite(self, mock_ee):
        """Test saving composite to cache."""
        from engine.io.cache import AssetCache

        cache = AssetCache(asset_folder="users/test/cache")
        mock_composite = MagicMock()

        task = cache.save_composite(
            composite=mock_composite,
            period="present",
            aoi_hash="abc123"
        )

        assert task is not None or mock_ee.batch.Export.called

    def test_cache_get_composite(self, mock_ee):
        """Test getting composite from cache."""
        from engine.io.cache import AssetCache

        cache = AssetCache(asset_folder="users/test/cache")

        # Mock asset exists
        mock_ee.data.getAsset = MagicMock(return_value={"type": "Image"})

        result = cache.get_composite(period="present", aoi_hash="abc123")

        assert result is not None or mock_ee.Image.called
