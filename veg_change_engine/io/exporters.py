"""
Export module for vegetation change analysis results.

Note:
    This module provides backward-compatible re-exports from engine/io/exporters.py.
    For new code, prefer importing directly from engine.io.exporters.
"""

# Re-export everything from engine.io.exporters
from engine.io.exporters import (
    # Configuration
    ExportConfig,
    # Abstract exporter
    Exporter,
    # Concrete exporters
    DriveExporter,
    AssetExporter,
    CloudStorageExporter,
    # Convenience functions
    export_to_drive,
    export_composite,
    export_change_map,
    export_all_composites,
    export_all_changes,
    # Task monitoring
    get_task_status,
    monitor_tasks,
    wait_for_tasks,
)

__all__ = [
    # Configuration
    "ExportConfig",
    # Abstract exporter
    "Exporter",
    # Concrete exporters
    "DriveExporter",
    "AssetExporter",
    "CloudStorageExporter",
    # Convenience functions
    "export_to_drive",
    "export_composite",
    "export_change_map",
    "export_all_composites",
    "export_all_changes",
    # Task monitoring
    "get_task_status",
    "monitor_tasks",
    "wait_for_tasks",
]
