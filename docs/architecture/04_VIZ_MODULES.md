# 04. Módulos de Visualización

## veg_change_engine/viz/

Los módulos de visualización manejan la presentación gráfica de resultados.

---

## colors.py - Paletas de Colores

### Propósito
Define paletas de colores consistentes para visualización de índices y cambios.

### Paletas de Índices

```python
INDEX_PALETTES = {
    'ndvi': [
        '#d73027',  # -1.0 - Agua/suelo (rojo)
        '#fc8d59',  # -0.5
        '#fee08b',  # 0.0 - Suelo desnudo (amarillo)
        '#d9ef8b',  # 0.3
        '#91cf60',  # 0.5 - Vegetación moderada
        '#1a9850',  # 0.8 - Vegetación densa (verde)
    ],
    'nbr': [
        '#7f3b08',  # Muy quemado (marrón)
        '#b35806',
        '#e08214',
        '#fdb863',
        '#fee0b6',
        '#d8daeb',
        '#b2abd2',
        '#8073ac',
        '#542788',  # Sin quemar
    ],
    'ndwi': [
        '#a50026',  # Seco
        '#d73027',
        '#f46d43',
        '#fdae61',
        '#fee090',
        '#e0f3f8',
        '#abd9e9',
        '#74add1',
        '#4575b4',
        '#313695',  # Agua
    ],
}
```

### Paleta de Cambios (SGC-inspired)

```python
CHANGE_PALETTE = {
    1: '#d7191c',  # Pérdida fuerte - Rojo
    2: '#fdae61',  # Pérdida moderada - Naranja
    3: '#ffffbf',  # Estable - Amarillo
    4: '#a6d96a',  # Ganancia moderada - Verde claro
    5: '#1a9641',  # Ganancia fuerte - Verde oscuro
}

CHANGE_LABELS = {
    1: 'Pérdida Fuerte',
    2: 'Pérdida Moderada',
    3: 'Estable',
    4: 'Ganancia Moderada',
    5: 'Ganancia Fuerte',
}
```

### Funciones de Color

```python
def get_index_palette(index: str) -> List[str]:
    """Obtiene paleta para un índice."""
    return INDEX_PALETTES.get(index, INDEX_PALETTES['ndvi'])

def get_change_color(class_value: int) -> str:
    """Obtiene color para una clase de cambio."""
    return CHANGE_PALETTE.get(class_value, '#808080')

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convierte hex a RGB."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_colormap(palette: List[str], n_colors: int = 256) -> np.ndarray:
    """Crea colormap interpolado."""
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list('custom', palette, N=n_colors)
    return cmap
```

### Visualización de Paletas

```
NDVI Palette:
█████ -1.0  Agua/Nubes (rojo)
█████ -0.5
█████  0.0  Suelo desnudo (amarillo)
█████  0.3  Vegetación escasa
█████  0.5  Vegetación moderada
█████  0.8  Vegetación densa (verde)

Change Palette:
█████  1  Pérdida Fuerte (rojo)
█████  2  Pérdida Moderada (naranja)
█████  3  Estable (amarillo)
█████  4  Ganancia Moderada (verde claro)
█████  5  Ganancia Fuerte (verde oscuro)
```

---

## maps.py - Mapas Interactivos

### Propósito
Genera mapas interactivos con Folium para visualización web.

### Clase Principal: VegChangeMap

```python
class VegChangeMap:
    """Generador de mapas interactivos."""

    def __init__(
        self,
        center: Tuple[float, float] = None,
        zoom: int = 12,
        basemap: str = 'OpenStreetMap',
    ):
        self.center = center or [4.5, -75.5]  # Colombia default
        self.zoom = zoom
        self.map = folium.Map(
            location=self.center,
            zoom_start=zoom,
            tiles=basemap,
        )
```

### Métodos de Capa

#### `add_ee_layer()`
```python
def add_ee_layer(
    self,
    image: ee.Image,
    vis_params: Dict,
    name: str,
    opacity: float = 1.0,
) -> 'VegChangeMap':
    """Añade capa de Earth Engine."""

    # Obtener URL de tiles
    map_id = image.getMapId(vis_params)
    tile_url = map_id['tile_fetcher'].url_format

    # Añadir como TileLayer
    folium.TileLayer(
        tiles=tile_url,
        attr='Google Earth Engine',
        name=name,
        overlay=True,
        control=True,
        opacity=opacity,
    ).add_to(self.map)

    return self
```

#### `add_aoi_layer()`
```python
def add_aoi_layer(
    self,
    gdf: gpd.GeoDataFrame,
    name: str = 'AOI',
    style: Dict = None,
) -> 'VegChangeMap':
    """Añade capa de AOI."""

    default_style = {
        'color': '#ff7800',
        'weight': 2,
        'fillOpacity': 0.1,
    }
    style = style or default_style

    folium.GeoJson(
        gdf.__geo_interface__,
        name=name,
        style_function=lambda x: style,
    ).add_to(self.map)

    return self
```

