"""
Change detection orchestrator service.

Provides high-level workflows for vegetation change analysis,
including job management for async API operations.

Example:
    >>> orchestrator = ChangeOrchestrator()
    >>> job_id = orchestrator.create_job(config)
    >>> orchestrator.run_job(job_id, aoi)
    >>> results = orchestrator.get_job(job_id)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import uuid
import threading
import ee

from engine.config import (
    VegChangeConfig,
    DEFAULT_CONFIG,
    TEMPORAL_PERIODS,
)
from engine.composites import (
    create_all_period_composites,
    create_fused_composite,
    get_image_count,
)
from engine.indices import add_all_indices, calculate_delta_indices
from engine.change import (
    create_change_analysis,
    generate_change_statistics,
)
from engine.io.aoi import (
    load_aoi,
    aoi_to_ee_geometry,
    create_buffered_aoi,
    get_aoi_centroid,
    get_aoi_area,
)
from engine.io.exporters import (
    export_all_composites,
    export_all_changes,
    ExportConfig,
)


# =============================================================================
# JOB STATUS AND MODELS
# =============================================================================

class AnalysisStatus(str, Enum):
    """Status of an analysis job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AnalysisJob:
    """
    Tracks state of an analysis job.

    Used for async API operations to monitor progress
    and store results.
    """
    job_id: str
    status: AnalysisStatus
    config: VegChangeConfig
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    current_step: str = ""
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API responses."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "progress": self.progress,
            "current_step": self.current_step,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "has_results": self.results is not None,
        }


