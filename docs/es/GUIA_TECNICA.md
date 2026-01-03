# Guía Técnica

## Referencia de API, Configuración y Guía de Extensión

---

## 1. Estructura del Paquete

```
veg_change_engine/
├── __init__.py          # Exportaciones de API pública
├── config.py            # Sistema de configuración
├── pipeline.py          # Orquestador principal
├── core/                # Algoritmos de análisis
│   ├── composites.py    # Generación de compuestos temporales
│   ├── indices.py       # Cálculo de índices espectrales
│   └── change.py        # Detección de cambios
├── io/                  # Entrada/Salida
│   ├── aoi.py           # Carga de AOI
│   ├── exporters.py     # Exportación a Drive/Assets
│   └── cache.py         # Persistencia de datos
└── viz/                 # Visualización
    ├── maps.py          # Generación de mapas Folium
    └── colors.py        # Paletas de colores
```

---

## 2. Referencia de API

### 2.1 Funciones de Alto Nivel

```python
from veg_change_engine import analyze_vegetation_change, run_full_analysis

# Analizar con ee.Geometry
results = analyze_vegetation_change(
    aoi=aoi,                    # ee.Geometry
    periods=["1990s", "present"],
    indices=["ndvi", "nbr"],
    reference_period="1990s",
)

# Ejecutar desde archivo
results = run_full_analysis(
    aoi_path="area.geojson",
    site_name="Mi Sitio de Análisis",
    periods=["1990s", "2010s", "present"],
    export=True,
)
```

### 2.2 Funciones Core

```python
from veg_change_engine.core import (
    create_all_period_composites,
    add_all_indices,
    create_change_analysis,
)

# Crear compuestos
compuestos = create_all_period_composites(aoi, periods, cloud_threshold=20.0)

# Agregar índices
imagen = add_all_indices(imagen, indices=["ndvi", "nbr"])

# Análisis de cambio
cambios = create_change_analysis(compuestos, indices, reference_period="1990s")
```

---

## 3. Configuración

### 3.1 Clase VegChangeConfig

```python
from veg_change_engine import VegChangeConfig

config = VegChangeConfig(
    site_name="Mi Análisis",
    periods=["1990s", "2010s", "present"],
    indices=["ndvi", "nbr"],
    buffer_distance=500.0,      # metros
    cloud_threshold=20.0,       # porcentaje
    export_scale=30,            # metros
    drive_folder="VegChangeAnalysis",
)
```

### 3.2 Configuración YAML

```yaml
# config.yaml
site_name: "Mi Análisis"
periods:
  - "1990s"
  - "present"
indices:
  - "ndvi"
buffer_distance: 500.0
cloud_threshold: 20.0
drive_folder: "VegChangeAnalysis"
```

---

## 4. Períodos Temporales

| Período | Años | Sensores | Descripción |
|---------|------|----------|-------------|
| 1990s | 1985-1999 | Landsat 5 TM | Línea base histórica |
| 2000s | 2000-2012 | Landsat 5/7 | Inicio del milenio |
| 2010s | 2013-2020 | Landsat 8 OLI | Década reciente |
| present | 2021-2024 | Landsat 8 + Sentinel-2 | Condiciones actuales |

---

## 5. Sistema de Caché

### 5.1 Por Qué Cachear?

Las llamadas a la API de Earth Engine pueden ser lentas y tienen cuotas. El caché:
- Guarda compuestos calculados como EE Assets (persistentes)
- Cachea URLs de tiles localmente (TTL de 24 horas)
- Acelera dramáticamente análisis repetidos

### 5.2 Usando el Caché

```python
from veg_change_engine.io import setup_cache

# Inicializar caché
cache = setup_cache("users/mi_usuario/veg_change_cache")

# Obtener compuesto (carga desde caché si está disponible)
compuesto = cache.get_composite(
    aoi=aoi,
    period="2010s",
    indices=["ndvi", "nbr"],
)

# Segunda llamada carga desde caché - mucho más rápido!
compuesto2 = cache.get_composite(aoi, "2010s", ["ndvi", "nbr"])

# Obtener mapa de cambio con caché
cambio = cache.get_change_map(
    aoi=aoi,
    before_period="1990s",
    after_period="present",
    index="ndvi",
)

# Listar assets cacheados
cacheados = cache.list_cached_assets()

# Limpiar caché
cache.clear_cache(assets=True, local=True)
```

---

## 6. Índices Espectrales

| Índice | Fórmula | Descripción |
|--------|---------|-------------|
| NDVI | (NIR - Rojo) / (NIR + Rojo) | Salud de la vegetación |
| NBR | (NIR - SWIR2) / (NIR + SWIR2) | Severidad de quema |
| NDWI | (Verde - NIR) / (Verde + NIR) | Contenido de agua |
| EVI | 2.5 * (NIR - Rojo) / (NIR + 6*Rojo - 7.5*Azul + 1) | Vegetación mejorada |
| NDMI | (NIR - SWIR1) / (NIR + SWIR1) | Contenido de humedad |

---

## 7. Umbrales de Detección de Cambio

```python
UMBRALES_CAMBIO = {
    "dndvi": {
        "perdida_fuerte": -0.15,
        "perdida_moderada": -0.05,
        "estable_min": -0.05,
        "estable_max": 0.05,
        "ganancia_moderada": 0.05,
        "ganancia_fuerte": 0.15,
    },
}
```

---

## 8. Referencia CLI

```bash
# Análisis completo
veg-change analyze \
    --aoi area.geojson \
    --name "Mi Sitio" \
    --periods 1990s,2000s,2010s,present \
    --indices ndvi,nbr \
    --export

# Vista previa rápida
veg-change preview --aoi area.geojson --period present --index ndvi

# Mostrar períodos
veg-change periods

# Mostrar índices
veg-change indices

# Ejecutar demo
veg-change run-demo

# Autenticar
veg-change auth
```

---

## 9. Manejo de Errores

| Error | Causa | Solución |
|-------|-------|----------|
| `ee.EEException` | Error de API EE | Verificar autenticación, cuotas |
| `FileNotFoundError` | Archivo AOI no existe | Verificar ruta del archivo |
| `ValueError: No images` | Colección vacía | Reducir umbral de nubes, verificar fechas |

---

## 10. Consejos de Rendimiento

1. **Usar Caché**: Configurar caché de assets para análisis repetidos
2. **Limitar Tamaño de AOI**: Áreas grandes toman más tiempo
3. **Aumentar Umbral de Nubes**: Si los compuestos están vacíos
4. **Reducir Períodos**: Comenzar con menos períodos temporales
5. **Usar Escala Apropiada**: 30m para Landsat, 10m para Sentinel-2
