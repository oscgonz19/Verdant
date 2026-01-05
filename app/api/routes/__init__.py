"""
API routes for vegetation change analysis.
"""

from app.api.routes.analysis import router as analysis_router
from app.api.routes.metadata import router as metadata_router

__all__ = [
    "analysis_router",
    "metadata_router",
]
