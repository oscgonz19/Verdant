# 02. Módulos Core

## veg_change_engine/core/

Los módulos core contienen los algoritmos principales de procesamiento de imágenes satelitales.

---

## composites.py - Compuestos Temporales

### Propósito
Genera compuestos temporales (imágenes agregadas) a partir de colecciones de imágenes satelitales, aplicando máscaras de nubes y reducción temporal.

### Funciones Principales

#### `create_composite()`
```python
def create_composite(
    aoi: ee.Geometry,
    period: str,
    config: Optional[VegChangeConfig] = None,
) -> ee.Image:
```

**Flujo de procesamiento:**
```
ImageCollection → Filtro espacial → Filtro temporal → Máscara nubes → Mediana
```

#### `mask_clouds_landsat()`
```python
def mask_clouds_landsat(image: ee.Image) -> ee.Image:
```
Aplica máscara de nubes usando la banda QA_PIXEL de Landsat Collection 2.

**Bits de QA_PIXEL:**
- Bit 3: Cloud Shadow
- Bit 4: Cloud
- Bit 5: Snow (opcional)

```python
# Ejemplo de máscara
qa = image.select('QA_PIXEL')
cloud_mask = qa.bitwiseAnd(1 << 3).eq(0)  # No shadow
cloud_mask = cloud_mask.And(qa.bitwiseAnd(1 << 4).eq(0))  # No cloud
```

#### `mask_clouds_sentinel2()`
```python
def mask_clouds_sentinel2(image: ee.Image) -> ee.Image:
```
Usa banda QA60 de Sentinel-2 para enmascarar nubes y cirrus.

**Bits de QA60:**
- Bit 10: Opaque clouds
- Bit 11: Cirrus clouds

#### `harmonize_bands()`
```python
def harmonize_bands(image: ee.Image, sensor: str) -> ee.Image:
```
Renombra bandas de diferentes sensores a nombres consistentes.

**Mapeo de bandas:**
```
Landsat 5/7:  B1→blue, B2→green, B3→red, B4→nir, B5→swir1, B7→swir2
Landsat 8:    B2→blue, B3→green, B4→red, B5→nir, B6→swir1, B7→swir2
Sentinel-2:   B2→blue, B3→green, B4→red, B8→nir, B11→swir1, B12→swir2
```

### Diagrama de Flujo

```
┌─────────────────┐
│ get_collection()│
│ (por período)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Landsat 5 TM    │────▶│ mask_clouds_    │
│ 1985-1999       │     │ landsat()       │
└─────────────────┘     └────────┬────────┘
                                 │
┌─────────────────┐     ┌────────▼────────┐
│ Landsat 7 ETM+  │────▶│ harmonize_      │
│ 2000-2009       │     │ bands()         │
└─────────────────┘     └────────┬────────┘
                                 │
┌─────────────────┐     ┌────────▼────────┐
│ Landsat 8 OLI   │────▶│ merge()         │
│ 2013-present    │     │ collections     │
└─────────────────┘     └────────┬────────┘
                                 │
┌─────────────────┐     ┌────────▼────────┐
│ Sentinel-2 MSI  │────▶│ median()        │
│ 2017-present    │     │ composite       │
└─────────────────┘     └─────────────────┘
```

---

## indices.py - Índices Espectrales

### Propósito
Calcula índices espectrales de vegetación usando el patrón Strategy para extensibilidad.

### Patrón Strategy

```python
class SpectralIndex(ABC):
    """Clase abstracta para índices espectrales."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def calculate(self, image: ee.Image) -> ee.Image:
        pass
```

### Índices Implementados

#### NDVI - Normalized Difference Vegetation Index
```python
class NDVIIndex(SpectralIndex):
    @property
    def name(self) -> str:
        return "ndvi"

    def calculate(self, image: ee.Image) -> ee.Image:
        return image.normalizedDifference(['nir', 'red']).rename('ndvi')
```

**Fórmula:** `NDVI = (NIR - RED) / (NIR + RED)`

**Interpretación:**
- -1 a 0: Agua, suelo desnudo, nubes
- 0 a 0.3: Vegetación escasa
- 0.3 a 0.6: Vegetación moderada
- 0.6 a 1: Vegetación densa

#### NBR - Normalized Burn Ratio
```python
class NBRIndex(SpectralIndex):
    def calculate(self, image: ee.Image) -> ee.Image:
        return image.normalizedDifference(['nir', 'swir2']).rename('nbr')
```

**Fórmula:** `NBR = (NIR - SWIR2) / (NIR + SWIR2)`

**Uso:** Detección de áreas quemadas y severidad de incendios.

#### NDWI - Normalized Difference Water Index
```python
class NDWIIndex(SpectralIndex):
    def calculate(self, image: ee.Image) -> ee.Image:
        return image.normalizedDifference(['green', 'nir']).rename('ndwi')
```

**Fórmula:** `NDWI = (GREEN - NIR) / (GREEN + NIR)`

**Uso:** Detección de cuerpos de agua y contenido hídrico.

