# 03. Módulos de Entrada/Salida

## veg_change_engine/io/

Los módulos IO manejan la carga de datos, exportación de resultados y persistencia.

---

## aoi.py - Carga de Áreas de Interés

### Propósito
Cargar y procesar geometrías de múltiples formatos para usarlas como áreas de análisis en Earth Engine.

### Patrón de Diseño: Strategy + Registry

```python
class AOILoader(ABC):
    """Clase abstracta para cargadores de AOI."""

    @abstractmethod
    def load(self, filepath: str) -> gpd.GeoDataFrame:
        """Carga AOI desde archivo."""
        pass

    @abstractmethod
    def supports(self, filepath: str) -> bool:
        """Verifica si soporta el formato."""
        pass
```

### Cargadores Implementados

| Loader | Extensiones | Descripción |
|--------|-------------|-------------|
| `GeoPackageLoader` | .gpkg | SQLite con geometrías |
| `ShapefileLoader` | .shp | ESRI Shapefile |
| `GeoJSONLoader` | .geojson, .json | JSON geoespacial |
| `KMZLoader` | .kmz | Google Earth (comprimido) |
| `KMLLoader` | .kml | Google Earth (XML) |

### Registro de Cargadores

```python
LOADER_REGISTRY: list[AOILoader] = [
    GeoPackageLoader(),
    ShapefileLoader(),
    GeoJSONLoader(),
    KMZLoader(),
    KMLLoader(),
]

def get_loader(filepath: str) -> AOILoader:
    """Selecciona el cargador apropiado."""
    for loader in LOADER_REGISTRY:
        if loader.supports(filepath):
            return loader
    raise ValueError(f"No loader found for: {filepath}")
```

### Carga de KMZ con Fallbacks

Los archivos KMZ/KML pueden fallar con diferentes drivers. El código implementa múltiples estrategias:

```python
def _read_kml_file(kml_path: str) -> gpd.GeoDataFrame:
    """Lee KML con múltiples métodos de fallback."""
    errors = []

    # Método 1: Driver LIBKML
    try:
        gdf = gpd.read_file(kml_path, driver="LIBKML")
        if len(gdf) > 0:
            return gdf
    except Exception as e:
        errors.append(f"LIBKML: {e}")

    # Método 2: Driver KML
    try:
        gdf = gpd.read_file(kml_path, driver="KML")
        if len(gdf) > 0:
            return gdf
    except Exception as e:
        errors.append(f"KML: {e}")

    # Método 3: pyogrio
    try:
        gdf = gpd.read_file(kml_path, engine="pyogrio")
        if len(gdf) > 0:
            return gdf
    except Exception as e:
        errors.append(f"pyogrio: {e}")

    # Método 4: Parser XML manual
    try:
        gdf = _parse_kml_manually(kml_path)
        return gdf
    except Exception as e:
        errors.append(f"manual: {e}")

    raise ValueError(f"Failed to read KML: {'; '.join(errors)}")
```

### Parser KML Manual

Cuando los drivers fallan, se parsea el XML directamente:

```python
def _parse_kml_manually(kml_path: str) -> gpd.GeoDataFrame:
    """Parsea KML usando xml.etree."""
    import xml.etree.ElementTree as ET
    from shapely.geometry import Point, LineString, Polygon

    tree = ET.parse(kml_path)
    root = tree.getroot()

    # Namespace KML
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    # Buscar Placemarks
    placemarks = root.findall('.//Placemark')
    if not placemarks:
        placemarks = root.findall('.//{http://www.opengis.net/kml/2.2}Placemark')

    geometries = []
    for pm in placemarks:
        # Extraer Point, LineString o Polygon
        # ... (ver código completo)
        pass

    return gpd.GeoDataFrame({'geometry': geometries})
```

### Funciones de Conversión

#### `geodataframe_to_ee()`
```python
def geodataframe_to_ee(
    gdf: gpd.GeoDataFrame,
    simplify_tolerance: Optional[float] = None,
) -> ee.FeatureCollection:
    """Convierte GeoDataFrame a FeatureCollection de EE."""
```

#### `aoi_to_ee_geometry()`
```python
def aoi_to_ee_geometry(gdf: gpd.GeoDataFrame) -> ee.Geometry:
    """Convierte AOI a geometría única de EE."""
```

### Funciones Utilitarias

| Función | Descripción |
|---------|-------------|
| `validate_geometry()` | Repara geometrías inválidas |
| `create_buffered_aoi()` | Crea buffer en metros |
| `get_aoi_bounds()` | Obtiene bounding box |
| `get_aoi_centroid()` | Obtiene centroide |
| `get_aoi_area()` | Calcula área en hectáreas |

---

## exporters.py - Exportación de Resultados

### Propósito
Exportar imágenes procesadas a diferentes destinos.

### Exportadores Disponibles

#### `export_to_drive()`
```python
def export_to_drive(
    image: ee.Image,
    description: str,
    folder: str,
    region: ee.Geometry,
    scale: int = 30,
    crs: str = 'EPSG:4326',
) -> ee.batch.Task:
    """Exporta imagen a Google Drive."""

    task = ee.batch.Export.image.toDrive(
        image=image,
        description=description,
        folder=folder,
        region=region,
        scale=scale,
        crs=crs,
        maxPixels=1e13,
        fileFormat='GeoTIFF'
    )
    task.start()
    return task
```

