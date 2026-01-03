"""
Interactive map generation using Folium and geemap.

Provides:
- Folium map creation with Earth Engine layers
- Split/comparison maps for temporal analysis
- Layer controls and legends

Follows SOLID principles:
- Single Responsibility: Each function adds one type of layer
- Open/Closed: New layer types via layer factory
"""

from typing import Dict, List, Optional, Tuple, Union
import ee
import folium
from folium import plugins

from veg_change_engine.viz.colors import (
    get_vis_params,
    get_legend_html,
    NDVI_VIS_PARAMS,
    NBR_VIS_PARAMS,
    CHANGE_VIS_PARAMS,
    RGB_VIS_PARAMS,
)


# =============================================================================
# MAP CREATION
# =============================================================================

def create_folium_map(
    center: Tuple[float, float] = (4.5, -75.5),
    zoom: int = 12,
    basemap: str = "CartoDB positron",
    height: str = "600px",
    width: str = "100%",
) -> folium.Map:
    """
    Create a base Folium map.

    Args:
        center: (lat, lon) center coordinates
        zoom: Initial zoom level
        basemap: Base map tile name
        height: Map height (CSS)
        width: Map width (CSS)

    Returns:
        folium.Map object
    """
    # Basemap options
    basemaps = {
        "CartoDB positron": "cartodbpositron",
        "CartoDB dark": "cartodbdark_matter",
        "OpenStreetMap": "openstreetmap",
        "Stamen Terrain": "Stamen Terrain",
    }

    tiles = basemaps.get(basemap, basemap)

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=tiles,
        control_scale=True,
    )

    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)

    return m


def get_ee_tile_url(image: ee.Image, vis_params: Dict) -> str:
    """
    Get tile URL for Earth Engine image.

    Args:
        image: ee.Image to visualize
        vis_params: Visualization parameters

    Returns:
        Tile URL string
    """
    map_id = image.getMapId(vis_params)
    return map_id["tile_fetcher"].url_format


def add_ee_layer(
    m: folium.Map,
    image: ee.Image,
    vis_params: Dict,
    name: str,
    show: bool = True,
    opacity: float = 1.0,
) -> folium.Map:
    """
    Add Earth Engine image layer to Folium map.

    Args:
        m: Folium map
        image: ee.Image to add
        vis_params: Visualization parameters
        name: Layer name
        show: Whether to show layer initially
        opacity: Layer opacity (0-1)

    Returns:
        Updated map
    """
    tile_url = get_ee_tile_url(image, vis_params)

    folium.TileLayer(
        tiles=tile_url,
        attr="Google Earth Engine",
        name=name,
        overlay=True,
        control=True,
        show=show,
        opacity=opacity,
    ).add_to(m)

    return m


# =============================================================================
# SPECIALIZED LAYER FUNCTIONS
# =============================================================================

def add_composite_layer(
    m: folium.Map,
    composite: ee.Image,
    period_name: str,
    vis_type: str = "rgb",
    show: bool = True,
    opacity: float = 1.0,
) -> folium.Map:
    """
    Add temporal composite layer.

    Args:
        m: Folium map
        composite: Composite ee.Image
        period_name: Name for the layer
        vis_type: Visualization type (rgb, false_color, ndvi, nbr)
        show: Whether to show initially
        opacity: Layer opacity

    Returns:
        Updated map
    """
    vis_params = get_vis_params(vis_type).to_dict()

    # For index layers, select the specific band
    if vis_type in ["ndvi", "nbr"]:
        composite = composite.select(vis_type)

    name = f"{period_name} ({vis_type.upper()})"

    return add_ee_layer(m, composite, vis_params, name, show, opacity)


def add_index_layer(
    m: folium.Map,
    image: ee.Image,
    index_name: str,
    layer_name: Optional[str] = None,
    show: bool = True,
    opacity: float = 1.0,
) -> folium.Map:
    """
    Add spectral index layer.

    Args:
        m: Folium map
        image: ee.Image with index band
        index_name: Name of the index (ndvi, nbr)
        layer_name: Custom layer name
        show: Whether to show initially
        opacity: Layer opacity

    Returns:
        Updated map
    """
    vis_params = get_vis_params(index_name).to_dict()
    index_image = image.select(index_name)
    name = layer_name or index_name.upper()

    return add_ee_layer(m, index_image, vis_params, name, show, opacity)


def add_change_layer(
    m: folium.Map,
    change_image: ee.Image,
    comparison_name: str,
    band: str = "change_class",
    show: bool = True,
    opacity: float = 0.8,
) -> folium.Map:
    """
    Add change detection layer.

    Args:
        m: Folium map
        change_image: ee.Image with change bands
        comparison_name: Period comparison name
        band: Band to visualize (change_class, dndvi, dnbr)
        show: Whether to show initially
        opacity: Layer opacity

    Returns:
        Updated map
    """
    if band == "change_class":
        vis_params = get_vis_params("change_class").to_dict()
    elif band.startswith("d"):
        vis_params = get_vis_params(band).to_dict()
    else:
        vis_params = get_vis_params(f"d{band}").to_dict()

    layer_image = change_image.select(band)
    name = f"Change: {comparison_name}"

    return add_ee_layer(m, layer_image, vis_params, name, show, opacity)


