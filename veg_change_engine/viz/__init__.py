"""
Visualization module for vegetation change analysis.

- maps: Folium/Leaflet map generation
- colors: Color palettes and visualization parameters
"""

from veg_change_engine.viz.maps import (
    create_folium_map,
    add_composite_layer,
    add_change_layer,
    add_index_layer,
    add_aoi_layer,
    create_split_map,
    create_comparison_map,
)

from veg_change_engine.viz.colors import (
    NDVI_VIS_PARAMS,
    NBR_VIS_PARAMS,
    CHANGE_VIS_PARAMS,
    RGB_VIS_PARAMS,
    get_colormap,
    get_legend_html,
)

__all__ = [
    # Maps
    "create_folium_map",
    "add_composite_layer",
    "add_change_layer",
    "add_index_layer",
    "add_aoi_layer",
    "create_split_map",
    "create_comparison_map",
    # Colors
    "NDVI_VIS_PARAMS",
    "NBR_VIS_PARAMS",
    "CHANGE_VIS_PARAMS",
    "RGB_VIS_PARAMS",
    "get_colormap",
    "get_legend_html",
]
