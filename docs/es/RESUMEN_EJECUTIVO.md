# Resumen Ejecutivo

## Plataforma de Inteligencia de Cambio de Vegetación

### Qué Hace Este Sistema

La Plataforma de Inteligencia de Cambio de Vegetación es un sistema automatizado de análisis de imágenes satelitales que detecta y cuantifica cambios en la vegetación durante períodos multi-decadales. Construido sobre Google Earth Engine, procesa imágenes Landsat y Sentinel-2 para producir mapas de detección de cambios y estadísticas accionables.

### El Problema

Monitorear cambios de vegetación en grandes paisajes es desafiante:
- **Análisis Manual**: Los métodos tradicionales requieren experiencia extensiva en SIG
- **Volumen de Datos**: Décadas de imágenes satelitales son difíciles de procesar
- **Contaminación por Nubes**: Las regiones tropicales tienen cobertura persistente de nubes
- **Complejidad Multi-Sensor**: Diferentes satélites tienen diferentes configuraciones de bandas
- **Reproducibilidad**: Los resultados varían entre analistas y métodos

### La Solución

Esta plataforma automatiza el flujo de trabajo completo de análisis:

```
Carga de AOI → Generación de Compuestos → Cálculo de Índices → Detección de Cambio → Exportación
```

**Entrada**: Área de Interés (KMZ, GeoJSON, Shapefile)

**Salida**:
- Compuestos temporales (imágenes libres de nubes para cada período)
- Índices espectrales (NDVI, NBR, etc.)
- Mapas de detección de cambio (pérdida/ganancia clasificada)
- Estadísticas y resúmenes

### Capacidades Clave

| Capacidad | Descripción |
|-----------|-------------|
| **Fusión Multi-Sensor** | Landsat 5/7/8 + Sentinel-2 para cobertura continua |
| **Enmascaramiento Automático de Nubes** | Remoción basada en QA de nubes y sombras |
| **Flexibilidad Temporal** | Analiza cualquier período desde 1985 hasta el presente |
| **Persistencia de Datos** | Sistema de caché evita consumo repetido de API |
| **Múltiples Salidas** | GeoTIFF, EE Assets, mapas interactivos |

### Clases de Detección de Cambio

| Clase | Etiqueta | Descripción | Color |
|-------|----------|-------------|-------|
| 1 | Pérdida Fuerte | Disminución significativa de vegetación | Rojo |
| 2 | Pérdida Moderada | Disminución moderada | Naranja |
| 3 | Estable | Sin cambio significativo | Amarillo |
| 4 | Ganancia Moderada | Aumento moderado de vegetación | Verde Claro |
| 5 | Ganancia Fuerte | Aumento significativo | Verde Oscuro |

### Casos de Uso

- **Monitoreo de Deforestación**: Seguimiento de pérdida de bosques en el tiempo
- **Evaluación de Reforestación**: Medir recuperación después de restauración
- **Cambio Agrícola**: Monitorear patrones de cultivos y expansión
- **Recuperación Post-Incendio**: Evaluar regeneración de vegetación tras incendios
- **Estudios de Impacto Climático**: Análisis de tendencias de vegetación a largo plazo

### Inicio Rápido

```bash
# Instalar
pip install -e .

# Autenticar con Earth Engine
earthengine authenticate

# Ejecutar demo
veg-change run-demo

# Analizar sus propios datos
veg-change analyze --aoi area.geojson --periods 1990s,present --export
```

### Visión General de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│           PLATAFORMA DE CAMBIO DE VEGETACIÓN                 │
├─────────────────────────────────────────────────────────────┤
│  ENTRADA         PROCESO              SALIDA                 │
│  ──────          ───────              ──────                 │
│  Archivo AOI →   Compuestos      →    Rásters GeoTIFF       │
│  Config      →   Índices         →    EE Assets             │
│              →   Detección       →    Mapas Interactivos    │
│              →   Estadísticas    →    Reportes              │
└─────────────────────────────────────────────────────────────┘
```

### Fundamento Técnico

- **Google Earth Engine**: Procesamiento geoespacial en la nube
- **Landsat Colección 2**: Imágenes de reflectancia superficial (1985-presente)
- **Sentinel-2 SR Armonizado**: Imágenes de 10m de resolución (2017-presente)
- **Ecosistema Python**: geopandas, folium, streamlit

### Quién Debe Usar Esto

- **Científicos Ambientales**: Investigación de monitoreo de vegetación
- **Organizaciones de Conservación**: Monitoreo de áreas protegidas
- **Agencias Gubernamentales**: Seguimiento de cambio de uso del suelo
- **Consultores Agrícolas**: Monitoreo y evaluación de cultivos
- **Investigadores Climáticos**: Estudios de ecosistemas a largo plazo

---

*Construido para análisis escalable y reproducible de cambio de vegetación*
