# 08. Referencia de API

## veg_change_engine

### Función Principal

```python
from veg_change_engine import analyze_vegetation_change

results = analyze_vegetation_change(
    aoi: Union[ee.Geometry, gpd.GeoDataFrame, str],
    periods: List[str] = ["1990s", "present"],
    indices: List[str] = ["ndvi"],
    reference_period: str = "1990s",
    config: Optional[VegChangeConfig] = None,
) -> Dict
```

**Parámetros:**
| Nombre | Tipo | Descripción |
|--------|------|-------------|
| `aoi` | `ee.Geometry`, `GeoDataFrame`, `str` | Área de interés |
| `periods` | `List[str]` | Períodos a analizar |
| `indices` | `List[str]` | Índices espectrales |
| `reference_period` | `str` | Período base para comparación |
| `config` | `VegChangeConfig` | Configuración opcional |

**Retorna:**
```python
{
    'config': VegChangeConfig,
    'aoi': ee.Geometry,
    'composites': Dict[str, ee.Image],
    'indices': Dict[str, Dict[str, ee.Image]],
    'changes': Dict[str, Dict[str, Dict]],
    'statistics': Dict[str, Dict[str, Dict]],
}
```

---

## veg_change_engine.config

### VegChangeConfig

```python
from veg_change_engine.config import VegChangeConfig

config = VegChangeConfig(
    site_name: str = "Default Site",
    description: str = "",
    periods: List[str] = ["1990s", "present"],
    indices: List[str] = ["ndvi", "nbr"],
    reference_period: str = "1990s",
    scale: int = 30,
    crs: str = "EPSG:4326",
    cloud_threshold: float = 20.0,
    use_cache: bool = True,
    cache_to_asset: bool = False,
    asset_folder: Optional[str] = None,
    export_composites: bool = False,
    export_changes: bool = False,
    export_folder: str = "VegChange_Exports",
)
```

### Constantes

```python
from veg_change_engine.config import (
    DEFAULT_PROJECT,      # "geoconcret-474619"
    DEFAULT_SCALE,        # 30
    DEFAULT_CRS,          # "EPSG:4326"
    TEMPORAL_PERIODS,     # Dict con períodos
    BAND_MAPPING,         # Dict con mapeo de bandas
    CHANGE_THRESHOLDS,    # Dict con umbrales
)
```

---

## veg_change_engine.core.composites

### create_composite()

```python
from veg_change_engine.core.composites import create_composite

composite = create_composite(
    aoi: ee.Geometry,
    period: str,
    config: Optional[VegChangeConfig] = None,
) -> ee.Image
```

### mask_clouds_landsat()

```python
from veg_change_engine.core.composites import mask_clouds_landsat

masked = mask_clouds_landsat(image: ee.Image) -> ee.Image
```

### mask_clouds_sentinel2()

```python
from veg_change_engine.core.composites import mask_clouds_sentinel2

masked = mask_clouds_sentinel2(image: ee.Image) -> ee.Image
```

### harmonize_bands()

```python
from veg_change_engine.core.composites import harmonize_bands

harmonized = harmonize_bands(
    image: ee.Image,
    sensor: str,
) -> ee.Image
```

---

## veg_change_engine.core.indices

### SpectralIndex (ABC)

```python
from veg_change_engine.core.indices import SpectralIndex

class SpectralIndex(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def calculate(self, image: ee.Image) -> ee.Image: ...
```

### get_index()

```python
from veg_change_engine.core.indices import get_index

ndvi_calculator = get_index("ndvi") -> SpectralIndex
```

### calculate_indices()

```python
from veg_change_engine.core.indices import calculate_indices

image_with_indices = calculate_indices(
    image: ee.Image,
    indices: List[str],
) -> ee.Image
```

### Índices Disponibles

