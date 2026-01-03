"""
Color palettes and visualization parameters.

Provides consistent color schemes for:
- Spectral indices (NDVI, NBR)
- Change detection classes
- RGB composites

Follows scientific visualization best practices:
- Colorblind-friendly palettes where possible
- Perceptually uniform gradients
- Standard conventions (green=vegetation, red=loss)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


# =============================================================================
# VISUALIZATION PARAMETERS
# =============================================================================

@dataclass
class VisParams:
    """Visualization parameters for Earth Engine."""
    min: float
    max: float
    palette: Optional[List[str]] = None
    bands: Optional[List[str]] = None
    gamma: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for ee.Image.visualize()."""
        params = {"min": self.min, "max": self.max}
        if self.palette:
            params["palette"] = self.palette
        if self.bands:
            params["bands"] = self.bands
        if self.gamma:
            params["gamma"] = self.gamma
        return params


# =============================================================================
# NDVI VISUALIZATION
# =============================================================================

NDVI_PALETTE = [
    "#d73027",  # -1.0 to -0.2: Water/bare (red)
    "#fc8d59",  # -0.2 to 0.0: Very sparse
    "#fee08b",  # 0.0 to 0.2: Sparse vegetation
    "#d9ef8b",  # 0.2 to 0.4: Low vegetation
    "#91cf60",  # 0.4 to 0.6: Moderate vegetation
    "#1a9850",  # 0.6 to 1.0: Dense vegetation (green)
]

NDVI_VIS_PARAMS = VisParams(
    min=-0.2,
    max=0.8,
    palette=NDVI_PALETTE,
)


# =============================================================================
# NBR VISUALIZATION
# =============================================================================

NBR_PALETTE = [
    "#7f3b08",  # Very low (burned)
    "#b35806",
    "#e08214",
    "#fdb863",
    "#fee0b6",
    "#f7f7f7",  # Neutral
    "#d8daeb",
    "#b2abd2",
    "#8073ac",
    "#542788",  # Very high
]

NBR_VIS_PARAMS = VisParams(
    min=-0.5,
    max=0.8,
    palette=NBR_PALETTE,
)


# =============================================================================
# CHANGE DETECTION VISUALIZATION
# =============================================================================

# Delta NDVI (change)
DNDVI_PALETTE = [
    "#d7191c",  # Strong loss (red)
    "#fdae61",  # Moderate loss (orange)
    "#ffffbf",  # Stable (yellow)
    "#a6d96a",  # Moderate gain (light green)
    "#1a9641",  # Strong gain (dark green)
]

DNDVI_VIS_PARAMS = VisParams(
    min=-0.4,
    max=0.4,
    palette=DNDVI_PALETTE,
)

# Delta NBR (change)
DNBR_PALETTE = [
    "#7f3b08",  # Severe disturbance
    "#b35806",
    "#e08214",
    "#fdb863",
    "#f7f7f7",  # No change
    "#d8daeb",
    "#b2abd2",
    "#8073ac",
    "#2d004b",  # Strong recovery
]

DNBR_VIS_PARAMS = VisParams(
    min=-0.5,
    max=0.5,
    palette=DNBR_PALETTE,
)

# Change classes (1-5)
CHANGE_CLASS_PALETTE = [
    "#d7191c",  # 1: Strong loss
    "#fdae61",  # 2: Moderate loss
    "#ffffbf",  # 3: Stable
    "#a6d96a",  # 4: Moderate gain
    "#1a9641",  # 5: Strong gain
]

CHANGE_VIS_PARAMS = VisParams(
    min=1,
    max=5,
    palette=CHANGE_CLASS_PALETTE,
)


# =============================================================================
# RGB COMPOSITE VISUALIZATION
# =============================================================================

# For scaled Landsat (0-1 range)
RGB_VIS_PARAMS = VisParams(
    min=0,
    max=0.3,
    bands=["red", "green", "blue"],
    gamma=1.4,
)

# False color (NIR-Red-Green)
FALSE_COLOR_VIS_PARAMS = VisParams(
    min=0,
    max=0.4,
    bands=["nir", "red", "green"],
    gamma=1.4,
)

