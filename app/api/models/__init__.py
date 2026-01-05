"""
Pydantic models for API requests and responses.
"""

from app.api.models.requests import (
    AnalysisRequest,
    PreviewRequest,
    BoundingBox,
    GeoJSONGeometry,
    TemporalPeriod,
    SpectralIndexType,
)

from app.api.models.responses import (
    AnalysisJobResponse,
    JobStatusResponse,
    JobListResponse,
    PreviewResponse,
    PeriodInfo,
    IndexInfo,
    PeriodsResponse,
    IndicesResponse,
    ErrorResponse,
    HealthResponse,
)

__all__ = [
    # Requests
    "AnalysisRequest",
    "PreviewRequest",
    "BoundingBox",
    "GeoJSONGeometry",
    "TemporalPeriod",
    "SpectralIndexType",
    # Responses
    "AnalysisJobResponse",
    "JobStatusResponse",
    "JobListResponse",
    "PreviewResponse",
    "PeriodInfo",
    "IndexInfo",
    "PeriodsResponse",
    "IndicesResponse",
    "ErrorResponse",
    "HealthResponse",
]
