# 01. Visión General del Sistema

## Vegetation Change Intelligence Platform

### Descripción

Plataforma de análisis de cambio de vegetación basada en Google Earth Engine que procesa imágenes satelitales multi-temporales para detectar y cuantificar cambios en la cobertura vegetal.

### Propósito

- Detectar pérdida de vegetación (deforestación, incendios, urbanización)
- Identificar recuperación vegetal (reforestación, regeneración natural)
- Generar mapas de cambio clasificados
- Exportar resultados para análisis GIS

### Capacidades Principales

```
┌─────────────────────────────────────────────────────────────────┐
│                    VEGETATION CHANGE PLATFORM                    │
├─────────────────────────────────────────────────────────────────┤
│  📅 Rango Temporal    │  1985 - 2024 (40 años de análisis)      │
│  🛰️ Sensores          │  Landsat 5/7/8 + Sentinel-2             │
│  📊 Índices           │  NDVI, NBR, NDWI, EVI, NDMI             │
│  🎯 Resolución        │  30m (Landsat) / 10m (Sentinel-2)       │
│  💾 Persistencia      │  EE Assets + Cache Local                │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de Trabajo Principal

```
                    ┌──────────────────┐
                    │   Usuario        │
                    │   (CLI/Web)      │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   Área de        │
                    │   Interés (AOI)  │
                    │   KMZ/GeoJSON    │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────┐  ┌──────▼──────┐  ┌───▼────────┐
     │   Período   │  │   Período   │  │   Período  │
     │   1990s     │  │   2010s     │  │   Presente │
     │  Landsat 5  │  │  Landsat 8  │  │  L8 + S2   │
     └────────┬────┘  └──────┬──────┘  └───┬────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼─────────┐
                    │   Composites     │
                    │   Temporales     │
                    │   (Mediana)      │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   Índices        │
                    │   Espectrales    │
                    │   NDVI, NBR...   │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   Detección      │
                    │   de Cambios     │
                    │   (Delta)        │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   Clasificación  │
                    │   5 Categorías   │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌─────▼─────┐       ┌────▼────┐
    │  Mapas  │        │  Reportes │       │ Export  │
    │  Folium │        │   Stats   │       │ GeoTIFF │
    └─────────┘        └───────────┘       └─────────┘
```

### Períodos Temporales Disponibles

| Período | Rango de Fechas | Sensores | Descripción |
|---------|-----------------|----------|-------------|
| **1990s** | 1985-01-01 → 1999-12-31 | Landsat 5 TM | Era pre-digital, línea base histórica |
| **2000s** | 2000-01-01 → 2009-12-31 | Landsat 7 ETM+ | Incluye stripe issues post-2003 |
| **2010s** | 2010-01-01 → 2019-12-31 | Landsat 8 OLI | Alta calidad radiométrica |
| **present** | 2020-01-01 → Presente | L8 + Sentinel-2 | Fusión multi-sensor |

### Clasificación de Cambios

```
┌────────────────────────────────────────────────────────────────┐
│  CLASE           │  UMBRAL        │  COLOR    │  SIGNIFICADO   │
├────────────────────────────────────────────────────────────────┤
│  Pérdida Fuerte  │  ΔNDVI < -0.2  │  🔴 Rojo  │  Deforestación │
│  Pérdida Moderada│  -0.2 ≤ Δ<-0.1│  🟠 Naranja│  Degradación   │
│  Estable         │  -0.1 ≤ Δ ≤0.1│  🟡 Amarillo│ Sin cambio    │
│  Ganancia Moderada│ 0.1 < Δ ≤ 0.2 │  🟢 Verde │  Recuperación  │
│  Ganancia Fuerte │  ΔNDVI > 0.2   │  🌲 Verde │  Reforestación │
└────────────────────────────────────────────────────────────────┘
```

### Arquitectura de Alto Nivel

```
vegetation-change-intelligence-platform/
│
├── veg_change_engine/          # 🔧 Motor de Análisis
│   ├── core/                   #    Algoritmos principales
│   ├── io/                     #    Entrada/Salida
│   └── viz/                    #    Visualización
│
├── cli/                        # 💻 Interfaz de Comandos
│   └── main.py                 #    CLI con Typer
│
├── app/                        # 🌐 Dashboard Web
│   ├── Home.py                 #    Página principal
│   └── pages/                  #    Sub-páginas
│
└── docs/                       # 📚 Documentación
    └── architecture/           #    Esta carpeta
```

### Principios de Diseño

1. **Modularidad**: Cada componente tiene responsabilidad única
2. **Extensibilidad**: Nuevos índices/formatos via registros
3. **Persistencia**: Caché para evitar consumo repetido de API
4. **Usabilidad**: CLI + Web para diferentes usuarios
5. **Documentación**: Bilingüe (ES/EN) para alcance internacional
