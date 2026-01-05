"""
Metadata routes for vegetation change API.

Endpoints:
- GET /periods - List available temporal periods
- GET /indices - List available spectral indices
"""

from fastapi import APIRouter

from app.api.models.responses import (
    PeriodsResponse,
    IndicesResponse,
    PeriodInfo,
    IndexInfo,
)
from engine.config import TEMPORAL_PERIODS
from engine.indices import get_available_indices, INDEX_REGISTRY

router = APIRouter(tags=["Metadata"])


# Index descriptions and formulas
INDEX_METADATA = {
    "ndvi": {
        "full_name": "Normalized Difference Vegetation Index",
        "description": "Measures vegetation greenness and health. Higher values indicate denser, healthier vegetation.",
        "formula": "(NIR - Red) / (NIR + Red)",
        "range": {"min": -1.0, "max": 1.0},
    },
    "nbr": {
        "full_name": "Normalized Burn Ratio",
        "description": "Detects burned areas and fire severity. Low values indicate burned or stressed vegetation.",
        "formula": "(NIR - SWIR2) / (NIR + SWIR2)",
        "range": {"min": -1.0, "max": 1.0},
    },
    "ndwi": {
        "full_name": "Normalized Difference Water Index",
        "description": "Detects water bodies and moisture content. Higher values indicate more water.",
        "formula": "(Green - NIR) / (Green + NIR)",
        "range": {"min": -1.0, "max": 1.0},
    },
    "evi": {
        "full_name": "Enhanced Vegetation Index",
        "description": "Improved vegetation monitoring in high biomass regions. Less sensitive to atmospheric effects.",
        "formula": "2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)",
        "range": {"min": -1.0, "max": 1.0},
    },
    "ndmi": {
        "full_name": "Normalized Difference Moisture Index",
        "description": "Measures vegetation water content and drought stress.",
        "formula": "(NIR - SWIR1) / (NIR + SWIR1)",
        "range": {"min": -1.0, "max": 1.0},
    },
}


@router.get(
    "/periods",
    response_model=PeriodsResponse,
    summary="List temporal periods",
    description="Get list of available temporal periods for analysis.",
)
async def list_periods():
    """List available temporal periods."""
    periods = [
        PeriodInfo(
            name=name,
            start=info["start"],
            end=info["end"],
            sensors=info["sensors"],
            description=info["description"],
        )
        for name, info in TEMPORAL_PERIODS.items()
    ]

    return PeriodsResponse(periods=periods)


@router.get(
    "/indices",
    response_model=IndicesResponse,
    summary="List spectral indices",
    description="Get list of available spectral indices for analysis.",
)
async def list_indices():
    """List available spectral indices."""
    available = get_available_indices()

    indices = []
    for name in available:
        metadata = INDEX_METADATA.get(name, {
            "full_name": name.upper(),
            "description": f"Spectral index: {name}",
            "formula": "Custom formula",
            "range": {"min": -1.0, "max": 1.0},
        })

        indices.append(IndexInfo(
            name=name,
            full_name=metadata["full_name"],
            description=metadata["description"],
            formula=metadata["formula"],
            range=metadata["range"],
        ))

    return IndicesResponse(indices=indices)
