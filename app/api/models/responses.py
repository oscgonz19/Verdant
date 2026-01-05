"""
Pydantic response models for vegetation change API.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AnalysisStatus(str, Enum):
    """Status of an analysis job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisJobResponse(BaseModel):
    """
    Response when creating a new analysis job.
    """
    job_id: str = Field(..., description="Unique identifier for the job")
    status: AnalysisStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Human-readable status message")
    created_at: datetime = Field(..., description="Job creation timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "abc12345",
                "status": "pending",
                "message": "Analysis job created successfully",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    }


class JobStatusResponse(BaseModel):
    """
    Response when querying job status.
    """
    job_id: str = Field(..., description="Unique identifier for the job")
    status: AnalysisStatus = Field(..., description="Current job status")
    progress: float = Field(
        ...,
        ge=0,
        le=1,
        description="Progress from 0.0 to 1.0"
    )
    current_step: str = Field(
        default="",
        description="Description of current processing step"
    )
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(
        default=None,
        description="Job start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Job completion timestamp"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if job failed"
    )
    results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Analysis results (when completed)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "abc12345",
                "status": "running",
                "progress": 0.65,
                "current_step": "Analyzing vegetation change",
                "created_at": "2024-01-15T10:30:00Z",
                "started_at": "2024-01-15T10:30:05Z",
                "completed_at": None,
                "error": None,
                "results": None
            }
        }
    }


class JobListResponse(BaseModel):
    """
    Response when listing analysis jobs.
    """
    jobs: List[JobStatusResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")


class PreviewResponse(BaseModel):
    """
    Response when generating a preview tile URL.
    """
    tile_url: str = Field(..., description="XYZ tile URL template")
    center: Dict[str, float] = Field(
        ...,
        description="Center coordinates {lat, lon}"
    )
    bounds: Dict[str, float] = Field(
        ...,
        description="Bounding box {min_lat, min_lon, max_lat, max_lon}"
    )
    vis_params: Dict[str, Any] = Field(
        ...,
        description="Visualization parameters used"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "tile_url": "https://earthengine.googleapis.com/v1alpha/projects/earthengine-legacy/maps/...",
                "center": {"lat": -3.5, "lon": -62.5},
                "bounds": {
                    "min_lat": -4.0,
                    "min_lon": -63.0,
                    "max_lat": -3.0,
                    "max_lon": -62.0
                },
                "vis_params": {
                    "min": -0.2,
                    "max": 0.8,
                    "palette": ["red", "yellow", "green"]
                }
            }
        }
    }


class PeriodInfo(BaseModel):
    """
    Information about a temporal period.
    """
    name: str = Field(..., description="Period identifier")
    start: str = Field(..., description="Start date (YYYY-MM-DD)")
    end: str = Field(..., description="End date (YYYY-MM-DD)")
    sensors: List[str] = Field(..., description="Satellite sensors used")
    description: str = Field(..., description="Human-readable description")


class PeriodsResponse(BaseModel):
    """
    Response listing available temporal periods.
    """
    periods: List[PeriodInfo] = Field(..., description="Available periods")


class IndexInfo(BaseModel):
    """
    Information about a spectral index.
    """
    name: str = Field(..., description="Index identifier")
    full_name: str = Field(..., description="Full index name")
    description: str = Field(..., description="What the index measures")
    formula: str = Field(..., description="Calculation formula")
    range: Dict[str, float] = Field(
        ...,
        description="Typical value range {min, max}"
    )


class IndicesResponse(BaseModel):
    """
    Response listing available spectral indices.
    """
    indices: List[IndexInfo] = Field(..., description="Available indices")


class ErrorResponse(BaseModel):
    """
    Standard error response.
    """
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error details")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error context"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ValidationError",
                "message": "Invalid request parameters",
                "details": {"field": "periods", "issue": "Minimum 2 periods required"}
            }
        }
    }


class HealthResponse(BaseModel):
    """
    Health check response.
    """
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    earth_engine: bool = Field(
        ...,
        description="Whether Earth Engine is initialized"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "earth_engine": True
            }
        }
    }
