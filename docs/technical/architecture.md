# Architecture Overview

This document describes the architecture of the Vegetation Change Intelligence Platform, including its modular design, component interactions, and design patterns.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Streamlit     │   CLI           │   External Apps             │
│   Dashboard     │   (Typer)       │   (via REST API)            │
└────────┬────────┴────────┬────────┴────────────┬────────────────┘
         │                 │                      │
         ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                                │
│                    (FastAPI REST API)                            │
│  ┌───────────┐  ┌────────────┐  ┌──────────┐  ┌────────────┐   │
│  │ /analysis │  │ /periods   │  │ /indices │  │ /health    │   │
│  └───────────┘  └────────────┘  └──────────┘  └────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SERVICES LAYER                             │
│                   (Business Logic Orchestration)                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               ChangeOrchestrator                          │   │
│  │  • analyze_vegetation_change()                            │   │
│  │  • run_full_analysis()                                    │   │
│  │  • Job management (create, get, run, cancel)              │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ENGINE LAYER                              │
│                    (Core GEE Processing)                         │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│ composites/ │  indices/   │  change/    │    io/      │alphaearth│
├─────────────┼─────────────┼─────────────┼─────────────┼─────────┤
│cloud_masking│   base.py   │ thresholds  │   aoi/      │embeddings│
│band_harmoni-│ vegetation  │ detection   │ exporters   │similarity│
│   zation    │   burn      │ statistics  │   cache     │ features │
│  temporal   │   water     │             │             │          │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE EARTH ENGINE                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                 │
│  │  Landsat   │  │ Sentinel-2 │  │ AlphaEarth │                 │
│  │ 5/7/8 C2   │  │    SR      │  │ Embeddings │                 │
│  └────────────┘  └────────────┘  └────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
vegetation-change-intelligence-platform/
├── engine/                      # Core GEE processing
│   ├── __init__.py             # Main exports
│   ├── config.py               # Configuration & constants
│   ├── ee_init.py              # EE authentication
│   ├── alphaearth.py           # Satellite embeddings
│   ├── composites/             # Composite generation
│   │   ├── cloud_masking.py    # Cloud/shadow removal
│   │   ├── band_harmonization.py # Sensor normalization
│   │   └── temporal.py         # Median composites
│   ├── indices/                # Spectral indices
│   │   ├── base.py             # ABC & registry
│   │   ├── vegetation.py       # NDVI, EVI
│   │   ├── burn.py             # NBR
│   │   ├── water.py            # NDWI, NDMI
│   │   └── convenience.py      # Helper functions
│   ├── change/                 # Change detection
│   │   ├── thresholds.py       # Classification thresholds
│   │   ├── detection.py        # Change algorithms
│   │   └── statistics.py       # Area calculations
│   └── io/                     # Input/Output
│       ├── aoi/                # AOI loading
│       │   ├── loaders.py      # Format-specific loaders
│       │   └── geometry.py     # Geometry operations
│       ├── exporters.py        # Drive/Asset export
│       └── cache.py            # Caching system
├── services/                   # Business logic
│   ├── __init__.py
│   └── change_orchestrator.py  # Main orchestrator
├── app/                        # Applications
│   ├── api/                    # FastAPI REST API
│   │   ├── main.py             # App entry point
│   │   ├── models/             # Pydantic models
│   │   │   ├── requests.py
│   │   │   └── responses.py
│   │   └── routes/             # API endpoints
│   │       ├── analysis.py
│   │       └── metadata.py
│   ├── Home.py                 # Streamlit dashboard
│   └── pages/                  # Dashboard pages
├── cli/                        # Command-line interface
│   └── main.py                 # Typer CLI
├── notebooks/                  # Jupyter tutorials
├── veg_change_engine/          # Backward compat layer
└── docs/                       # Documentation
```

## Design Patterns

### 1. Strategy Pattern (AOI Loaders)

```python
class AOILoader(ABC):
    @abstractmethod
    def load(self, filepath: str) -> gpd.GeoDataFrame:
        pass

    @abstractmethod
    def supports(self, filepath: str) -> bool:
        pass