#### EVI - Enhanced Vegetation Index
```python
class EVIIndex(SpectralIndex):
    def calculate(self, image: ee.Image) -> ee.Image:
        return image.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
            {
                'NIR': image.select('nir'),
                'RED': image.select('red'),
                'BLUE': image.select('blue')
            }
        ).rename('evi')
```

**Uso:** Mejor rendimiento en áreas de alta biomasa.

#### NDMI - Normalized Difference Moisture Index
```python
class NDMIIndex(SpectralIndex):
    def calculate(self, image: ee.Image) -> ee.Image:
        return image.normalizedDifference(['nir', 'swir1']).rename('ndmi')
```

**Fórmula:** `NDMI = (NIR - SWIR1) / (NIR + SWIR1)`

**Uso:** Estrés hídrico de la vegetación.

### Registro de Índices

```python
INDEX_REGISTRY: Dict[str, SpectralIndex] = {
    'ndvi': NDVIIndex(),
    'nbr': NBRIndex(),
    'ndwi': NDWIIndex(),
    'evi': EVIIndex(),
    'ndmi': NDMIIndex(),
}

def get_index(name: str) -> SpectralIndex:
    """Obtiene índice del registro."""
    if name not in INDEX_REGISTRY:
        raise ValueError(f"Unknown index: {name}")
    return INDEX_REGISTRY[name]

def calculate_indices(image: ee.Image, indices: List[str]) -> ee.Image:
    """Calcula múltiples índices y los añade a la imagen."""
    for name in indices:
        index = get_index(name)
        image = image.addBands(index.calculate(image))
    return image
```

---

## change.py - Detección de Cambios

### Propósito
Calcula diferencias temporales y clasifica cambios en vegetación.

### Funciones Principales

#### `calculate_change()`
```python
def calculate_change(
    before: ee.Image,
    after: ee.Image,
    index: str = "ndvi",
) -> ee.Image:
```

Calcula la diferencia simple:
```python
delta = after.select(index).subtract(before.select(index))
return delta.rename(f'd{index}')
```

#### `classify_change()`
```python
def classify_change(
    change_image: ee.Image,
    thresholds: Optional[Dict] = None,
) -> ee.Image:
```

Aplica clasificación por umbrales:
```python
THRESHOLDS = {
    'strong_loss': -0.2,
    'moderate_loss': -0.1,
    'moderate_gain': 0.1,
    'strong_gain': 0.2,
}
```

**Lógica de clasificación:**
```python
classified = (
    change_image
    .where(change_image.lt(thresholds['strong_loss']), 1)      # Pérdida fuerte
    .where(change_image.gte(thresholds['strong_loss'])
           .And(change_image.lt(thresholds['moderate_loss'])), 2)  # Pérdida moderada
    .where(change_image.gte(thresholds['moderate_loss'])
           .And(change_image.lte(thresholds['moderate_gain'])), 3) # Estable
    .where(change_image.gt(thresholds['moderate_gain'])
           .And(change_image.lte(thresholds['strong_gain'])), 4)   # Ganancia moderada
    .where(change_image.gt(thresholds['strong_gain']), 5)      # Ganancia fuerte
)
```

#### `get_change_statistics()`
```python
def get_change_statistics(
    classified: ee.Image,
    aoi: ee.Geometry,
    scale: int = 30,
) -> Dict:
```

Calcula estadísticas por clase:
```python
stats = classified.reduceRegion(
    reducer=ee.Reducer.frequencyHistogram(),
    geometry=aoi,
    scale=scale,
    maxPixels=1e9
)
```

**Retorna:**
```python
{
    'total_pixels': 150000,
    'class_counts': {1: 5000, 2: 10000, 3: 120000, 4: 10000, 5: 5000},
    'class_percentages': {1: 3.3, 2: 6.7, 3: 80.0, 4: 6.7, 5: 3.3},
    'area_ha': {1: 450, 2: 900, 3: 10800, 4: 900, 5: 450}
}
```

### Diagrama de Detección de Cambios

```
┌─────────────┐         ┌─────────────┐
│  Composite  │         │  Composite  │
│   Before    │         │    After    │
│  (1990s)    │         │  (present)  │
└──────┬──────┘         └──────┬──────┘
       │                       │
       │    ┌─────────────┐    │
       └───▶│  calculate_ │◀───┘
            │  change()   │
            └──────┬──────┘
                   │
                   ▼
            ┌─────────────┐
            │  Delta      │
            │  dNDVI      │
            │  [-1, +1]   │
            └──────┬──────┘
                   │
                   ▼
            ┌─────────────┐
            │  classify_  │
            │  change()   │
            └──────┬──────┘
                   │
                   ▼
            ┌─────────────┐
            │  Classified │
            │  [1-5]      │
            └──────┬──────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   ┌───────┐  ┌─────────┐  ┌───────┐
   │ Stats │  │   Map   │  │Export │
   │ (ha)  │  │ (Folium)│  │(TIFF) │
   └───────┘  └─────────┘  └───────┘
```
