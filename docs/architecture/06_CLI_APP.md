# 06. CLI y Dashboard Streamlit

## cli/main.py - Interfaz de Línea de Comandos

### Propósito
Proporciona acceso al motor de análisis desde la terminal usando Typer.

### Estructura del CLI

```python
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="vegchange",
    help="Vegetation Change Intelligence Platform CLI",
    add_completion=False,
)
console = Console()
```

### Comandos Disponibles

#### `vegchange analyze`
```bash
vegchange analyze path/to/aoi.kmz \
    --periods 1990s present \
    --indices ndvi nbr \
    --reference 1990s \
    --output results/
```

```python
@app.command()
def analyze(
    aoi: str = typer.Argument(..., help="Path to AOI file"),
    periods: List[str] = typer.Option(
        ["1990s", "present"],
        "--periods", "-p",
        help="Periods to analyze"
    ),
    indices: List[str] = typer.Option(
        ["ndvi"],
        "--indices", "-i",
        help="Spectral indices to calculate"
    ),
    reference: str = typer.Option(
        "1990s",
        "--reference", "-r",
        help="Reference period for comparison"
    ),
    output: str = typer.Option(
        "./output",
        "--output", "-o",
        help="Output directory"
    ),
    export: bool = typer.Option(
        False,
        "--export", "-e",
        help="Export results to Drive"
    ),
):
    """Run vegetation change analysis."""
    # ... implementation
```

#### `vegchange preview`
```bash
vegchange preview path/to/aoi.kmz --period 2010s
```

```python
@app.command()
def preview(
    aoi: str = typer.Argument(..., help="Path to AOI file"),
    period: str = typer.Option(
        "present",
        "--period", "-p",
        help="Period to preview"
    ),
    index: str = typer.Option(
        "ndvi",
        "--index", "-i",
        help="Index to display"
    ),
):
    """Preview a single period composite."""
```

#### `vegchange periods`
```bash
vegchange periods
```

```python
@app.command()
def periods():
    """List available temporal periods."""

    table = Table(title="Temporal Periods")
    table.add_column("Period", style="cyan")
    table.add_column("Date Range", style="green")
    table.add_column("Sensors", style="yellow")
    table.add_column("Description")

    for name, info in TEMPORAL_PERIODS.items():
        sensors = ", ".join([s.split("/")[1] for s in info["sensors"]])
        table.add_row(
            name.upper(),
            f"{info['start'][:4]} - {info['end'][:4]}",
            sensors,
            info["description"]
        )

    console.print(table)
```

#### `vegchange indices`
```bash
vegchange indices
```

```python
@app.command()
def indices():
    """List available spectral indices."""

    table = Table(title="Spectral Indices")
    table.add_column("Index", style="cyan")
    table.add_column("Full Name", style="green")
    table.add_column("Formula")
    table.add_column("Use Case")

    indices_info = [
        ("ndvi", "Normalized Difference Vegetation Index",
         "(NIR-RED)/(NIR+RED)", "Vegetation health"),
        ("nbr", "Normalized Burn Ratio",
         "(NIR-SWIR2)/(NIR+SWIR2)", "Burn severity"),
        ("ndwi", "Normalized Difference Water Index",
         "(GREEN-NIR)/(GREEN+NIR)", "Water content"),
        ("evi", "Enhanced Vegetation Index",
         "2.5*(NIR-RED)/(NIR+6*RED-7.5*BLUE+1)", "High biomass"),
        ("ndmi", "Normalized Difference Moisture Index",
         "(NIR-SWIR1)/(NIR+SWIR1)", "Vegetation moisture"),
    ]

    for idx in indices_info:
        table.add_row(*idx)

    console.print(table)
```

#### `vegchange run-demo`
```bash
vegchange run-demo
```

```python
@app.command()
def run_demo():
    """Run demo analysis on Colombian Andes region."""

    console.print("[bold green]Running demo analysis...[/]")

    aoi = ee.Geometry.Rectangle([-75.7, 4.4, -75.6, 4.5])

    results = analyze_vegetation_change(
        aoi=aoi,
        periods=["2010s", "present"],
        indices=["ndvi"],
        reference_period="2010s"
    )

    console.print("[bold green]Demo complete![/]")
    console.print(f"Composites: {list(results['composites'].keys())}")
    console.print(f"Changes: {list(results['changes'].keys())}")
```