# SWIR composite (SWIR2-NIR-Red)
SWIR_VIS_PARAMS = VisParams(
    min=0,
    max=0.4,
    bands=["swir2", "nir", "red"],
    gamma=1.4,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Registry of all visualization parameters
VIS_PARAMS_REGISTRY = {
    "ndvi": NDVI_VIS_PARAMS,
    "nbr": NBR_VIS_PARAMS,
    "dndvi": DNDVI_VIS_PARAMS,
    "dnbr": DNBR_VIS_PARAMS,
    "change_class": CHANGE_VIS_PARAMS,
    "rgb": RGB_VIS_PARAMS,
    "false_color": FALSE_COLOR_VIS_PARAMS,
    "swir": SWIR_VIS_PARAMS,
}


def get_vis_params(name: str) -> VisParams:
    """
    Get visualization parameters by name.

    Args:
        name: Parameter set name

    Returns:
        VisParams object

    Raises:
        ValueError: If name not found
    """
    if name not in VIS_PARAMS_REGISTRY:
        available = ", ".join(VIS_PARAMS_REGISTRY.keys())
        raise ValueError(f"Unknown vis params: {name}. Available: {available}")
    return VIS_PARAMS_REGISTRY[name]


def get_colormap(name: str) -> List[str]:
    """
    Get color palette by name.

    Args:
        name: Palette name (ndvi, nbr, dndvi, etc.)

    Returns:
        List of hex color strings
    """
    params = get_vis_params(name)
    return params.palette or []


def interpolate_color(value: float, min_val: float, max_val: float, palette: List[str]) -> str:
    """
    Interpolate color from palette based on value.

    Args:
        value: Value to map
        min_val: Minimum of value range
        max_val: Maximum of value range
        palette: List of hex colors

    Returns:
        Hex color string
    """
    if len(palette) == 0:
        return "#808080"  # Gray default

    # Normalize value to 0-1
    normalized = (value - min_val) / (max_val - min_val)
    normalized = max(0, min(1, normalized))

    # Map to palette index
    index = int(normalized * (len(palette) - 1))
    return palette[index]


# =============================================================================
# LEGEND GENERATION
# =============================================================================

CHANGE_CLASS_LABELS = {
    "en": {
        1: "Strong Loss",
        2: "Moderate Loss",
        3: "Stable",
        4: "Moderate Gain",
        5: "Strong Gain",
    },
    "es": {
        1: "Pérdida Fuerte",
        2: "Pérdida Moderada",
        3: "Estable",
        4: "Ganancia Moderada",
        5: "Ganancia Fuerte",
    },
}


def get_legend_html(
    vis_type: str = "change_class",
    language: str = "en",
    title: Optional[str] = None,
) -> str:
    """
    Generate HTML legend for visualization.

    Args:
        vis_type: Type of visualization
        language: Language for labels
        title: Optional custom title

    Returns:
        HTML string for legend
    """
    if vis_type == "change_class":
        labels = CHANGE_CLASS_LABELS.get(language, CHANGE_CLASS_LABELS["en"])
        palette = CHANGE_CLASS_PALETTE
        title = title or ("Vegetation Change" if language == "en" else "Cambio de Vegetación")

        items = ""
        for i, (class_num, label) in enumerate(labels.items()):
            color = palette[i]
            items += f"""
            <div style="display: flex; align-items: center; margin: 2px 0;">
                <div style="width: 20px; height: 20px; background-color: {color}; margin-right: 8px; border: 1px solid #333;"></div>
                <span>{label}</span>
            </div>
            """

        return f"""
        <div style="padding: 10px; background: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
            <h4 style="margin: 0 0 10px 0;">{title}</h4>
            {items}
        </div>
        """

    elif vis_type == "ndvi":
        title = title or "NDVI"
        return _generate_gradient_legend(
            title=title,
            palette=NDVI_PALETTE,
            min_val=-0.2,
            max_val=0.8,
            min_label="Bare/Water",
            max_label="Dense Vegetation",
        )

    elif vis_type == "nbr":
        title = title or "NBR"
        return _generate_gradient_legend(
            title=title,
            palette=NBR_PALETTE,
            min_val=-0.5,
            max_val=0.8,
            min_label="Burned",
            max_label="Healthy",
        )

    else:
        return ""


def _generate_gradient_legend(
    title: str,
    palette: List[str],
    min_val: float,
    max_val: float,
    min_label: str,
    max_label: str,
) -> str:
    """Generate a gradient legend."""
    gradient = ", ".join(palette)

    return f"""
    <div style="padding: 10px; background: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
        <h4 style="margin: 0 0 10px 0;">{title}</h4>
        <div style="display: flex; align-items: center;">
            <span style="font-size: 12px;">{min_val}</span>
            <div style="flex: 1; height: 20px; margin: 0 8px; background: linear-gradient(to right, {gradient}); border: 1px solid #333;"></div>
            <span style="font-size: 12px;">{max_val}</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 11px; margin-top: 2px;">
            <span>{min_label}</span>
            <span>{max_label}</span>
        </div>
    </div>
    """


def get_matplotlib_cmap(name: str):
    """
    Get matplotlib colormap from palette.

    Args:
        name: Palette name

    Returns:
        matplotlib LinearSegmentedColormap
    """
    from matplotlib.colors import LinearSegmentedColormap

    palette = get_colormap(name)
    if not palette:
        return None

    # Convert hex to RGB tuples
    rgb_colors = []
    for hex_color in palette:
        hex_color = hex_color.lstrip("#")
        rgb = tuple(int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))
        rgb_colors.append(rgb)

    return LinearSegmentedColormap.from_list(name, rgb_colors)
