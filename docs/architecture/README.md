# Arquitectura del Sistema

## Vegetation Change Intelligence Platform

Esta documentación describe la arquitectura completa de la plataforma de análisis de cambio de vegetación basada en Google Earth Engine.

## Índice de Documentación

| Documento | Descripción |
|-----------|-------------|
| [01_OVERVIEW.md](01_OVERVIEW.md) | Visión general del sistema |
| [02_CORE_MODULES.md](02_CORE_MODULES.md) | Módulos core (composites, indices, change) |
| [03_IO_MODULES.md](03_IO_MODULES.md) | Módulos de entrada/salida |
| [04_VIZ_MODULES.md](04_VIZ_MODULES.md) | Módulos de visualización |
| [05_CONFIG_PIPELINE.md](05_CONFIG_PIPELINE.md) | Configuración y orquestación |
| [06_CLI_APP.md](06_CLI_APP.md) | CLI y Dashboard Streamlit |
| [07_DATA_FLOW.md](07_DATA_FLOW.md) | Flujo de datos y diagramas |
| [08_API_REFERENCE.md](08_API_REFERENCE.md) | Referencia de API |

## Estructura del Proyecto

```
vegetation-change-intelligence-platform/
│
├── veg_change_engine/          # Motor principal de análisis
│   ├── __init__.py             # Exportaciones públicas
│   ├── config.py               # Configuración global
│   ├── pipeline.py             # Orquestador principal
│   ├── ee_init.py              # Inicialización Earth Engine
│   │
│   ├── core/                   # Algoritmos de análisis
│   │   ├── __init__.py
│   │   ├── composites.py       # Compuestos temporales
│   │   ├── indices.py          # Índices espectrales
│   │   └── change.py           # Detección de cambios
│   │
│   ├── io/                     # Entrada/Salida
│   │   ├── __init__.py
│   │   ├── aoi.py              # Carga de AOI
│   │   ├── exporters.py        # Exportación
│   │   └── cache.py            # Sistema de caché
│   │
│   └── viz/                    # Visualización
│       ├── __init__.py
│       ├── colors.py           # Paletas de colores
│       └── maps.py             # Mapas interactivos
│
├── cli/                        # Interfaz de comandos
│   ├── __init__.py
│   └── main.py                 # CLI con Typer
│
├── app/                        # Dashboard Streamlit
│   ├── Home.py                 # Página principal
│   └── pages/
│       ├── 1_Analysis.py       # Página de análisis
│       └── 2_Map.py            # Página de mapa
│
├── docs/                       # Documentación
│   ├── architecture/           # Esta carpeta
│   ├── en/                     # Docs en inglés
│   └── es/                     # Docs en español
│
├── pyproject.toml              # Configuración del paquete
├── Makefile                    # Comandos de desarrollo
└── README.md                   # Documentación principal
```

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Backend de Procesamiento | Google Earth Engine |
| Lenguaje | Python 3.9+ |
| Geoespacial | GeoPandas, Shapely, Rasterio |
| Visualización | Folium, Matplotlib |
| Dashboard | Streamlit |
| CLI | Typer + Rich |
| Configuración | PyYAML, Dataclasses |

## Principios de Diseño

1. **SOLID**: Código modular y extensible
2. **Strategy Pattern**: Índices y loaders intercambiables
3. **Registry Pattern**: Registro de componentes disponibles
4. **Dependency Injection**: Configuración inyectable
5. **Caching**: Evitar consumo repetido de API