class JobStore:
    """
    In-memory storage for analysis jobs.

    Thread-safe for use with FastAPI BackgroundTasks.
    For production, replace with Redis or database.
    """

    def __init__(self, max_jobs: int = 100):
        """
        Initialize job store.

        Args:
            max_jobs: Maximum number of jobs to retain
        """
        self._jobs: Dict[str, AnalysisJob] = {}
        self._lock = threading.Lock()
        self._max_jobs = max_jobs

    def create(self, config: VegChangeConfig) -> AnalysisJob:
        """Create a new job."""
        job_id = str(uuid.uuid4())[:8]
        job = AnalysisJob(
            job_id=job_id,
            status=AnalysisStatus.PENDING,
            config=config,
        )

        with self._lock:
            # Cleanup old jobs if needed
            self._cleanup_old_jobs()
            self._jobs[job_id] = job

        return job

    def get(self, job_id: str) -> Optional[AnalysisJob]:
        """Get job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs) -> Optional[AnalysisJob]:
        """Update job fields."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                for key, value in kwargs.items():
                    if hasattr(job, key):
                        setattr(job, key, value)
            return job

    def delete(self, job_id: str) -> bool:
        """Delete a job."""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False

    def list_jobs(
        self,
        status: Optional[AnalysisStatus] = None,
        limit: int = 50,
    ) -> List[AnalysisJob]:
        """List jobs, optionally filtered by status."""
        with self._lock:
            jobs = list(self._jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        return jobs[:limit]

    def _cleanup_old_jobs(self):
        """Remove oldest completed jobs if over limit."""
        if len(self._jobs) < self._max_jobs:
            return

        # Get completed jobs sorted by completion time
        completed = [
            (jid, job) for jid, job in self._jobs.items()
            if job.status in (AnalysisStatus.COMPLETED, AnalysisStatus.FAILED)
        ]
        completed.sort(key=lambda x: x[1].completed_at or x[1].created_at)

        # Remove oldest completed jobs
        to_remove = len(self._jobs) - self._max_jobs + 10
        for jid, _ in completed[:to_remove]:
            del self._jobs[jid]


# =============================================================================
# CHANGE ORCHESTRATOR
# =============================================================================

class ChangeOrchestrator:
    """
    Orchestrates vegetation change analysis workflows.

    Provides both synchronous methods for direct use and
    job-based methods for async API operations.

    Example:
        >>> orchestrator = ChangeOrchestrator()
        >>>
        >>> # Direct use
        >>> results = orchestrator.analyze(aoi, periods, indices)
        >>>
        >>> # Job-based use
        >>> job_id = orchestrator.create_job(config)
        >>> orchestrator.run_job(job_id, aoi)
        >>> job = orchestrator.get_job(job_id)
    """

    def __init__(self, job_store: Optional[JobStore] = None):
        """
        Initialize orchestrator.

        Args:
            job_store: Optional custom job store (creates default if None)
        """
        self.job_store = job_store or JobStore()

    # -------------------------------------------------------------------------
    # SYNCHRONOUS ANALYSIS METHODS
    # -------------------------------------------------------------------------

    def analyze(
        self,
        aoi: ee.Geometry,
        periods: Optional[List[str]] = None,
        indices: Optional[List[str]] = None,
        reference_period: str = "1990s",
        config: Optional[VegChangeConfig] = None,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Run vegetation change analysis on an area of interest.

        Args:
            aoi: Area of interest as ee.Geometry
            periods: List of temporal periods to analyze
            indices: Spectral indices to calculate
            reference_period: Baseline period for change detection
            config: Analysis configuration
            progress_callback: Optional callback(progress, step) for updates

        Returns:
            Dictionary with composites, changes, and statistics
        """
        if config is None:
            config = DEFAULT_CONFIG

        if periods is None:
            periods = config.periods

        if indices is None:
            indices = config.indices

        def update_progress(progress: float, step: str):
            if progress_callback:
                progress_callback(progress, step)

        update_progress(0.0, "Starting analysis")

        # Step 1: Create temporal composites (0-40%)
        update_progress(0.05, "Creating temporal composites")
        composites = create_all_period_composites(
            aoi=aoi,
            periods=periods,
            cloud_threshold=config.cloud_threshold,
        )
        update_progress(0.40, "Composites created")

        # Step 2: Add spectral indices (40-60%)
        update_progress(0.45, "Calculating spectral indices")
        for period_name in composites:
            composites[period_name] = add_all_indices(
                composites[period_name],
                indices=indices,
            )
        update_progress(0.60, "Indices calculated")

        # Step 3: Create change analysis (60-85%)
        update_progress(0.65, "Analyzing vegetation change")
        changes = create_change_analysis(
            composites=composites,
            indices=indices,
            reference_period=reference_period,
        )
        update_progress(0.85, "Change analysis complete")

        # Step 4: Generate statistics (85-100%)
        update_progress(0.90, "Generating statistics")
        statistics = {}
        for comparison_name, change_image in changes.items():
            stats = generate_change_statistics(
                change_image=change_image,
                aoi=aoi,
                scale=config.export_scale,
            )
            statistics[comparison_name] = stats

        update_progress(1.0, "Analysis complete")

        return {
            "composites": composites,
            "changes": changes,
            "statistics": statistics,
            "config": config,
        }

    def analyze_from_file(
        self,
        aoi_path: str,
        site_name: str = "Analysis Site",
        periods: Optional[List[str]] = None,
        indices: Optional[List[str]] = None,
        reference_period: str = "1990s",
        buffer_distance: float = 500.0,
        export: bool = False,
        export_folder: str = "VegChangeAnalysis",
        config: Optional[VegChangeConfig] = None,
        progress_callback: Optional[callable] = None,
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
            progress_callback: Optional callback for progress updates

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

        def update_progress(progress: float, step: str):
            if progress_callback:
                progress_callback(progress, step)

        update_progress(0.0, "Loading area of interest")

        # Load and prepare AOI
        gdf = load_aoi(aoi_path)

        # Get AOI info
        centroid = get_aoi_centroid(gdf)
        area_ha = get_aoi_area(gdf)

        # Create buffered AOI
        if buffer_distance > 0:
            gdf_buffered = create_buffered_aoi(gdf, buffer_distance)
        else:
            gdf_buffered = gdf

        # Convert to EE geometry
        aoi = aoi_to_ee_geometry(gdf_buffered)

        update_progress(0.05, "AOI prepared")

        # Run analysis with progress callback offset
        def analysis_callback(progress: float, step: str):
            # Scale progress to 5-90% range
            scaled_progress = 0.05 + (progress * 0.85)
            update_progress(scaled_progress, step)

        results = self.analyze(
            aoi=aoi,
            periods=config.periods,
            indices=config.indices,
            reference_period=reference_period,
            config=config,
            progress_callback=analysis_callback,
        )

        # Export if requested
        if export:
            update_progress(0.92, "Starting exports")

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

        # Add metadata
        results["aoi_gdf"] = gdf
        results["aoi_buffered_gdf"] = gdf_buffered
        results["aoi_centroid"] = centroid
        results["aoi_area_ha"] = area_ha

        update_progress(1.0, "Complete")

        return results

    def preview(
        self,
        aoi_path: str,
        period: str = "present",
        index: str = "ndvi",
    ) -> ee.Image:
        """
        Generate a quick preview composite.

        Args:
            aoi_path: Path to AOI file
            period: Single period to preview
            index: Index to calculate

        Returns:
            ee.Image composite with index band
        """
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

    # -------------------------------------------------------------------------
    # JOB-BASED METHODS (for API)
    # -------------------------------------------------------------------------

    def create_job(self, config: VegChangeConfig) -> str:
        """
        Create a new analysis job.

        Args:
            config: Analysis configuration

        Returns:
            Job ID string
        """
        job = self.job_store.create(config)
        return job.job_id

    def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        """
        Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            AnalysisJob if found, None otherwise
        """
        return self.job_store.get(job_id)

    def run_job(
        self,
        job_id: str,
        aoi: ee.Geometry,
        reference_period: str = "1990s",
    ) -> None:
        """
        Run analysis job (for BackgroundTasks).

        Updates job status and progress as analysis runs.

        Args:
            job_id: Job identifier
            aoi: Area of interest geometry
            reference_period: Baseline period
        """
        job = self.job_store.get(job_id)
        if not job:
            return

        # Update job status
        self.job_store.update(
            job_id,
            status=AnalysisStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        try:
            # Progress callback updates job
            def progress_callback(progress: float, step: str):
                self.job_store.update(
                    job_id,
                    progress=progress,
                    current_step=step,
                )

            # Run analysis
            results = self.analyze(
                aoi=aoi,
                periods=job.config.periods,
                indices=job.config.indices,
                reference_period=reference_period,
                config=job.config,
                progress_callback=progress_callback,
            )

            # Store results (convert ee objects to serializable format)
            serializable_results = {
                "statistics": results.get("statistics"),
                "config": job.config.to_dict() if hasattr(job.config, "to_dict") else None,
            }

            self.job_store.update(
                job_id,
                status=AnalysisStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                progress=1.0,
                current_step="Complete",
                results=serializable_results,
            )

        except Exception as e:
            self.job_store.update(
                job_id,
                status=AnalysisStatus.FAILED,
                completed_at=datetime.utcnow(),
                error=str(e),
            )
            raise

    def run_job_from_file(
        self,
        job_id: str,
        aoi_path: str,
        buffer_distance: float = 500.0,
        reference_period: str = "1990s",
        export: bool = False,
    ) -> None:
        """
        Run analysis job from file (for BackgroundTasks).

        Args:
            job_id: Job identifier
            aoi_path: Path to AOI file
            buffer_distance: Buffer in meters
            reference_period: Baseline period
            export: Whether to export results
        """
        job = self.job_store.get(job_id)
        if not job:
            return

        # Update job status
        self.job_store.update(
            job_id,
            status=AnalysisStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        try:
            # Progress callback updates job
            def progress_callback(progress: float, step: str):
                self.job_store.update(
                    job_id,
                    progress=progress,
                    current_step=step,
                )

            # Run analysis
            results = self.analyze_from_file(
                aoi_path=aoi_path,
                site_name=job.config.site_name,
                periods=job.config.periods,
                indices=job.config.indices,
                reference_period=reference_period,
                buffer_distance=buffer_distance,
                export=export,
                export_folder=job.config.drive_folder,
                config=job.config,
                progress_callback=progress_callback,
            )

            # Store serializable results
            serializable_results = {
                "statistics": results.get("statistics"),
                "aoi_centroid": results.get("aoi_centroid"),
                "aoi_area_ha": results.get("aoi_area_ha"),
            }

            self.job_store.update(
                job_id,
                status=AnalysisStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                progress=1.0,
                current_step="Complete",
                results=serializable_results,
            )

        except Exception as e:
            self.job_store.update(
                job_id,
                status=AnalysisStatus.FAILED,
                completed_at=datetime.utcnow(),
                error=str(e),
            )
            raise

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job.

        Note: Cannot cancel running jobs (would require EE task cancellation).

        Args:
            job_id: Job identifier

        Returns:
            True if cancelled, False otherwise
        """
        job = self.job_store.get(job_id)
        if job and job.status == AnalysisStatus.PENDING:
            self.job_store.update(
                job_id,
                status=AnalysisStatus.CANCELLED,
                completed_at=datetime.utcnow(),
            )
            return True
        return False

    def list_jobs(
        self,
        status: Optional[AnalysisStatus] = None,
        limit: int = 50,
    ) -> List[AnalysisJob]:
        """
        List analysis jobs.

        Args:
            status: Filter by status
            limit: Maximum number of jobs to return

        Returns:
            List of AnalysisJob objects
        """
        return self.job_store.list_jobs(status=status, limit=limit)


# =============================================================================
# CONVENIENCE FUNCTIONS (backward compatibility with pipeline.py)
# =============================================================================

# Global orchestrator instance
_orchestrator: Optional[ChangeOrchestrator] = None


def _get_orchestrator() -> ChangeOrchestrator:
    """Get or create global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ChangeOrchestrator()
    return _orchestrator


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
        Dictionary with composites, changes, and statistics
    """
    orchestrator = _get_orchestrator()
    return orchestrator.analyze(
        aoi=aoi,
        periods=periods,
        indices=indices,
        reference_period=reference_period,
        config=config,
    )


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
    orchestrator = _get_orchestrator()
    return orchestrator.analyze_from_file(
        aoi_path=aoi_path,
        site_name=site_name,
        periods=periods,
        indices=indices,
        reference_period=reference_period,
        buffer_distance=buffer_distance,
        export=export,
        export_folder=export_folder,
        config=config,
    )


def quick_preview(
    aoi_path: str,
    period: str = "present",
    index: str = "ndvi",
) -> ee.Image:
    """
    Generate a quick preview composite.

    Args:
        aoi_path: Path to AOI file
        period: Single period to preview
        index: Index to calculate

    Returns:
        ee.Image composite with index band
    """
    orchestrator = _get_orchestrator()
    return orchestrator.preview(
        aoi_path=aoi_path,
        period=period,
        index=index,
    )


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
