"""
Export module for vegetation change analysis results.

Supports:
- Google Drive export (via Earth Engine)
- Local GeoTIFF export
- Report generation

Follows SOLID principles:
- Single Responsibility: Each exporter handles one output type
- Open/Closed: New export formats via strategy pattern
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
import ee


# =============================================================================
# EXPORT CONFIGURATION
# =============================================================================

@dataclass
class ExportConfig:
    """Configuration for export operations."""

    # Google Drive settings
    drive_folder: str = "VegChangeAnalysis"

    # Resolution
    scale: int = 30  # meters

    # File naming
    prefix: str = "veg_change"
    date_format: str = "%Y%m%d"

    # CRS
    crs: str = "EPSG:4326"

    # Compression
    format_options: Dict = None

    def __post_init__(self):
        if self.format_options is None:
            self.format_options = {"cloudOptimized": True}


# =============================================================================
# ABSTRACT EXPORTER (Strategy Pattern)
# =============================================================================

class Exporter(ABC):
    """Abstract base class for exporters."""

    @abstractmethod
    def export(
        self,
        image: ee.Image,
        name: str,
        region: ee.Geometry,
        config: ExportConfig,
    ) -> ee.batch.Task:
        """Export image and return task."""
        pass


# =============================================================================
# CONCRETE EXPORTERS
# =============================================================================

class DriveExporter(Exporter):
    """Export images to Google Drive."""

    def export(
        self,
        image: ee.Image,
        name: str,
        region: ee.Geometry,
        config: ExportConfig,
    ) -> ee.batch.Task:
        """
        Export image to Google Drive.

        Args:
            image: ee.Image to export
            name: Output filename
            region: Export region
            config: Export configuration

        Returns:
            ee.batch.Task object
        """
        task = ee.batch.Export.image.toDrive(
            image=image,
            description=name,
            folder=config.drive_folder,
            fileNamePrefix=name,
            region=region,
            scale=config.scale,
            crs=config.crs,
            maxPixels=1e13,
            formatOptions=config.format_options,
        )
        return task


class AssetExporter(Exporter):
    """Export images to Earth Engine Assets."""

    def __init__(self, asset_folder: str):
        self.asset_folder = asset_folder

    def export(
        self,
        image: ee.Image,
        name: str,
        region: ee.Geometry,
        config: ExportConfig,
    ) -> ee.batch.Task:
        """
        Export image to EE Asset.

        Args:
            image: ee.Image to export
            name: Asset name
            region: Export region
            config: Export configuration

        Returns:
            ee.batch.Task object
        """
        asset_id = f"{self.asset_folder}/{name}"

        task = ee.batch.Export.image.toAsset(
            image=image,
            description=name,
            assetId=asset_id,
            region=region,
            scale=config.scale,
            crs=config.crs,
            maxPixels=1e13,
        )
        return task


class CloudStorageExporter(Exporter):
    """Export images to Google Cloud Storage."""

    def __init__(self, bucket: str):
        self.bucket = bucket

    def export(
        self,
        image: ee.Image,
        name: str,
        region: ee.Geometry,
        config: ExportConfig,
    ) -> ee.batch.Task:
        """
        Export image to Cloud Storage.

        Args:
            image: ee.Image to export
            name: Output filename
            region: Export region
            config: Export configuration

        Returns:
            ee.batch.Task object
        """
        task = ee.batch.Export.image.toCloudStorage(
            image=image,
            description=name,
            bucket=self.bucket,
            fileNamePrefix=name,
            region=region,
            scale=config.scale,
            crs=config.crs,
            maxPixels=1e13,
            formatOptions=config.format_options,
        )
        return task


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def export_to_drive(
    image: ee.Image,
    name: str,
    region: ee.Geometry,
    folder: str = "VegChangeAnalysis",
    scale: int = 30,
    crs: str = "EPSG:4326",
    start: bool = True,
) -> ee.batch.Task:
    """
    Export image to Google Drive.

    Args:
        image: ee.Image to export
        name: Output filename
        region: Export region
        folder: Drive folder name
        scale: Export scale in meters
        crs: Coordinate reference system
        start: Whether to start the task immediately

    Returns:
        ee.batch.Task object
    """
    config = ExportConfig(
        drive_folder=folder,
        scale=scale,
        crs=crs,
    )

    exporter = DriveExporter()
    task = exporter.export(image, name, region, config)

    if start:
        task.start()

    return task


def export_composite(
    composite: ee.Image,
    period_name: str,
    region: ee.Geometry,
    site_name: str = "site",
    bands: Optional[List[str]] = None,
    config: Optional[ExportConfig] = None,
    start: bool = True,
) -> ee.batch.Task:
    """
    Export a temporal composite.

    Args:
        composite: Composite ee.Image
        period_name: Name of the time period
        region: Export region
        site_name: Site identifier
        bands: Bands to export (default: all)
        config: Export configuration
        start: Whether to start the task

    Returns:
        ee.batch.Task object
    """
    if config is None:
        config = ExportConfig()

    # Select bands if specified
    if bands:
        composite = composite.select(bands)

    # Generate filename
    date_str = datetime.now().strftime(config.date_format)
    name = f"{config.prefix}_{site_name}_{period_name}_{date_str}"

    task = export_to_drive(
        image=composite,
        name=name,
        region=region,
        folder=config.drive_folder,
        scale=config.scale,
        crs=config.crs,
        start=start,
    )

    return task


def export_change_map(
    change_image: ee.Image,
    comparison_name: str,
    region: ee.Geometry,
    site_name: str = "site",
    config: Optional[ExportConfig] = None,
    start: bool = True,
) -> ee.batch.Task:
    """
    Export a change detection result.

    Args:
        change_image: Change ee.Image (with delta and class bands)
        comparison_name: Period comparison name (e.g., "1990s_to_present")
        region: Export region
        site_name: Site identifier
        config: Export configuration
        start: Whether to start the task

    Returns:
        ee.batch.Task object
    """
    if config is None:
        config = ExportConfig()

    # Generate filename
    date_str = datetime.now().strftime(config.date_format)
    name = f"{config.prefix}_change_{site_name}_{comparison_name}_{date_str}"

    task = export_to_drive(
        image=change_image,
        name=name,
        region=region,
        folder=config.drive_folder,
        scale=config.scale,
        crs=config.crs,
        start=start,
    )

    return task


def export_all_composites(
    composites: Dict[str, ee.Image],
    region: ee.Geometry,
    site_name: str = "site",
    config: Optional[ExportConfig] = None,
    start: bool = True,
) -> Dict[str, ee.batch.Task]:
    """
    Export all temporal composites.

    Args:
        composites: Dictionary of period -> composite
        region: Export region
        site_name: Site identifier
        config: Export configuration
        start: Whether to start tasks

    Returns:
        Dictionary of period -> task
    """
    tasks = {}

    for period_name, composite in composites.items():
        task = export_composite(
            composite=composite,
            period_name=period_name,
            region=region,
            site_name=site_name,
            config=config,
            start=start,
        )
        tasks[period_name] = task

    return tasks


def export_all_changes(
    change_images: Dict[str, ee.Image],
    region: ee.Geometry,
    site_name: str = "site",
    config: Optional[ExportConfig] = None,
    start: bool = True,
) -> Dict[str, ee.batch.Task]:
    """
    Export all change detection results.

    Args:
        change_images: Dictionary of comparison -> change image
        region: Export region
        site_name: Site identifier
        config: Export configuration
        start: Whether to start tasks

    Returns:
        Dictionary of comparison -> task
    """
    tasks = {}

    for comparison_name, change_image in change_images.items():
        task = export_change_map(
            change_image=change_image,
            comparison_name=comparison_name,
            region=region,
            site_name=site_name,
            config=config,
            start=start,
        )
        tasks[comparison_name] = task

    return tasks


# =============================================================================
# TASK MONITORING
# =============================================================================

def get_task_status(task: ee.batch.Task) -> Dict:
    """
    Get status of an export task.

    Args:
        task: ee.batch.Task object

    Returns:
        Dictionary with task status info
    """
    status = task.status()
    return {
        "id": status.get("id"),
        "state": status.get("state"),
        "description": status.get("description"),
        "creation_time": status.get("creation_timestamp_ms"),
        "start_time": status.get("start_timestamp_ms"),
        "update_time": status.get("update_timestamp_ms"),
    }


def monitor_tasks(tasks: Dict[str, ee.batch.Task]) -> Dict[str, Dict]:
    """
    Monitor status of multiple tasks.

    Args:
        tasks: Dictionary of name -> task

    Returns:
        Dictionary of name -> status
    """
    statuses = {}
    for name, task in tasks.items():
        statuses[name] = get_task_status(task)
    return statuses


def wait_for_tasks(
    tasks: Dict[str, ee.batch.Task],
    timeout_seconds: int = 3600,
    poll_interval: int = 30,
) -> bool:
    """
    Wait for all tasks to complete.

    Args:
        tasks: Dictionary of name -> task
        timeout_seconds: Maximum wait time
        poll_interval: Seconds between status checks

    Returns:
        True if all tasks completed successfully
    """
    import time

    start_time = time.time()

    while True:
        # Check timeout
        if time.time() - start_time > timeout_seconds:
            print("Timeout waiting for tasks")
            return False

        # Check all task statuses
        all_complete = True
        any_failed = False

        for name, task in tasks.items():
            status = task.status()
            state = status.get("state")

            if state in ["RUNNING", "READY", "PENDING"]:
                all_complete = False
            elif state == "FAILED":
                any_failed = True
                print(f"Task {name} failed: {status.get('error_message')}")

        if all_complete:
            if any_failed:
                print("Some tasks failed")
                return False
            else:
                print("All tasks completed successfully")
                return True

        time.sleep(poll_interval)
