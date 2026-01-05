# 05. Configuración y Orquestación

## veg_change_engine/config.py

### Propósito
Define la configuración global del sistema y los parámetros por defecto.

### Constantes Globales

```python
# Proyecto de Earth Engine por defecto
DEFAULT_PROJECT = "geoconcret-474619"

# Resolución de exportación en metros
DEFAULT_SCALE = 30

# Sistema de referencia por defecto
DEFAULT_CRS = "EPSG:4326"

# Directorio de caché local
CACHE_DIR = ".veg_cache"
```

### Períodos Temporales

```python
TEMPORAL_PERIODS = {
    "1990s": {
        "start": "1985-01-01",
        "end": "1999-12-31",
        "sensors": ["LANDSAT/LT05/C02/T1_L2"],
        "description": "Era Landsat 5 - Línea base histórica"
    },
    "2000s": {
        "start": "2000-01-01",
        "end": "2009-12-31",
        "sensors": ["LANDSAT/LE07/C02/T1_L2"],
        "description": "Era Landsat 7 - Incluye stripe issues"
    },
    "2010s": {
        "start": "2010-01-01",
        "end": "2019-12-31",
        "sensors": ["LANDSAT/LC08/C02/T1_L2"],
        "description": "Era Landsat 8 - Alta calidad"
    },
    "present": {
        "start": "2020-01-01",
        "end": "2024-12-31",
        "sensors": [
            "LANDSAT/LC08/C02/T1_L2",
            "COPERNICUS/S2_SR_HARMONIZED"
        ],
        "description": "Fusión Landsat 8 + Sentinel-2"
    },
}
```

### Mapeo de Bandas

```python
BAND_MAPPING = {
    "LANDSAT/LT05/C02/T1_L2": {
        "blue": "SR_B1",
        "green": "SR_B2",
        "red": "SR_B3",
        "nir": "SR_B4",
        "swir1": "SR_B5",
        "swir2": "SR_B7",
        "qa": "QA_PIXEL"
    },
    "LANDSAT/LE07/C02/T1_L2": {
        "blue": "SR_B1",
        "green": "SR_B2",
        "red": "SR_B3",
        "nir": "SR_B4",
        "swir1": "SR_B5",
        "swir2": "SR_B7",
        "qa": "QA_PIXEL"
    },
    "LANDSAT/LC08/C02/T1_L2": {
        "blue": "SR_B2",
        "green": "SR_B3",
        "red": "SR_B4",
        "nir": "SR_B5",
        "swir1": "SR_B6",
        "swir2": "SR_B7",
        "qa": "QA_PIXEL"
    },
    "COPERNICUS/S2_SR_HARMONIZED": {
        "blue": "B2",
        "green": "B3",
        "red": "B4",
        "nir": "B8",
        "swir1": "B11",
        "swir2": "B12",
        "qa": "QA60"
    },
}
```

### Umbrales de Cambio

```python
CHANGE_THRESHOLDS = {
    "strong_loss": -0.2,      # ΔNDVI < -0.2
    "moderate_loss": -0.1,    # -0.2 ≤ ΔNDVI < -0.1
    "moderate_gain": 0.1,     # 0.1 < ΔNDVI ≤ 0.2
    "strong_gain": 0.2,       # ΔNDVI > 0.2
}
```

### Dataclass de Configuración

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class VegChangeConfig:
    """Configuración de análisis de cambio de vegetación."""

    # Identificación
    site_name: str = "Default Site"
    description: str = ""

    # Períodos a analizar
    periods: List[str] = field(default_factory=lambda: ["1990s", "present"])

    # Índices a calcular
    indices: List[str] = field(default_factory=lambda: ["ndvi", "nbr"])

    # Período de referencia para comparación
    reference_period: str = "1990s"

    # Parámetros de procesamiento
    scale: int = 30
    crs: str = "EPSG:4326"
    cloud_threshold: float = 20.0  # Máximo % de nubes

    # Caché
    use_cache: bool = True
    cache_to_asset: bool = False
    asset_folder: Optional[str] = None

    # Exportación
    export_composites: bool = False
    export_changes: bool = False
    export_folder: str = "VegChange_Exports"

    def validate(self):
        """Valida la configuración."""
        for period in self.periods:
            if period not in TEMPORAL_PERIODS:
                raise ValueError(f"Unknown period: {period}")

        if self.reference_period not in self.periods:
            raise ValueError(
                f"Reference period '{self.reference_period}' "
                f"must be in periods list"
            )
```

---

## veg_change_engine/pipeline.py

### Propósito
Orquesta el flujo completo de análisis, coordinando todos los módulos.

### Función Principal

```python
def analyze_vegetation_change(
    aoi: Union[ee.Geometry, gpd.GeoDataFrame, str],
    periods: List[str] = None,
    indices: List[str] = None,
    reference_period: str = None,
    config: Optional[VegChangeConfig] = None,
) -> Dict:
    """
    Ejecuta análisis completo de cambio de vegetación.

    Args:
        aoi: Área de interés (Geometry, GeoDataFrame, o path a archivo)
        periods: Lista de períodos a analizar
        indices: Lista de índices a calcular
        reference_period: Período de referencia para comparación
        config: Configuración opcional

    Returns:
        Diccionario con resultados:
        {
            'config': VegChangeConfig,
            'aoi': ee.Geometry,
            'composites': Dict[str, ee.Image],
            'indices': Dict[str, Dict[str, ee.Image]],
            'changes': Dict[str, Dict],
            'statistics': Dict,
        }
    """