#### `export_to_asset()`
```python
def export_to_asset(
    image: ee.Image,
    asset_id: str,
    region: ee.Geometry,
    scale: int = 30,
) -> ee.batch.Task:
    """Exporta imagen a EE Asset."""

    task = ee.batch.Export.image.toAsset(
        image=image,
        description=asset_id.split('/')[-1],
        assetId=asset_id,
        region=region,
        scale=scale,
        maxPixels=1e13
    )
    task.start()
    return task
```

#### `export_to_cloud_storage()`
```python
def export_to_cloud_storage(
    image: ee.Image,
    bucket: str,
    file_path: str,
    region: ee.Geometry,
    scale: int = 30,
) -> ee.batch.Task:
    """Exporta imagen a Google Cloud Storage."""
```

### Monitoreo de Tareas

```python
def wait_for_task(task: ee.batch.Task, timeout: int = 3600) -> bool:
    """Espera a que la tarea termine."""
    import time

    start_time = time.time()
    while task.active():
        if time.time() - start_time > timeout:
            return False
        time.sleep(10)

    return task.status()['state'] == 'COMPLETED'
```

---

## cache.py - Sistema de Caché

### Propósito
Evitar consumo repetido de la API de Earth Engine mediante persistencia de resultados.

### Niveles de Caché

```
┌─────────────────────────────────────────────────────────┐
│                   SISTEMA DE CACHÉ                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Nivel 1: EE Assets (permanente)                        │
│  ├── Composites procesados                              │
│  ├── Índices calculados                                 │
│  └── Mapas de cambio                                    │
│                                                          │
│  Nivel 2: Tile URLs (24h TTL)                           │
│  ├── URLs de tiles para visualización                   │
│  └── Evita regenerar tiles                              │
│                                                          │
│  Nivel 3: Metadata local (SQLite/JSON)                  │
│  ├── Configuraciones de análisis                        │
│  ├── Estadísticas calculadas                            │
│  └── Historial de ejecuciones                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### AssetCache

```python
class AssetCache:
    """Caché basado en EE Assets."""

    def __init__(self, base_path: str):
        self.base_path = base_path

    def get_asset_id(self, name: str, params: Dict) -> str:
        """Genera ID único basado en parámetros."""
        param_hash = hashlib.md5(
            json.dumps(params, sort_keys=True).encode()
        ).hexdigest()[:8]
        return f"{self.base_path}/{name}_{param_hash}"

    def exists(self, asset_id: str) -> bool:
        """Verifica si el asset existe."""
        try:
            ee.data.getAsset(asset_id)
            return True
        except ee.EEException:
            return False

    def get(self, asset_id: str) -> Optional[ee.Image]:
        """Obtiene imagen del caché."""
        if self.exists(asset_id):
            return ee.Image(asset_id)
        return None

    def put(self, image: ee.Image, asset_id: str, region: ee.Geometry):
        """Guarda imagen en caché."""
        task = export_to_asset(image, asset_id, region)
        wait_for_task(task)
```

### LocalCache

```python
class LocalCache:
    """Caché local para metadata y URLs."""

    def __init__(self, cache_dir: str = ".veg_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_tile_url(self, key: str) -> Optional[str]:
        """Obtiene URL de tile cacheada."""
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            data = json.loads(cache_file.read_text())
            # Verificar TTL (24 horas)
            if time.time() - data['timestamp'] < 86400:
                return data['url']
        return None

    def set_tile_url(self, key: str, url: str):
        """Guarda URL de tile."""
        cache_file = self.cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps({
            'url': url,
            'timestamp': time.time()
        }))
```

### Uso del Caché en Pipeline

```python
def get_or_create_composite(aoi, period, config, cache):
    """Obtiene composite del caché o lo crea."""

    # Generar ID único
    asset_id = cache.get_asset_id('composite', {
        'period': period,
        'aoi_hash': hash_geometry(aoi),
    })

    # Intentar obtener del caché
    cached = cache.get(asset_id)
    if cached is not None:
        return cached

    # Crear nuevo composite
    composite = create_composite(aoi, period, config)

    # Guardar en caché (async)
    cache.put(composite, asset_id, aoi)

    return composite
```

### Diagrama de Flujo del Caché

```
┌──────────────┐
│   Request    │
│   Composite  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  Check       │────▶│  Asset       │
│  Asset Cache │ hit │  Exists!     │
└──────┬───────┘     └──────┬───────┘
       │ miss               │
       ▼                    │
┌──────────────┐            │
│  Create      │            │
│  Composite   │            │
└──────┬───────┘            │
       │                    │
       ▼                    │
┌──────────────┐            │
│  Export to   │            │
│  Asset       │            │
└──────┬───────┘            │
       │                    │
       ▼                    ▼
┌──────────────────────────────┐
│      Return ee.Image         │
└──────────────────────────────┘
```
