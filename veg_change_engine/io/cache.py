"""
Caching module for Earth Engine data persistence.

Strategies to avoid repeated API consumption:
1. EE Asset caching - Save processed composites as reusable assets
2. Local metadata cache - Store tile URLs and computation results
3. Drive export - Download GeoTIFFs for offline analysis

This significantly reduces API calls and speeds up repeated analyses.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta
import json
import hashlib
import ee


# =============================================================================
# EE ASSET CACHING
# =============================================================================

class AssetCache:
    """
    Cache processed images as Earth Engine Assets.

    Assets persist indefinitely and load much faster than recomputing.
    Ideal for composites that don't change frequently.
    """

    def __init__(self, asset_folder: str):
        """
        Initialize asset cache.

        Args:
            asset_folder: EE asset folder path (e.g., 'users/username/veg_change_cache')
        """
        self.asset_folder = asset_folder
        self._ensure_folder_exists()

    def _ensure_folder_exists(self):
        """Create asset folder if it doesn't exist."""
        try:
            ee.data.createAsset(
                {"type": "Folder"},
                self.asset_folder,
            )
        except ee.EEException:
            # Folder already exists
            pass

    def _get_asset_id(self, name: str) -> str:
        """Generate full asset ID."""
        return f"{self.asset_folder}/{name}"

    def _generate_cache_key(
        self,
        aoi: ee.Geometry,
        period: str,
        indices: List[str],
    ) -> str:
        """Generate unique cache key based on parameters."""
        # Hash the geometry and parameters
        aoi_info = aoi.getInfo()
        key_data = json.dumps({
            "aoi": aoi_info,
            "period": period,
            "indices": sorted(indices),
        }, sort_keys=True)

        return hashlib.md5(key_data.encode()).hexdigest()[:12]

    def exists(self, name: str) -> bool:
        """Check if asset exists in cache."""
        asset_id = self._get_asset_id(name)
        try:
            ee.data.getAsset(asset_id)
            return True
        except ee.EEException:
            return False

    def get(self, name: str) -> Optional[ee.Image]:
        """
        Retrieve cached image.

        Args:
            name: Cache key/name

        Returns:
            ee.Image if exists, None otherwise
        """
        asset_id = self._get_asset_id(name)
        try:
            return ee.Image(asset_id)
        except ee.EEException:
            return None

    def put(
        self,
        image: ee.Image,
        name: str,
        region: ee.Geometry,
        scale: int = 30,
        wait: bool = False,
    ) -> ee.batch.Task:
        """
        Store image in cache as EE Asset.

        Args:
            image: ee.Image to cache
            name: Cache key/name
            region: Export region
            scale: Export scale in meters
            wait: Whether to wait for export to complete

        Returns:
            Export task
        """
        asset_id = self._get_asset_id(name)

        task = ee.batch.Export.image.toAsset(
            image=image,
            description=f"cache_{name}",
            assetId=asset_id,
            region=region,
            scale=scale,
            maxPixels=1e13,
        )

        task.start()

        if wait:
            import time
            while task.status()["state"] in ["READY", "RUNNING"]:
                time.sleep(10)

        return task

    def get_or_compute(
        self,
        name: str,
        compute_fn,
        region: ee.Geometry,
        scale: int = 30,
        force_recompute: bool = False,
    ) -> ee.Image:
        """
        Get from cache or compute and cache.

        Args:
            name: Cache key
            compute_fn: Function that returns ee.Image
            region: Export region (for caching)
            scale: Export scale
            force_recompute: Ignore cache and recompute

        Returns:
            ee.Image (from cache or freshly computed)
        """
        if not force_recompute and self.exists(name):
            print(f"  [CACHE HIT] Loading {name} from assets")
            return self.get(name)

        print(f"  [CACHE MISS] Computing {name}...")
        image = compute_fn()

        # Start caching in background
        print(f"  [CACHING] Saving {name} to assets...")
        self.put(image, name, region, scale, wait=False)

        return image

    def list_cached(self) -> List[str]:
        """List all cached assets."""
        try:
            assets = ee.data.listAssets({"parent": self.asset_folder})
            return [a["name"].split("/")[-1] for a in assets.get("assets", [])]
        except ee.EEException:
            return []

    def clear(self, name: Optional[str] = None):
        """
        Clear cache.

        Args:
            name: Specific asset to delete, or None for all
        """
        if name:
            asset_id = self._get_asset_id(name)
            try:
                ee.data.deleteAsset(asset_id)
            except ee.EEException:
                pass
        else:
            for cached_name in self.list_cached():
                self.clear(cached_name)


# =============================================================================
# LOCAL METADATA CACHE
# =============================================================================