```

### Flujo de Ejecución

```python
def analyze_vegetation_change(...) -> Dict:
    # 1. Configuración
    config = config or VegChangeConfig(
        periods=periods or ["1990s", "present"],
        indices=indices or ["ndvi"],
    )
    config.validate()

    # 2. Convertir AOI
    if isinstance(aoi, str):
        gdf = load_aoi(aoi)
        aoi = aoi_to_ee_geometry(gdf)
    elif isinstance(aoi, gpd.GeoDataFrame):
        aoi = aoi_to_ee_geometry(aoi)

    # 3. Generar composites
    composites = {}
    for period in config.periods:
        composites[period] = create_composite(aoi, period, config)

    # 4. Calcular índices
    indices_by_period = {}
    for period, composite in composites.items():
        indices_by_period[period] = {}
        for index_name in config.indices:
            index = get_index(index_name)
            indices_by_period[period][index_name] = index.calculate(composite)

    # 5. Detectar cambios
    changes = {}
    ref = config.reference_period
    for period in config.periods:
        if period != ref:
            key = f"{ref}_vs_{period}"
            changes[key] = {}

            for index_name in config.indices:
                before = indices_by_period[ref][index_name]
                after = indices_by_period[period][index_name]

                delta = calculate_change(before, after, index_name)
                classified = classify_change(delta)

                changes[key][index_name] = {
                    'delta': delta,
                    'classified': classified,
                }

    # 6. Calcular estadísticas
    statistics = {}
    for change_key, change_data in changes.items():
        statistics[change_key] = {}
        for index_name, data in change_data.items():
            statistics[change_key][index_name] = get_change_statistics(
                data['classified'], aoi, config.scale
            )

    # 7. Retornar resultados
    return {
        'config': config,
        'aoi': aoi,
        'composites': composites,
        'indices': indices_by_period,
        'changes': changes,
        'statistics': statistics,
    }
```

### Diagrama del Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE ANÁLISIS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ENTRADA                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │    AOI      │  │   Config    │  │  Períodos   │              │
│  │ (file/geom) │  │  (params)   │  │   [list]    │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┴────────────────┘                      │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    1. VALIDACIÓN                         │    │
│  │  - Convertir AOI a ee.Geometry                          │    │
│  │  - Validar períodos y configuración                     │    │
│  └────────────────────────────┬────────────────────────────┘    │
│                               │                                  │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 2. COMPOSITES TEMPORALES                 │    │
│  │  Para cada período:                                      │    │
│  │  - Cargar ImageCollection                               │    │
│  │  - Filtrar por AOI y fechas                             │    │
│  │  - Aplicar máscara de nubes                             │    │
│  │  - Calcular mediana                                      │    │
│  └────────────────────────────┬────────────────────────────┘    │
│                               │                                  │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  3. ÍNDICES ESPECTRALES                  │    │
│  │  Para cada composite:                                    │    │
│  │  - Calcular NDVI, NBR, etc.                             │    │
│  │  - Añadir como bandas                                    │    │
│  └────────────────────────────┬────────────────────────────┘    │
│                               │                                  │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                4. DETECCIÓN DE CAMBIOS                   │    │
│  │  Para cada par (referencia, comparación):               │    │
│  │  - Calcular delta (after - before)                      │    │
│  │  - Clasificar por umbrales                              │    │
│  └────────────────────────────┬────────────────────────────┘    │
│                               │                                  │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    5. ESTADÍSTICAS                       │    │
│  │  - Contar píxeles por clase                             │    │
│  │  - Calcular áreas en hectáreas                          │    │
│  │  - Generar porcentajes                                  │    │
│  └────────────────────────────┬────────────────────────────┘    │
│                               │                                  │
│                               ▼                                  │
│  SALIDA                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  {                                                       │    │
│  │    'composites': {period: ee.Image, ...},               │    │
│  │    'indices': {period: {index: ee.Image, ...}, ...},    │    │
│  │    'changes': {pair: {index: {delta, classified}}, ...},│    │
│  │    'statistics': {pair: {index: stats}, ...}            │    │
│  │  }                                                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## veg_change_engine/ee_init.py

### Propósito
Maneja la inicialización y autenticación de Earth Engine.

### Funciones

```python
def initialize_ee(project: str = None) -> bool:
    """
    Inicializa Earth Engine con manejo robusto.

    Args:
        project: ID del proyecto de Google Cloud

    Returns:
        True si la inicialización fue exitosa
    """
    import ee

    project = project or DEFAULT_PROJECT

    try:
        ee.Initialize(project=project)
        return True
    except ee.EEException:
        # Intentar sin proyecto
        try:
            ee.Initialize()
            return True
        except ee.EEException:
            return False


def get_ee_status() -> Dict:
    """
    Obtiene estado de la conexión a Earth Engine.

    Returns:
        {
            'initialized': bool,
            'project': str or None,
            'user': str or None
        }
    """
    import ee

    try:
        # Verificar conexión
        ee.Number(1).getInfo()

        # Obtener info del proyecto
        credentials = ee.data.getAssetRoots()

        return {
            'initialized': True,
            'project': credentials[0]['id'] if credentials else None,
        }
    except Exception:
        return {
            'initialized': False,
            'project': None,
        }


def authenticate_ee() -> bool:
    """
    Ejecuta flujo de autenticación.

    Returns:
        True si la autenticación fue exitosa
    """
    import ee

    try:
        ee.Authenticate()
        return True
    except Exception:
        return False
```
