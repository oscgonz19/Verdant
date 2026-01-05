"""
Configuration module for Vegetation Change Intelligence Platform.

Contains temporal period definitions, sensor configurations, visualization
parameters, and change detection thresholds.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import yaml


# =============================================================================
# TEMPORAL PERIODS
# =============================================================================

TEMPORAL_PERIODS = {
    "1990s": {
        "start": "1985-01-01",
        "end": "1999-12-31",
        "sensors": ["LANDSAT/LT05/C02/T1_L2"],
        "description": "Pre-2000 baseline (Landsat 5 TM)",
    },
    "2000s": {
        "start": "2000-01-01",
        "end": "2012-12-31",
        "sensors": ["LANDSAT/LE07/C02/T1_L2", "LANDSAT/LT05/C02/T1_L2"],
        "description": "Early 2000s (Landsat 5/7)",
    },
    "2010s": {
        "start": "2013-01-01",
        "end": "2020-12-31",
        "sensors": ["LANDSAT/LC08/C02/T1_L2"],
        "description": "Recent decade (Landsat 8 OLI)",
    },
    "present": {
        "start": "2021-01-01",
        "end": "2024-12-31",
        "sensors": ["LANDSAT/LC08/C02/T1_L2", "COPERNICUS/S2_SR_HARMONIZED"],
        "description": "Current period (Landsat 8 + Sentinel-2)",
    },
}


# =============================================================================
# SENSOR BAND MAPPINGS
# =============================================================================

BAND_MAPPINGS = {
    # Landsat 5/7 TM/ETM+ (Collection 2)
    "LANDSAT/LT05/C02/T1_L2": {
        "blue": "SR_B1",
        "green": "SR_B2",
        "red": "SR_B3",
        "nir": "SR_B4",
        "swir1": "SR_B5",
        "swir2": "SR_B7",
        "qa": "QA_PIXEL",
        "scale_factor": 0.0000275,
        "offset": -0.2,
    },
    "LANDSAT/LE07/C02/T1_L2": {
        "blue": "SR_B1",
        "green": "SR_B2",
        "red": "SR_B3",
        "nir": "SR_B4",
        "swir1": "SR_B5",
        "swir2": "SR_B7",
        "qa": "QA_PIXEL",
        "scale_factor": 0.0000275,
        "offset": -0.2,
    },
    # Landsat 8 OLI (Collection 2)
    "LANDSAT/LC08/C02/T1_L2": {
        "blue": "SR_B2",
        "green": "SR_B3",
        "red": "SR_B4",
        "nir": "SR_B5",
        "swir1": "SR_B6",
        "swir2": "SR_B7",
        "qa": "QA_PIXEL",
        "scale_factor": 0.0000275,
        "offset": -0.2,
    },
    # Sentinel-2 MSI
    "COPERNICUS/S2_SR_HARMONIZED": {
        "blue": "B2",
        "green": "B3",
        "red": "B4",
        "nir": "B8",
        "swir1": "B11",
        "swir2": "B12",
        "qa": "QA60",
        "scale_factor": 0.0001,
        "offset": 0,
    },
}


# =============================================================================
# CLOUD MASKING
# =============================================================================

CLOUD_MASK_CONFIG = {
    "landsat": {
        # QA_PIXEL bit positions for Collection 2
        "cloud_bit": 3,
        "cloud_shadow_bit": 4,
        "snow_bit": 5,
        "dilated_cloud_bit": 1,
    },
    "sentinel2": {
        # QA60 bit positions
        "cloud_bit": 10,
        "cirrus_bit": 11,
    },
}


# =============================================================================
# VISUALIZATION PARAMETERS
# =============================================================================

VIS_PARAMS = {
    "rgb_landsat": {
        "bands": ["red", "green", "blue"],
        "min": 0,
        "max": 0.3,
        "gamma": 1.4,
    },
    "rgb_sentinel": {
        "bands": ["red", "green", "blue"],
        "min": 0,
        "max": 3000,
        "gamma": 1.4,
    },
    "ndvi": {
        "min": -0.2,
        "max": 0.8,
        "palette": [
            "#d73027",  # -0.2: Bare/water (red)
            "#fc8d59",  # 0.0: Sparse vegetation
            "#fee08b",  # 0.2: Low vegetation
            "#d9ef8b",  # 0.4: Moderate vegetation
            "#91cf60",  # 0.6: Dense vegetation
            "#1a9850",  # 0.8: Very dense (green)
        ],
    },
    "nbr": {
        "min": -0.5,
        "max": 0.8,
        "palette": [
            "#7f3b08",  # Very low (burned)
            "#b35806",
            "#e08214",
            "#fdb863",
            "#fee0b6",
            "#d8daeb",
            "#b2abd2",
            "#8073ac",
            "#542788",  # Very high
        ],
    },
    "dndvi": {
        "min": -0.4,
        "max": 0.4,
        "palette": [
            "#d7191c",  # Strong loss (red)
            "#fdae61",  # Moderate loss
            "#ffffbf",  # No change (yellow)
            "#a6d96a",  # Moderate gain
            "#1a9641",  # Strong gain (green)
        ],
    },
    "dnbr": {
        "min": -0.5,
        "max": 0.5,
        "palette": [
            "#7f3b08",  # Severe disturbance
            "#b35806",
            "#e08214",
            "#fdb863",
            "#f7f7f7",  # No change
            "#d8daeb",
            "#b2abd2",
            "#8073ac",
            "#2d004b",  # Strong recovery
        ],
    },
    "change_class": {
        "min": 1,
        "max": 5,
        "palette": [
            "#d7191c",  # 1: Strong loss
            "#fdae61",  # 2: Moderate loss
            "#ffffbf",  # 3: Stable
            "#a6d96a",  # 4: Moderate gain
            "#1a9641",  # 5: Strong gain
        ],
    },
}


# =============================================================================
# CHANGE DETECTION THRESHOLDS
# =============================================================================

CHANGE_THRESHOLDS = {
    "dndvi": {
        "strong_loss": -0.15,
        "moderate_loss": -0.05,
        "stable_min": -0.05,
        "stable_max": 0.05,
        "moderate_gain": 0.05,
        "strong_gain": 0.15,
    },
    "dnbr": {
        "strong_loss": -0.20,
        "moderate_loss": -0.10,
        "stable_min": -0.10,
        "stable_max": 0.10,
        "moderate_gain": 0.10,
        "strong_gain": 0.20,
    },
}

CHANGE_CLASSES = {
    1: {"label": "Strong Loss", "label_es": "Pérdida Fuerte", "color": "#d7191c"},
    2: {"label": "Moderate Loss", "label_es": "Pérdida Moderada", "color": "#fdae61"},
    3: {"label": "Stable", "label_es": "Estable", "color": "#ffffbf"},
    4: {"label": "Moderate Gain", "label_es": "Ganancia Moderada", "color": "#a6d96a"},
    5: {"label": "Strong Gain", "label_es": "Ganancia Fuerte", "color": "#1a9641"},
}


# =============================================================================
# SITE CONFIGURATION
# =============================================================================

@dataclass
class VegChangeConfig:
    """Configuration for vegetation change analysis."""

    # Site identification
    site_name: str = "Analysis Site"
    site_description: str = "Vegetation change analysis"
    region: str = "Region"
    country: str = "Country"

    # Analysis periods
    periods: List[str] = field(default_factory=lambda: ["1990s", "2000s", "2010s", "present"])

    # Spatial parameters
    buffer_distance: float = 500.0  # meters around AOI
    export_scale: int = 30  # meters (Landsat resolution)

    # Processing parameters
    cloud_threshold: float = 20.0  # Max cloud cover percentage
    min_images: int = 5  # Minimum images for composite

    # Spectral indices to calculate
    indices: List[str] = field(default_factory=lambda: ["ndvi", "nbr"])

    # Output configuration
    output_dir: str = "outputs"
    export_to_drive: bool = True
    drive_folder: str = "VegChangeAnalysis"

    # CRS
    target_epsg: int = 4326  # WGS84 for GEE

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "VegChangeConfig":
        """Load configuration from YAML file."""
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, yaml_path: str) -> None:
        """Save configuration to YAML file."""
        data = {
            "site_name": self.site_name,
            "site_description": self.site_description,
            "region": self.region,
            "country": self.country,
            "periods": self.periods,
            "buffer_distance": self.buffer_distance,
            "export_scale": self.export_scale,
            "cloud_threshold": self.cloud_threshold,
            "min_images": self.min_images,
            "indices": self.indices,
            "output_dir": self.output_dir,
            "export_to_drive": self.export_to_drive,
            "drive_folder": self.drive_folder,
            "target_epsg": self.target_epsg,
        }
        with open(yaml_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)


# Default configuration
DEFAULT_CONFIG = VegChangeConfig()


def get_config(yaml_path: Optional[str] = None) -> VegChangeConfig:
    """Get configuration, optionally from YAML file."""
    if yaml_path and Path(yaml_path).exists():
        return VegChangeConfig.from_yaml(yaml_path)
    return DEFAULT_CONFIG


def get_period_info(period_name: str) -> Dict:
    """Get information for a temporal period."""
    if period_name not in TEMPORAL_PERIODS:
        raise ValueError(f"Unknown period: {period_name}. Valid: {list(TEMPORAL_PERIODS.keys())}")
    return TEMPORAL_PERIODS[period_name]


def get_band_mapping(sensor: str) -> Dict:
    """Get band mapping for a sensor."""
    if sensor not in BAND_MAPPINGS:
        raise ValueError(f"Unknown sensor: {sensor}. Valid: {list(BAND_MAPPINGS.keys())}")
    return BAND_MAPPINGS[sensor]