#### `vegchange auth`
```bash
vegchange auth --project geoconcret-474619
```

```python
@app.command()
def auth(
    project: str = typer.Option(
        None,
        "--project", "-p",
        help="Google Cloud project ID"
    ),
):
    """Authenticate with Earth Engine."""
```

### Ejemplo de Salida

```
╭─────────────────── Temporal Periods ───────────────────╮
│ Period   │ Date Range   │ Sensors      │ Description   │
├──────────┼──────────────┼──────────────┼───────────────┤
│ 1990S    │ 1985 - 1999  │ LT05         │ Era Landsat 5 │
│ 2000S    │ 2000 - 2009  │ LE07         │ Era Landsat 7 │
│ 2010S    │ 2010 - 2019  │ LC08         │ Era Landsat 8 │
│ PRESENT  │ 2020 - 2024  │ LC08, S2_SR  │ Multi-sensor  │
╰─────────────────────────────────────────────────────────╯
```

---

## app/ - Dashboard Streamlit

### Estructura de Archivos

```
app/
├── Home.py                 # Página principal
└── pages/
    ├── 1_Analysis.py       # Página de análisis
    └── 2_Map.py            # Página de mapa
```

### Home.py - Página Principal

#### Configuración Inicial
```python
import streamlit as st

st.set_page_config(
    page_title="Vegetation Change Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)
```

#### Fix PROJ_LIB
```python
# Necesario ANTES de importar geopandas
import os
os.environ['PROJ_LIB'] = '/path/to/conda/env/share/proj'
os.environ['PROJ_DATA'] = '/path/to/conda/env/share/proj'
```

#### Autenticación de Earth Engine
```python
DEFAULT_PROJECT = "geoconcret-474619"

def init_ee_with_ui():
    """Inicializa Earth Engine con UI amigable."""
    import ee

    if "ee_initialized" in st.session_state and st.session_state.ee_initialized:
        return True

    try:
        project = st.session_state.get("ee_project", DEFAULT_PROJECT)
        ee.Initialize(project=project)
        st.session_state.ee_initialized = True
        st.session_state.ee_project = project
        return True
    except Exception:
        st.session_state.ee_initialized = False
        return False
```

#### UI de Autenticación
```python
def show_ee_auth_instructions():
    """Muestra opciones de autenticación."""

    st.warning("⚠️ Earth Engine authentication required")

    st.markdown("**Enter your Google Cloud Project ID:**")

    col1, col2 = st.columns([3, 1])

    with col1:
        project_id = st.text_input(
            "Project ID",
            value=DEFAULT_PROJECT,
            key="ee_project_input",
            label_visibility="collapsed"
        )

    with col2:
        connect_btn = st.button("🔗 Connect", type="primary")

    if connect_btn and project_id:
        with st.spinner("Connecting..."):
            try:
                ee.Initialize(project=project_id)
                st.session_state.ee_initialized = True
                st.session_state.ee_project = project_id
                st.success(f"✅ Connected to: {project_id}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed: {e}")
```

### pages/1_Analysis.py - Análisis

#### Componentes Principales

