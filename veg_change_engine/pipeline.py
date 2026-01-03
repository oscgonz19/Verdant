"""
Main pipeline orchestrator for vegetation change analysis.

Provides high-level functions that combine all modules into
a complete analysis workflow.

Example:
    >>> results = run_full_analysis(
    ...     aoi_path="area.geojson",
    ...     periods=["1990s", "2000s", "2010s", "present"],
    ...     export=True
    ... )
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import ee

from veg_change_engine.config import (
    VegChangeConfig,
    DEFAULT_CONFIG,
    TEMPORAL_PERIODS,
)
from veg_change_engine.core.composites import (
    create_all_period_composites,
    get_image_count,
)
from veg_change_engine.core.indices import add_all_indices, calculate_delta_indices
from veg_change_engine.core.change import (
    create_change_analysis,
    generate_change_statistics,
)
from veg_change_engine.io.aoi import (
    load_aoi,
    aoi_to_ee_geometry,
    create_buffered_aoi,
    get_aoi_centroid,
    get_aoi_area,
)
from veg_change_engine.io.exporters import (
    export_all_composites,
    export_all_changes,
    ExportConfig,
)


def analyze_vegetation_change(
    aoi: ee.Geometry,
    periods: Optional[List[str]] = None,
    indices: Optional[List[str]] = None,
    reference_period: str = "1990s",
    config: Optional[VegChangeConfig] = None,
) -> Dict[str, Any]:
    """
    Run vegetation change analysis on an area of interest.

    This is the main entry point for programmatic use.

    Args:
        aoi: Area of interest as ee.Geometry
        periods: List of temporal periods to analyze
        indices: Spectral indices to calculate
        reference_period: Baseline period for change detection
        config: Analysis configuration

    Returns:
        Dictionary with:
        - composites: Period composites with indices
        - changes: Change detection results
        - statistics: Summary statistics
    """
    if config is None:
        config = DEFAULT_CONFIG

    if periods is None:
        periods = config.periods

    if indices is None:
        indices = config.indices

    print(f"Starting vegetation change analysis...")
    print(f"  Periods: {periods}")
    print(f"  Indices: {indices}")

    # Step 1: Create temporal composites
    print("\n[1/4] Creating temporal composites...")
    composites = create_all_period_composites(
        aoi=aoi,
        periods=periods,
        cloud_threshold=config.cloud_threshold,
    )

    # Step 2: Add spectral indices
    print("[2/4] Calculating spectral indices...")
    for period_name in composites:
        composites[period_name] = add_all_indices(
            composites[period_name],
            indices=indices,
        )
        print(f"  - {period_name}: indices added")

    # Step 3: Create change analysis
    print("[3/4] Analyzing vegetation change...")
    changes = create_change_analysis(
        composites=composites,
        indices=indices,
        reference_period=reference_period,
    )

    for comparison_name in changes:
        print(f"  - {comparison_name}: change calculated")

    # Step 4: Generate statistics
    print("[4/4] Generating statistics...")
    statistics = {}
    for comparison_name, change_image in changes.items():
        stats = generate_change_statistics(
            change_image=change_image,
            aoi=aoi,
            scale=config.export_scale,
        )
        statistics[comparison_name] = stats

    print("\nAnalysis complete!")

    return {
        "composites": composites,
        "changes": changes,
        "statistics": statistics,
        "config": config,
    }


def run_full_analysis(
    aoi_path: str,
    site_name: str = "Analysis Site",
    periods: Optional[List[str]] = None,
    indices: Optional[List[str]] = None,
    reference_period: str = "1990s",
    buffer_distance: float = 500.0,
    export: bool = False,
    export_folder: str = "VegChangeAnalysis",
    config: Optional[VegChangeConfig] = None,
) -> Dict[str, Any]:
    """
    Run complete analysis workflow from file.

    Args:
        aoi_path: Path to AOI file (KMZ, GeoJSON, Shapefile, etc.)
        site_name: Name for the analysis site
        periods: Temporal periods to analyze
        indices: Spectral indices to calculate
        reference_period: Baseline period
        buffer_distance: Buffer around AOI in meters
        export: Whether to export results to Drive
        export_folder: Google Drive folder name
        config: Full configuration object

    Returns:
        Dictionary with analysis results and export tasks
    """
    # Initialize configuration
    if config is None:
        config = VegChangeConfig(
            site_name=site_name,
            periods=periods or ["1990s", "2000s", "2010s", "present"],
            indices=indices or ["ndvi", "nbr"],
            buffer_distance=buffer_distance,
            drive_folder=export_folder,
        )

    print("=" * 60)
    print(f"VEGETATION CHANGE ANALYSIS: {config.site_name}")
    print("=" * 60)

    # Step 1: Load and prepare AOI
    print("\n[SETUP] Loading area of interest...")
    gdf = load_aoi(aoi_path)
    print(f"  Loaded: {aoi_path}")

    # Get AOI info
    centroid = get_aoi_centroid(gdf)
    area_ha = get_aoi_area(gdf)
    print(f"  Center: {centroid['lat']:.4f}, {centroid['lon']:.4f}")
    print(f"  Area: {area_ha:.1f} hectares")

    # Create buffered AOI
    if buffer_distance > 0:
        gdf_buffered = create_buffered_aoi(gdf, buffer_distance)
        print(f"  Buffer: {buffer_distance}m applied")
    else:
        gdf_buffered = gdf

    # Convert to EE geometry
    aoi = aoi_to_ee_geometry(gdf_buffered)

    # Step 2: Check data availability
    print("\n[DATA] Checking image availability...")
    for period_name in config.periods:
        period_info = TEMPORAL_PERIODS[period_name]
        for sensor in period_info["sensors"]:
            count = get_image_count(
                aoi=aoi,
                start_date=period_info["start"],
                end_date=period_info["end"],
                sensor=sensor,
                cloud_threshold=config.cloud_threshold,
            )
            # Note: count is an ee.Number, would need .getInfo() to print

    # Step 3: Run analysis
    results = analyze_vegetation_change(
        aoi=aoi,
        periods=config.periods,
        indices=config.indices,
        reference_period=reference_period,
        config=config,
    )

    # Step 4: Export if requested
    if export:
        print("\n[EXPORT] Starting exports to Google Drive...")

        export_config = ExportConfig(
            drive_folder=config.drive_folder,
            scale=config.export_scale,
            prefix=f"veg_{site_name.lower().replace(' ', '_')}",
        )

        # Export composites
        composite_tasks = export_all_composites(
            composites=results["composites"],
            region=aoi,
            site_name=site_name,
            config=export_config,
            start=True,
        )
        results["composite_tasks"] = composite_tasks

        # Export change maps
        change_tasks = export_all_changes(
            change_images=results["changes"],
            region=aoi,
            site_name=site_name,
            config=export_config,
            start=True,
        )
        results["change_tasks"] = change_tasks

        print(f"  Started {len(composite_tasks)} composite exports")
        print(f"  Started {len(change_tasks)} change map exports")
        print(f"  Check Google Drive folder: {config.drive_folder}")

    # Add metadata
    results["aoi_gdf"] = gdf
    results["aoi_buffered_gdf"] = gdf_buffered
    results["aoi_centroid"] = centroid
    results["aoi_area_ha"] = area_ha

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    return results


def quick_preview(
    aoi_path: str,
    period: str = "present",
    index: str = "ndvi",
) -> ee.Image:
    """
    Generate a quick preview composite.

    Useful for testing AOI and data availability.

    Args:
        aoi_path: Path to AOI file
        period: Single period to preview
        index: Index to calculate

    Returns:
        ee.Image composite with index band
    """
    from veg_change_engine.core.composites import create_fused_composite

    # Load AOI
    gdf = load_aoi(aoi_path)
    aoi = aoi_to_ee_geometry(gdf)

    # Get period info
    period_info = TEMPORAL_PERIODS[period]

    # Create composite
    composite = create_fused_composite(
        aoi=aoi,
        start_date=period_info["start"],
        end_date=period_info["end"],
        sensors=period_info["sensors"],
    )

    # Add index
    composite = add_all_indices(composite, [index])

    return composite


def get_period_summary(periods: Optional[List[str]] = None) -> Dict:
    """
    Get summary of temporal periods.

    Args:
        periods: List of period names (default: all)

    Returns:
        Dictionary with period information
    """
    if periods is None:
        periods = list(TEMPORAL_PERIODS.keys())

    summary = {}
    for period_name in periods:
        if period_name in TEMPORAL_PERIODS:
            info = TEMPORAL_PERIODS[period_name]
            summary[period_name] = {
                "start": info["start"],
                "end": info["end"],
                "sensors": info["sensors"],
                "description": info["description"],
            }

    return summary
