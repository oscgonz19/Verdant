"""
Analysis routes for vegetation change detection API.

Endpoints:
- POST /analysis - Create analysis job
- GET /analysis/{job_id} - Get job status/results
- DELETE /analysis/{job_id} - Cancel job
- GET /analysis - List jobs
- POST /analysis/preview - Generate preview tile URL
"""

from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
import ee

from app.api.models.requests import (
    AnalysisRequest,
    PreviewRequest,
    TemporalPeriod,
    SpectralIndexType,
)
from app.api.models.responses import (
    AnalysisJobResponse,
    JobStatusResponse,
    JobListResponse,
    PreviewResponse,
    AnalysisStatus,
    ErrorResponse,
)
from engine.config import VegChangeConfig, TEMPORAL_PERIODS, VIS_PARAMS
from services.change_orchestrator import ChangeOrchestrator

router = APIRouter(prefix="/analysis", tags=["Analysis"])

# Global orchestrator instance
_orchestrator: Optional[ChangeOrchestrator] = None


def get_orchestrator() -> ChangeOrchestrator:
    """Get or create orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ChangeOrchestrator()
    return _orchestrator


def request_to_aoi(request: AnalysisRequest | PreviewRequest) -> ee.Geometry:
    """Convert request AOI to ee.Geometry."""
    if request.bbox:
        geojson = request.bbox.to_geojson()
    else:
        geojson = {
            "type": request.aoi_geojson.type,
            "coordinates": request.aoi_geojson.coordinates,
        }
    return ee.Geometry(geojson)


@router.post(
    "",
    response_model=AnalysisJobResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Create analysis job",
    description="Create a new vegetation change analysis job. The job runs asynchronously.",
)
async def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
):
    """Create a new analysis job."""
    orchestrator = get_orchestrator()

    # Convert request to config
    config = VegChangeConfig(
        site_name=request.site_name,
        periods=[p.value for p in request.periods],
        indices=[i.value for i in request.indices],
        buffer_distance=request.buffer_distance,
        cloud_threshold=request.cloud_threshold,
        export_to_drive=request.export_to_drive,
        drive_folder=request.drive_folder or "VegChangeAnalysis",
    )

    # Create job
    job_id = orchestrator.create_job(config)
    job = orchestrator.get_job(job_id)

    # Convert AOI and start background task
    try:
        aoi = request_to_aoi(request)

        # Run analysis in background
        background_tasks.add_task(
            orchestrator.run_job,
            job_id,
            aoi,
            request.reference_period.value,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid AOI: {str(e)}")

    return AnalysisJobResponse(
        job_id=job.job_id,
        status=AnalysisStatus(job.status.value),
        message="Analysis job created successfully",
        created_at=job.created_at,
    )


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
    summary="Get job status",
    description="Get the current status and results of an analysis job.",
)
async def get_job_status(job_id: str):
    """Get status of an analysis job."""
    orchestrator = get_orchestrator()
    job = orchestrator.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return JobStatusResponse(
        job_id=job.job_id,
        status=AnalysisStatus(job.status.value),
        progress=job.progress,
        current_step=job.current_step,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error=job.error,
        results=job.results,
    )


@router.delete(
    "/{job_id}",
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Cannot cancel running job"},
    },
    summary="Cancel job",
    description="Cancel a pending analysis job. Running jobs cannot be cancelled.",
)
async def cancel_job(job_id: str):
    """Cancel an analysis job."""
    orchestrator = get_orchestrator()
    job = orchestrator.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if not orchestrator.cancel_job(job_id):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel job with status: {job.status.value}"
        )

    return {"message": f"Job {job_id} cancelled"}


@router.get(
    "",
    response_model=JobListResponse,
    summary="List jobs",
    description="List analysis jobs, optionally filtered by status.",
)
async def list_jobs(
    status: Optional[AnalysisStatus] = Query(
        default=None,
        description="Filter by job status"
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of jobs to return"
    ),
):
    """List analysis jobs."""
    orchestrator = get_orchestrator()

    # Convert API status enum to service status enum
    from services.change_orchestrator import AnalysisStatus as ServiceStatus
    service_status = ServiceStatus(status.value) if status else None

    jobs = orchestrator.list_jobs(status=service_status, limit=limit)

    job_responses = [
        JobStatusResponse(
            job_id=job.job_id,
            status=AnalysisStatus(job.status.value),
            progress=job.progress,
            current_step=job.current_step,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error=job.error,
            results=job.results,
        )
        for job in jobs
    ]

    return JobListResponse(
        jobs=job_responses,
        total=len(job_responses),
    )


@router.post(
    "/preview",
    response_model=PreviewResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Generate preview",
    description="Generate a tile URL for previewing a single period/index.",
)
async def generate_preview(request: PreviewRequest):
    """Generate preview tile URL."""
    from engine.composites import create_fused_composite
    from engine.indices import add_all_indices

    try:
        # Convert AOI
        aoi = request_to_aoi(request)

        # Get period info
        period_info = TEMPORAL_PERIODS[request.period.value]

        # Create composite
        composite = create_fused_composite(
            aoi=aoi,
            start_date=period_info["start"],
            end_date=period_info["end"],
            sensors=period_info["sensors"],
        )

        # Add index
        composite = add_all_indices(composite, [request.index.value])

        # Get visualization params
        vis_params = VIS_PARAMS.get(request.index.value, VIS_PARAMS["ndvi"])

        # Generate tile URL
        map_id = composite.select(request.index.value).getMapId(vis_params)
        tile_url = map_id["tile_fetcher"].url_format

        # Calculate bounds and center
        if request.bbox:
            bounds = {
                "min_lat": request.bbox.min_lat,
                "min_lon": request.bbox.min_lon,
                "max_lat": request.bbox.max_lat,
                "max_lon": request.bbox.max_lon,
            }
            center = {
                "lat": (request.bbox.min_lat + request.bbox.max_lat) / 2,
                "lon": (request.bbox.min_lon + request.bbox.max_lon) / 2,
            }
        else:
            # For GeoJSON, compute bounds from geometry
            bounds_info = aoi.bounds().getInfo()
            coords = bounds_info["coordinates"][0]
            bounds = {
                "min_lon": coords[0][0],
                "min_lat": coords[0][1],
                "max_lon": coords[2][0],
                "max_lat": coords[2][1],
            }
            center = {
                "lat": (bounds["min_lat"] + bounds["max_lat"]) / 2,
                "lon": (bounds["min_lon"] + bounds["max_lon"]) / 2,
            }

        return PreviewResponse(
            tile_url=tile_url,
            center=center,
            bounds=bounds,
            vis_params=vis_params,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