| Nombre | Clase | Fórmula |
|--------|-------|---------|
| `ndvi` | `NDVIIndex` | `(NIR-RED)/(NIR+RED)` |
| `nbr` | `NBRIndex` | `(NIR-SWIR2)/(NIR+SWIR2)` |
| `ndwi` | `NDWIIndex` | `(GREEN-NIR)/(GREEN+NIR)` |
| `evi` | `EVIIndex` | `2.5*(NIR-RED)/(NIR+6*RED-7.5*BLUE+1)` |
| `ndmi` | `NDMIIndex` | `(NIR-SWIR1)/(NIR+SWIR1)` |

---

## veg_change_engine.core.change

### calculate_change()

```python
from veg_change_engine.core.change import calculate_change

delta = calculate_change(
    before: ee.Image,
    after: ee.Image,
    index: str = "ndvi",
) -> ee.Image
```

### classify_change()

```python
from veg_change_engine.core.change import classify_change

classified = classify_change(
    change_image: ee.Image,
    thresholds: Optional[Dict] = None,
) -> ee.Image
```

**Thresholds por defecto:**
```python
{
    'strong_loss': -0.2,
    'moderate_loss': -0.1,
    'moderate_gain': 0.1,
    'strong_gain': 0.2,
}
```

### get_change_statistics()

```python
from veg_change_engine.core.change import get_change_statistics

stats = get_change_statistics(
    classified: ee.Image,
    aoi: ee.Geometry,
    scale: int = 30,
) -> Dict
```

**Retorna:**
```python
{
    'total_pixels': int,
    'class_counts': Dict[int, int],
    'class_percentages': Dict[int, float],
    'area_ha': Dict[int, float],
}
```

---

## veg_change_engine.io.aoi

### load_aoi()

```python
from veg_change_engine.io.aoi import load_aoi

gdf = load_aoi(filepath: str) -> gpd.GeoDataFrame
```

**Formatos soportados:** `.kmz`, `.kml`, `.geojson`, `.json`, `.gpkg`, `.shp`

### aoi_to_ee_geometry()

```python
from veg_change_engine.io.aoi import aoi_to_ee_geometry

geometry = aoi_to_ee_geometry(
    gdf: gpd.GeoDataFrame
) -> ee.Geometry
```

### geodataframe_to_ee()

```python
from veg_change_engine.io.aoi import geodataframe_to_ee

fc = geodataframe_to_ee(
    gdf: gpd.GeoDataFrame,
    simplify_tolerance: Optional[float] = None,
) -> ee.FeatureCollection
```

### validate_geometry()

```python
from veg_change_engine.io.aoi import validate_geometry

cleaned = validate_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame
```

### create_buffered_aoi()

```python
from veg_change_engine.io.aoi import create_buffered_aoi

buffered = create_buffered_aoi(
    gdf: gpd.GeoDataFrame,
    buffer_distance: float,  # metros
    cap_style: int = 1,      # 1=round, 2=flat, 3=square
) -> gpd.GeoDataFrame
```

### Funciones Utilitarias

```python
from veg_change_engine.io.aoi import (
    get_aoi_bounds,    # -> Dict (minx, miny, maxx, maxy)
    get_aoi_centroid,  # -> Dict (lat, lon)
    get_aoi_area,      # -> float (hectáreas)
)
```

---

## veg_change_engine.io.exporters

### export_to_drive()

```python
from veg_change_engine.io.exporters import export_to_drive

task = export_to_drive(
    image: ee.Image,
    description: str,
    folder: str,
    region: ee.Geometry,
    scale: int = 30,
    crs: str = 'EPSG:4326',
) -> ee.batch.Task
```

### export_to_asset()

```python
from veg_change_engine.io.exporters import export_to_asset

task = export_to_asset(
    image: ee.Image,
    asset_id: str,
    region: ee.Geometry,
    scale: int = 30,
) -> ee.batch.Task
```

### wait_for_task()

```python
from veg_change_engine.io.exporters import wait_for_task

success = wait_for_task(
    task: ee.batch.Task,
    timeout: int = 3600,  # segundos
) -> bool
```

---

## veg_change_engine.io.cache

### AssetCache