def add_aoi_layer(
    m: folium.Map,
    aoi_geojson: Dict,
    name: str = "Area of Interest",
    style: Optional[Dict] = None,
    show: bool = True,
) -> folium.Map:
    """
    Add AOI boundary layer.

    Args:
        m: Folium map
        aoi_geojson: GeoJSON dictionary
        name: Layer name
        style: Style dictionary
        show: Whether to show initially

    Returns:
        Updated map
    """
    if style is None:
        style = {
            "fillColor": "transparent",
            "color": "#ff7800",
            "weight": 3,
            "dashArray": "5, 5",
        }

    folium.GeoJson(
        aoi_geojson,
        name=name,
        style_function=lambda x: style,
        show=show,
    ).add_to(m)

    return m


def add_legend(
    m: folium.Map,
    vis_type: str = "change_class",
    language: str = "en",
    position: str = "bottomright",
) -> folium.Map:
    """
    Add legend to map.

    Args:
        m: Folium map
        vis_type: Visualization type for legend
        language: Language for labels
        position: Legend position

    Returns:
        Updated map
    """
    legend_html = get_legend_html(vis_type, language)

    # Create legend element
    legend = folium.Element(f"""
        <div style="
            position: fixed;
            bottom: 50px;
            right: 50px;
            z-index: 1000;
        ">
            {legend_html}
        </div>
    """)

    m.get_root().html.add_child(legend)

    return m


# =============================================================================
# COMPARISON MAPS
# =============================================================================

def create_split_map(
    left_image: ee.Image,
    right_image: ee.Image,
    left_name: str,
    right_name: str,
    center: Tuple[float, float] = (4.5, -75.5),
    zoom: int = 12,
    vis_type: str = "ndvi",
) -> folium.Map:
    """
    Create a split/swipe comparison map.

    Args:
        left_image: Left side ee.Image
        right_image: Right side ee.Image
        left_name: Left layer name
        right_name: Right layer name
        center: Map center
        zoom: Zoom level
        vis_type: Visualization type

    Returns:
        Folium map with side-by-side comparison
    """
    m = folium.Map(location=center, zoom_start=zoom)

    vis_params = get_vis_params(vis_type).to_dict()

    # Add layers
    left_url = get_ee_tile_url(left_image.select(vis_type), vis_params)
    right_url = get_ee_tile_url(right_image.select(vis_type), vis_params)

    left_layer = folium.TileLayer(
        tiles=left_url,
        attr="Google Earth Engine",
        name=left_name,
    )

    right_layer = folium.TileLayer(
        tiles=right_url,
        attr="Google Earth Engine",
        name=right_name,
    )

    # Add side-by-side control
    plugins.SideBySideLayers(left_layer, right_layer).add_to(m)

    left_layer.add_to(m)
    right_layer.add_to(m)

    folium.LayerControl().add_to(m)

    return m


def create_comparison_map(
    composites: Dict[str, ee.Image],
    center: Tuple[float, float] = (4.5, -75.5),
    zoom: int = 12,
    vis_type: str = "ndvi",
    show_all: bool = False,
) -> folium.Map:
    """
    Create map with multiple temporal layers.

    Args:
        composites: Dictionary of period -> composite
        center: Map center
        zoom: Zoom level
        vis_type: Visualization type
        show_all: Whether to show all layers initially

    Returns:
        Folium map with temporal layers
    """
    m = create_folium_map(center=center, zoom=zoom)

    for i, (period_name, composite) in enumerate(composites.items()):
        # Show only the first layer by default
        show = show_all or (i == 0)

        add_composite_layer(
            m, composite, period_name,
            vis_type=vis_type,
            show=show,
        )

    return m


def create_change_map(
    change_images: Dict[str, ee.Image],
    center: Tuple[float, float] = (4.5, -75.5),
    zoom: int = 12,
    language: str = "en",
) -> folium.Map:
    """
    Create map with change detection layers.

    Args:
        change_images: Dictionary of comparison -> change image
        center: Map center
        zoom: Zoom level
        language: Language for labels

    Returns:
        Folium map with change layers
    """
    m = create_folium_map(center=center, zoom=zoom)

    for i, (comparison_name, change_image) in enumerate(change_images.items()):
        show = (i == 0)
        add_change_layer(m, change_image, comparison_name, show=show)

    # Add legend
    add_legend(m, "change_class", language)

    return m


# =============================================================================
# GEEMAP INTEGRATION (for Streamlit)
# =============================================================================

def create_geemap_map(
    center: Tuple[float, float] = (4.5, -75.5),
    zoom: int = 12,
):
    """
    Create a geemap Map for Streamlit.

    Requires geemap package.

    Args:
        center: Map center (lat, lon)
        zoom: Zoom level

    Returns:
        geemap.Map object
    """
    try:
        import geemap.foliumap as geemap
    except ImportError:
        raise ImportError("geemap is required: pip install geemap")

    m = geemap.Map(
        center=list(center),
        zoom=zoom,
    )

    return m


def add_geemap_layer(
    m,  # geemap.Map
    image: ee.Image,
    vis_params: Dict,
    name: str,
):
    """
    Add layer to geemap Map.

    Args:
        m: geemap.Map object
        image: ee.Image
        vis_params: Visualization parameters
        name: Layer name

    Returns:
        Updated map
    """
    m.addLayer(image, vis_params, name)
    return m