#### `add_change_layer()`
```python
def add_change_layer(
    self,
    change_image: ee.Image,
    name: str = 'Vegetation Change',
) -> 'VegChangeMap':
    """Añade capa de cambio clasificado."""

    vis_params = {
        'min': 1,
        'max': 5,
        'palette': list(CHANGE_PALETTE.values()),
    }

    return self.add_ee_layer(change_image, vis_params, name)
```

### Componentes de Mapa

#### `add_legend()`
```python
def add_legend(
    self,
    title: str = 'Cambio de Vegetación',
    classes: Dict = None,
) -> 'VegChangeMap':
    """Añade leyenda al mapa."""

    classes = classes or {
        '🔴 Pérdida Fuerte': '#d7191c',
        '🟠 Pérdida Moderada': '#fdae61',
        '🟡 Estable': '#ffffbf',
        '🟢 Ganancia Moderada': '#a6d96a',
        '🌲 Ganancia Fuerte': '#1a9641',
    }

    # HTML de leyenda
    legend_html = f'''
    <div style="position: fixed; bottom: 50px; right: 50px;
                background: white; padding: 10px; border-radius: 5px;
                border: 2px solid grey; z-index: 1000;">
        <h4 style="margin: 0 0 10px 0;">{title}</h4>
    '''

    for label, color in classes.items():
        legend_html += f'''
        <p style="margin: 5px;">
            <span style="background: {color}; padding: 0 10px;">&nbsp;</span>
            {label}
        </p>
        '''

    legend_html += '</div>'

    self.map.get_root().html.add_child(folium.Element(legend_html))
    return self
```

#### `add_layer_control()`
```python
def add_layer_control(self) -> 'VegChangeMap':
    """Añade control de capas."""
    folium.LayerControl(collapsed=False).add_to(self.map)
    return self
```

### Función de Generación Rápida

```python
def create_analysis_map(
    results: Dict,
    aoi: gpd.GeoDataFrame,
    reference_period: str = '1990s',
    comparison_period: str = 'present',
) -> VegChangeMap:
    """Crea mapa completo de análisis."""

    # Calcular centro del AOI
    centroid = aoi.unary_union.centroid
    center = [centroid.y, centroid.x]

    # Crear mapa
    vmap = VegChangeMap(center=center, zoom=12)

    # Añadir AOI
    vmap.add_aoi_layer(aoi, name='Área de Estudio')

    # Añadir composite de referencia
    if reference_period in results['composites']:
        vmap.add_ee_layer(
            results['composites'][reference_period],
            {'bands': ['red', 'green', 'blue'], 'min': 0, 'max': 3000},
            f'Composite {reference_period}'
        )

    # Añadir composite de comparación
    if comparison_period in results['composites']:
        vmap.add_ee_layer(
            results['composites'][comparison_period],
            {'bands': ['red', 'green', 'blue'], 'min': 0, 'max': 3000},
            f'Composite {comparison_period}'
        )

    # Añadir cambio
    change_key = f'{reference_period}_vs_{comparison_period}'
    if change_key in results['changes']:
        vmap.add_change_layer(
            results['changes'][change_key]['classified'],
            name='Cambio de Vegetación'
        )

    # Añadir leyenda y controles
    vmap.add_legend()
    vmap.add_layer_control()

    return vmap
```

### Diagrama de Arquitectura de Mapas

```
┌─────────────────────────────────────────────────────────────┐
│                      VegChangeMap                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Basemap    │  │   AOI Layer  │  │  EE Layers   │       │
│  │  OpenStreet  │  │   GeoJSON    │  │  Tile URLs   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │                  Composites                       │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │       │
│  │  │  1990s   │  │  2010s   │  │ Present  │        │       │
│  │  │   RGB    │  │   RGB    │  │   RGB    │        │       │
│  │  └──────────┘  └──────────┘  └──────────┘        │       │
│  └──────────────────────────────────────────────────┘       │
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │                 Change Layer                      │       │
│  │  ┌────────────────────────────────────────┐      │       │
│  │  │  Classified Change (1-5)               │      │       │
│  │  │  🔴🟠🟡🟢🌲                              │      │       │
│  │  └────────────────────────────────────────┘      │       │
│  └──────────────────────────────────────────────────┘       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │    Legend    │  │ Layer Control│                         │
│  │   (HTML)     │  │  (Folium)    │                         │
│  └──────────────┘  └──────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Exportación de Mapas

```python
def save_map(self, filepath: str) -> str:
    """Guarda mapa como HTML."""
    self.map.save(filepath)
    return filepath

def to_streamlit(self) -> 'streamlit_folium.folium_static':
    """Renderiza en Streamlit."""
    from streamlit_folium import folium_static
    return folium_static(self.map)
```