```python
def analysis_page():
    st.title("📊 Vegetation Change Analysis")

    # 1. Upload AOI
    st.subheader("1. Upload Area of Interest")
    uploaded_file = st.file_uploader(
        "Upload AOI file",
        type=['kmz', 'kml', 'geojson', 'gpkg', 'shp'],
    )

    if uploaded_file:
        # Guardar archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(uploaded_file.getvalue())
            filepath = f.name

        # Cargar AOI
        gdf = load_aoi(filepath)
        st.success(f"✅ Loaded {len(gdf)} features")

        # Mostrar preview
        st.map(gdf)

    # 2. Select Parameters
    st.subheader("2. Analysis Parameters")

    col1, col2 = st.columns(2)

    with col1:
        periods = st.multiselect(
            "Periods",
            options=list(TEMPORAL_PERIODS.keys()),
            default=["1990s", "present"]
        )

    with col2:
        indices = st.multiselect(
            "Indices",
            options=list(INDEX_REGISTRY.keys()),
            default=["ndvi"]
        )

    reference = st.selectbox(
        "Reference Period",
        options=periods,
        index=0
    )

    # 3. Run Analysis
    st.subheader("3. Run Analysis")

    if st.button("🚀 Run Analysis", type="primary"):
        with st.status("Running analysis...", expanded=True) as status:
            st.write("Creating composites...")
            # ... proceso

            results = analyze_vegetation_change(
                aoi=aoi,
                periods=periods,
                indices=indices,
                reference_period=reference
            )

            st.session_state.analysis_results = results
            status.update(label="Complete!", state="complete")

        st.success("Analysis complete! Go to Map page to view results.")
```

### pages/2_Map.py - Visualización

#### Componentes Principales

```python
def map_page():
    st.title("🗺️ Results Map")

    if "analysis_results" not in st.session_state:
        st.warning("No analysis results. Run analysis first.")
        return

    results = st.session_state.analysis_results

    # Sidebar controls
    with st.sidebar:
        st.header("Layer Controls")

        show_aoi = st.checkbox("Show AOI", value=True)

        selected_period = st.selectbox(
            "Composite Period",
            options=list(results['composites'].keys())
        )

        show_change = st.checkbox("Show Change Map", value=True)

        if show_change:
            change_pair = st.selectbox(
                "Change Comparison",
                options=list(results['changes'].keys())
            )

    # Create map
    from streamlit_folium import st_folium

    vmap = create_analysis_map(results, aoi)

    # Display
    st_folium(vmap.map, width=None, height=600)

    # Statistics
    st.subheader("📊 Statistics")

    for pair, stats in results['statistics'].items():
        st.markdown(f"**{pair}**")

        for index, data in stats.items():
            df = pd.DataFrame({
                'Class': list(data['class_counts'].keys()),
                'Pixels': list(data['class_counts'].values()),
                'Area (ha)': list(data['area_ha'].values()),
                '%': list(data['class_percentages'].values()),
            })
            st.dataframe(df, use_container_width=True)
```

### Diagrama de Flujo de la Aplicación

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT APPLICATION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                      Home.py                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │    │
│  │  │   Check EE  │→ │  Auth UI    │→ │  Overview   │      │    │
│  │  │   Status    │  │  (Project)  │  │  & Demo     │      │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                      │
│           ┌───────────────┴───────────────┐                     │
│           ▼                               ▼                      │
│  ┌─────────────────────┐        ┌─────────────────────┐         │
│  │   1_Analysis.py     │        │     2_Map.py        │         │
│  │                     │        │                     │         │
│  │  1. Upload AOI      │        │  1. Load Results    │         │
│  │     └─ KMZ/GeoJSON  │        │     └─ session_state│         │
│  │                     │        │                     │         │
│  │  2. Select Params   │        │  2. Layer Controls  │         │
│  │     └─ Periods      │        │     └─ Checkboxes   │         │
│  │     └─ Indices      │        │                     │         │
│  │                     │        │  3. Folium Map      │         │
│  │  3. Run Analysis    │───────▶│     └─ Composites   │         │
│  │     └─ Pipeline     │ save   │     └─ Changes      │         │
│  │     └─ Save Results │results │     └─ Legend       │         │
│  │                     │        │                     │         │
│  │                     │        │  4. Statistics      │         │
│  │                     │        │     └─ Tables       │         │
│  └─────────────────────┘        └─────────────────────┘         │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Session State                         │    │
│  │  - ee_initialized: bool                                  │    │
│  │  - ee_project: str                                       │    │
│  │  - analysis_results: Dict                                │    │
│  │  - aoi_gdf: GeoDataFrame                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Comandos de Ejecución

```bash
# Desarrollo
streamlit run app/Home.py

# Con puerto específico
streamlit run app/Home.py --server.port 8505

# Background
nohup streamlit run app/Home.py > /tmp/streamlit.log 2>&1 &
```