class GeoJSONLoader(AOILoader):
    def supports(self, filepath: str) -> bool:
        return filepath.endswith('.geojson')

    def load(self, filepath: str) -> gpd.GeoDataFrame:
        return gpd.read_file(filepath)
```

### 2. Registry Pattern (Spectral Indices)

```python
INDEX_REGISTRY: Dict[str, SpectralIndex] = {}

def register_index(index: SpectralIndex) -> None:
    INDEX_REGISTRY[index.name] = index

# Auto-registration on import
register_index(NDVIIndex())
register_index(NBRIndex())
```

### 3. Factory Pattern (Change Thresholds)

```python
@dataclass
class ChangeThresholds:
    strong_loss: float
    moderate_loss: float
    # ...

    @classmethod
    def from_config(cls, index_name: str) -> "ChangeThresholds":
        config = CHANGE_THRESHOLDS.get(f"d{index_name}")
        return cls(**config)
```

### 4. Orchestrator Pattern (Services)

```python
class ChangeOrchestrator:
    def analyze(self, aoi, periods, indices, ...):
        # Step 1: Create composites
        composites = create_all_period_composites(aoi, periods)

        # Step 2: Add indices
        for period in composites:
            composites[period] = add_all_indices(composites[period], indices)

        # Step 3: Detect changes
        changes = create_change_analysis(composites, indices)

        # Step 4: Calculate statistics
        statistics = generate_change_statistics(changes, aoi)

        return {"composites": composites, "changes": changes, "statistics": statistics}
```

## Layer Responsibilities

### Engine Layer
- Pure GEE processing functions
- No business logic
- Stateless operations
- Unit testable

### Services Layer
- Business logic orchestration
- Job management
- Progress tracking
- Workflow coordination

### API Layer
- HTTP request/response handling
- Input validation (Pydantic)
- Authentication (future)
- Rate limiting (future)

### Client Layer
- User interfaces
- Data presentation
- Interactive features

## Data Flow

```
User Request
    │
    ▼
┌─────────────────┐
│  Load AOI       │  ← GeoJSON, KMZ, Shapefile
│  (io/aoi)       │
└────────┬────────┘
         │ ee.Geometry
         ▼
┌─────────────────┐
│ Create          │  ← Landsat, Sentinel-2
│ Composites      │  ← Cloud masking
│ (composites/)   │  ← Band harmonization
└────────┬────────┘
         │ ee.Image (per period)
         ▼
┌─────────────────┐
│ Calculate       │  ← NDVI, NBR, etc.
│ Indices         │
│ (indices/)      │
└────────┬────────┘
         │ ee.Image + indices
         ▼
┌─────────────────┐
│ Detect          │  ← Delta calculation
│ Changes         │  ← Classification
│ (change/)       │
└────────┬────────┘
         │ ee.Image (change maps)
         ▼
┌─────────────────┐
│ Generate        │  ← Area by class
│ Statistics      │  ← Pixel counts
│ (change/)       │
└────────┬────────┘
         │ Dict
         ▼
┌─────────────────┐
│ Export          │  → Google Drive
│ (io/exporters)  │  → EE Assets
└─────────────────┘
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Satellite Processing | Google Earth Engine | Cloud-based geospatial |
| Backend Framework | FastAPI | REST API |
| Dashboard | Streamlit | Web UI |
| CLI | Typer + Rich | Command-line |
| Validation | Pydantic | Data models |
| Geospatial | GeoPandas, Shapely | Vector operations |
| Visualization | Folium, Matplotlib | Maps and charts |
| Testing | Pytest | Unit/integration tests |

## Scalability Considerations

### Horizontal Scaling
- Stateless API design
- Job queue for heavy processing
- Multiple API workers

### Earth Engine Limits
- Concurrent computations: 100
- Export tasks: 3000/day
- Geometry complexity limits

### Caching Strategy
- Asset cache: Persistent composites
- Local cache: Tile URLs, metadata
- TTL: 24 hours for tile URLs

## Security

### Authentication
- Earth Engine: Service account or user credentials
- API: Token-based (future)

### Data Access
- AOI files: Local filesystem only
- Results: Google Drive or EE Assets

## Next Steps

- [API Reference](api-reference.md)
- [Engine Modules](engine-modules.md)
- [Data Flow Details](data-flow.md)
