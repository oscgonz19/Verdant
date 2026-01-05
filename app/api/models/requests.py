"""
Pydantic request models for vegetation change API.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class TemporalPeriod(str, Enum):
    """Available temporal periods for analysis."""
    PERIOD_1990S = "1990s"
    PERIOD_2000S = "2000s"
    PERIOD_2010S = "2010s"
    PRESENT = "present"


class SpectralIndexType(str, Enum):
    """Available spectral indices."""
    NDVI = "ndvi"
    NBR = "nbr"
    NDWI = "ndwi"
    EVI = "evi"
    NDMI = "ndmi"


class BoundingBox(BaseModel):
    """
    Bounding box for defining area of interest.

    Coordinates in WGS84 (EPSG:4326).
    """
    min_lon: float = Field(..., ge=-180, le=180, description="Minimum longitude")
    min_lat: float = Field(..., ge=-90, le=90, description="Minimum latitude")
    max_lon: float = Field(..., ge=-180, le=180, description="Maximum longitude")
    max_lat: float = Field(..., ge=-90, le=90, description="Maximum latitude")

    @field_validator("max_lon")
    @classmethod
    def validate_lon_order(cls, v, info):
        if "min_lon" in info.data and v <= info.data["min_lon"]:
            raise ValueError("max_lon must be greater than min_lon")
        return v

    @field_validator("max_lat")
    @classmethod
    def validate_lat_order(cls, v, info):
        if "min_lat" in info.data and v <= info.data["min_lat"]:
            raise ValueError("max_lat must be greater than min_lat")
        return v

    def to_geojson(self) -> Dict[str, Any]:
        """Convert to GeoJSON Polygon."""
        return {
            "type": "Polygon",
            "coordinates": [[
                [self.min_lon, self.min_lat],
                [self.max_lon, self.min_lat],
                [self.max_lon, self.max_lat],
                [self.min_lon, self.max_lat],
                [self.min_lon, self.min_lat],
            ]]
        }


class GeoJSONGeometry(BaseModel):
    """
    GeoJSON geometry for complex AOI shapes.

    Supports Polygon and MultiPolygon.
    """
    type: str = Field(..., description="Geometry type (Polygon or MultiPolygon)")
    coordinates: List = Field(..., description="GeoJSON coordinates array")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        allowed = {"Polygon", "MultiPolygon"}
        if v not in allowed:
            raise ValueError(f"type must be one of {allowed}")
        return v


class AnalysisRequest(BaseModel):
    """
    Request model for creating a vegetation change analysis job.

    Provide either bbox or aoi_geojson, not both.
    """
    site_name: str = Field(
        default="Analysis Site",
        min_length=1,
        max_length=100,
        description="Name for the analysis site"
    )

    # Area of Interest (one of these is required)
    bbox: Optional[BoundingBox] = Field(
        default=None,
        description="Bounding box for simple rectangular AOI"
    )
    aoi_geojson: Optional[GeoJSONGeometry] = Field(
        default=None,
        description="GeoJSON geometry for complex AOI shapes"
    )

    # Analysis parameters
    periods: List[TemporalPeriod] = Field(
        default=[TemporalPeriod.PERIOD_1990S, TemporalPeriod.PRESENT],
        min_length=2,
        description="Temporal periods to analyze (minimum 2)"
    )
    indices: List[SpectralIndexType] = Field(
        default=[SpectralIndexType.NDVI],
        min_length=1,
        description="Spectral indices to calculate"
    )
    reference_period: TemporalPeriod = Field(
        default=TemporalPeriod.PERIOD_1990S,
        description="Baseline period for change detection"
    )

    # Processing options
    buffer_distance: float = Field(
        default=500.0,
        ge=0,
        le=10000,
        description="Buffer around AOI in meters"
    )
    cloud_threshold: float = Field(
        default=20.0,
        ge=0,
        le=100,
        description="Maximum cloud cover percentage"
    )

    # Export options
    export_to_drive: bool = Field(
        default=False,
        description="Whether to export results to Google Drive"
    )
    drive_folder: Optional[str] = Field(
        default="VegChangeAnalysis",
        description="Google Drive folder for exports"
    )

    @field_validator("bbox", mode="before")
    @classmethod
    def check_aoi_provided(cls, v, info):
        # This validator runs for bbox
        return v

    def model_post_init(self, __context):
        """Validate that exactly one AOI is provided."""
        if self.bbox is None and self.aoi_geojson is None:
            raise ValueError("Either bbox or aoi_geojson must be provided")
        if self.bbox is not None and self.aoi_geojson is not None:
            raise ValueError("Provide either bbox or aoi_geojson, not both")


class PreviewRequest(BaseModel):
    """
    Request model for generating a preview tile URL.
    """
    # Area of Interest (one of these is required)
    bbox: Optional[BoundingBox] = Field(
        default=None,
        description="Bounding box for simple rectangular AOI"
    )
    aoi_geojson: Optional[GeoJSONGeometry] = Field(
        default=None,
        description="GeoJSON geometry for complex AOI shapes"
    )

    # Preview parameters
    period: TemporalPeriod = Field(
        default=TemporalPeriod.PRESENT,
        description="Temporal period to preview"
    )
    index: SpectralIndexType = Field(
        default=SpectralIndexType.NDVI,
        description="Spectral index to visualize"
    )

    def model_post_init(self, __context):
        """Validate that exactly one AOI is provided."""
        if self.bbox is None and self.aoi_geojson is None:
            raise ValueError("Either bbox or aoi_geojson must be provided")
        if self.bbox is not None and self.aoi_geojson is not None:
            raise ValueError("Provide either bbox or aoi_geojson, not both")