class LocalCache:
    """
    Local file-based cache for metadata and tile URLs.

    Caches:
    - Tile URLs (expire after 24h by default)
    - Computation results (statistics, histograms)
    - AOI information
    """

    def __init__(self, cache_dir: str = ".veg_change_cache"):
        """
        Initialize local cache.

        Args:
            cache_dir: Local directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self._load_metadata()

    def _load_metadata(self):
        """Load metadata from file."""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

    def _save_metadata(self):
        """Save metadata to file."""
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2, default=str)

    def _is_expired(self, timestamp: str, ttl_hours: int = 24) -> bool:
        """Check if cached item is expired."""
        cached_time = datetime.fromisoformat(timestamp)
        return datetime.now() - cached_time > timedelta(hours=ttl_hours)

    def get_tile_url(self, key: str, ttl_hours: int = 24) -> Optional[str]:
        """
        Get cached tile URL.

        Args:
            key: Cache key
            ttl_hours: Time-to-live in hours

        Returns:
            Tile URL if cached and not expired, None otherwise
        """
        if key in self.metadata.get("tile_urls", {}):
            entry = self.metadata["tile_urls"][key]
            if not self._is_expired(entry["timestamp"], ttl_hours):
                return entry["url"]
        return None

    def put_tile_url(self, key: str, url: str):
        """
        Cache tile URL.

        Args:
            key: Cache key
            url: Tile URL to cache
        """
        if "tile_urls" not in self.metadata:
            self.metadata["tile_urls"] = {}

        self.metadata["tile_urls"][key] = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
        }
        self._save_metadata()

    def get_statistics(self, key: str) -> Optional[Dict]:
        """Get cached statistics."""
        return self.metadata.get("statistics", {}).get(key)

    def put_statistics(self, key: str, stats: Dict):
        """Cache statistics."""
        if "statistics" not in self.metadata:
            self.metadata["statistics"] = {}

        self.metadata["statistics"][key] = {
            "data": stats,
            "timestamp": datetime.now().isoformat(),
        }
        self._save_metadata()

    def clear(self):
        """Clear all cached data."""
        self.metadata = {}
        self._save_metadata()


# =============================================================================
# CACHED PIPELINE WRAPPER
# =============================================================================

class CachedAnalysis:
    """
    Wrapper for vegetation change analysis with caching.

    Automatically caches composites and change maps to avoid
    recomputing on repeated runs.
    """

    def __init__(
        self,
        asset_folder: str,
        local_cache_dir: str = ".veg_change_cache",
    ):
        """
        Initialize cached analysis.

        Args:
            asset_folder: EE asset folder for persistent cache
            local_cache_dir: Local directory for metadata cache
        """
        self.asset_cache = AssetCache(asset_folder)
        self.local_cache = LocalCache(local_cache_dir)

    def get_composite(
        self,
        aoi: ee.Geometry,
        period: str,
        indices: List[str],
        cloud_threshold: float = 20.0,
        force_recompute: bool = False,
    ) -> ee.Image:
        """
        Get composite with caching.

        Args:
            aoi: Area of interest
            period: Temporal period
            indices: Spectral indices to include
            cloud_threshold: Cloud cover threshold
            force_recompute: Ignore cache

        Returns:
            ee.Image composite with indices
        """
        from veg_change_engine.core.composites import create_fused_composite
        from veg_change_engine.core.indices import add_all_indices
        from veg_change_engine.config import TEMPORAL_PERIODS

        # Generate cache key
        cache_key = f"composite_{period}_{'_'.join(sorted(indices))}"

        def compute():
            period_info = TEMPORAL_PERIODS[period]
            composite = create_fused_composite(
                aoi=aoi,
                start_date=period_info["start"],
                end_date=period_info["end"],
                sensors=period_info["sensors"],
                cloud_threshold=cloud_threshold,
            )
            return add_all_indices(composite, indices)

        return self.asset_cache.get_or_compute(
            name=cache_key,
            compute_fn=compute,
            region=aoi,
            force_recompute=force_recompute,
        )

    def get_change_map(
        self,
        aoi: ee.Geometry,
        before_period: str,
        after_period: str,
        index: str = "ndvi",
        force_recompute: bool = False,
    ) -> ee.Image:
        """
        Get change map with caching.

        Args:
            aoi: Area of interest
            before_period: Earlier period
            after_period: Later period
            index: Index for change detection
            force_recompute: Ignore cache

        Returns:
            ee.Image with delta and change_class bands
        """
        from veg_change_engine.core.change import analyze_period_change

        cache_key = f"change_{before_period}_to_{after_period}_{index}"

        def compute():
            before = self.get_composite(aoi, before_period, [index])
            after = self.get_composite(aoi, after_period, [index])
            return analyze_period_change(before, after, index)

        return self.asset_cache.get_or_compute(
            name=cache_key,
            compute_fn=compute,
            region=aoi,
            force_recompute=force_recompute,
        )

    def get_tile_url_cached(
        self,
        image: ee.Image,
        vis_params: Dict,
        cache_key: str,
    ) -> str:
        """
        Get tile URL with local caching.

        Tile URLs expire after 24 hours.

        Args:
            image: ee.Image to visualize
            vis_params: Visualization parameters
            cache_key: Unique key for this visualization

        Returns:
            Tile URL string
        """
        # Check local cache first
        cached_url = self.local_cache.get_tile_url(cache_key)
        if cached_url:
            return cached_url

        # Generate new URL
        map_id = image.getMapId(vis_params)
        url = map_id["tile_fetcher"].url_format

        # Cache it
        self.local_cache.put_tile_url(cache_key, url)

        return url

    def list_cached_assets(self) -> List[str]:
        """List all cached EE assets."""
        return self.asset_cache.list_cached()

    def clear_cache(self, assets: bool = True, local: bool = True):
        """
        Clear caches.

        Args:
            assets: Clear EE asset cache
            local: Clear local metadata cache
        """
        if assets:
            self.asset_cache.clear()
        if local:
            self.local_cache.clear()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def setup_cache(asset_folder: str) -> CachedAnalysis:
    """
    Set up caching for vegetation change analysis.

    Args:
        asset_folder: EE asset folder (e.g., 'users/myuser/veg_cache')

    Returns:
        CachedAnalysis instance

    Example:
        >>> cache = setup_cache('users/myuser/veg_cache')
        >>> composite = cache.get_composite(aoi, '2010s', ['ndvi'])
        >>> # Second call loads from cache instead of recomputing
        >>> composite2 = cache.get_composite(aoi, '2010s', ['ndvi'])
    """
    return CachedAnalysis(asset_folder)