```python
from veg_change_engine.io.cache import AssetCache

cache = AssetCache(base_path: str)

# Métodos
asset_id = cache.get_asset_id(name: str, params: Dict) -> str
exists = cache.exists(asset_id: str) -> bool
image = cache.get(asset_id: str) -> Optional[ee.Image]
cache.put(image: ee.Image, asset_id: str, region: ee.Geometry)
```

### LocalCache

```python
from veg_change_engine.io.cache import LocalCache

cache = LocalCache(cache_dir: str = ".veg_cache")

# Métodos
url = cache.get_tile_url(key: str) -> Optional[str]
cache.set_tile_url(key: str, url: str)
```

---

## veg_change_engine.viz.colors

### Paletas

```python
from veg_change_engine.viz.colors import (
    INDEX_PALETTES,   # Dict[str, List[str]]
    CHANGE_PALETTE,   # Dict[int, str]
    CHANGE_LABELS,    # Dict[int, str]
)
```

### Funciones

```python
from veg_change_engine.viz.colors import (
    get_index_palette,  # (index: str) -> List[str]
    get_change_color,   # (class_value: int) -> str
    hex_to_rgb,         # (hex_color: str) -> Tuple[int, int, int]
    create_colormap,    # (palette: List[str], n: int) -> np.ndarray
)
```

---

## veg_change_engine.viz.maps

### VegChangeMap

```python
from veg_change_engine.viz.maps import VegChangeMap

vmap = VegChangeMap(
    center: Tuple[float, float] = None,
    zoom: int = 12,
    basemap: str = 'OpenStreetMap',
)

# Métodos (fluent interface)
vmap.add_ee_layer(image, vis_params, name, opacity=1.0)
vmap.add_aoi_layer(gdf, name='AOI', style=None)
vmap.add_change_layer(change_image, name='Change')
vmap.add_legend(title='Cambio', classes=None)
vmap.add_layer_control()

# Exportación
vmap.save_map(filepath: str) -> str
vmap.to_streamlit() -> folium_static
```

### create_analysis_map()

```python
from veg_change_engine.viz.maps import create_analysis_map

vmap = create_analysis_map(
    results: Dict,
    aoi: gpd.GeoDataFrame,
    reference_period: str = '1990s',
    comparison_period: str = 'present',
) -> VegChangeMap
```

---

## veg_change_engine.ee_init

### initialize_ee()

```python
from veg_change_engine.ee_init import initialize_ee

success = initialize_ee(project: str = None) -> bool
```

### get_ee_status()

```python
from veg_change_engine.ee_init import get_ee_status

status = get_ee_status() -> Dict
# {'initialized': bool, 'project': str or None}
```

### authenticate_ee()

```python
from veg_change_engine.ee_init import authenticate_ee

success = authenticate_ee() -> bool
```

---

## Ejemplo de Uso Completo

```python
import ee
from veg_change_engine import analyze_vegetation_change
from veg_change_engine.config import VegChangeConfig
from veg_change_engine.io.aoi import load_aoi
from veg_change_engine.viz.maps import create_analysis_map
from veg_change_engine.ee_init import initialize_ee

# 1. Inicializar Earth Engine
initialize_ee(project="my-project-id")

# 2. Configurar análisis
config = VegChangeConfig(
    site_name="Mi Sitio de Estudio",
    periods=["1990s", "2010s", "present"],
    indices=["ndvi", "nbr"],
    reference_period="1990s",
    scale=30,
)

# 3. Cargar AOI
gdf = load_aoi("area_estudio.kmz")

# 4. Ejecutar análisis
results = analyze_vegetation_change(
    aoi=gdf,
    config=config,
)

# 5. Ver estadísticas
for change_key, stats in results['statistics'].items():
    print(f"\n{change_key}:")
    for index, data in stats.items():
        print(f"  {index}:")
        for cls, area in data['area_ha'].items():
            print(f"    Clase {cls}: {area:.1f} ha")

# 6. Crear mapa
vmap = create_analysis_map(results, gdf)
vmap.save_map("resultado.html")
```
