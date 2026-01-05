# Local Development Setup

Complete guide to setting up the development environment.

## Prerequisites

- Python 3.9+
- Git
- Google Cloud account (for Earth Engine)

## Quick Setup

```bash
# Clone repository
git clone https://github.com/your-org/vegetation-change-platform.git
cd vegetation-change-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install with development dependencies
pip install -e ".[all]"

# Authenticate Earth Engine
earthengine authenticate

# Verify installation
python -c "import ee; ee.Initialize(); print('EE Ready!')"
```

---

## Detailed Setup

### 1. Python Environment

#### Using venv (Recommended)

```bash
# Create environment
python -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Verify
which python  # Should point to venv
```

#### Using conda

```bash
conda create -n vegchange python=3.11
conda activate vegchange

# Install geospatial dependencies
conda install -c conda-forge geopandas earthengine-api
```

### 2. Install Package

```bash
# Core package only
pip install -e .

# With development tools
pip install -e ".[dev]"

# With app dependencies (Streamlit)
pip install -e ".[app]"

# With API dependencies (FastAPI)
pip install -e ".[api]"

# Everything
pip install -e ".[all]"
```

### 3. Earth Engine Authentication

```bash
# Interactive authentication
earthengine authenticate

# For headless servers
earthengine authenticate --auth_mode=notebook
```

#### Service Account (CI/CD)

```python
import ee

# Using service account
credentials = ee.ServiceAccountCredentials(
    email='your-service-account@project.iam.gserviceaccount.com',
    key_file='path/to/key.json'
)
ee.Initialize(credentials)
```

### 4. Verify Installation

```bash
# Run tests
pytest tests/ -v

# Check all imports
python -c "
from engine.composites import create_landsat_composite
from engine.indices import add_ndvi
from engine.change import classify_change
from services.change_orchestrator import ChangeOrchestrator
print('All imports successful!')
"
```

---

## Development Tools

### Code Formatting

```bash
# Format code
black veg_change_engine/ engine/ services/ app/ cli/

# Sort imports
isort veg_change_engine/ engine/ services/ app/ cli/

# Or use make
make format
```

### Linting

```bash
# Run ruff linter
ruff check .

# Run mypy type checker
mypy veg_change_engine/

# Or use make
make lint
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=veg_change_engine --cov=engine

# Run specific test file
pytest tests/test_indices.py -v

# Run specific test
pytest tests/test_indices.py::test_ndvi_calculation -v
```

---

## Running Services

### Streamlit Dashboard

```bash
# Default port (8501)
streamlit run app/Home.py

# Custom port
streamlit run app/Home.py --server.port 8502

# With auto-reload
streamlit run app/Home.py --server.runOnSave true
```

Access at: http://localhost:8501

### FastAPI Server

```bash
# Development with auto-reload
uvicorn app.api.main:app --reload --port 8000

# Multiple workers
uvicorn app.api.main:app --workers 4 --port 8000
```

Access at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Jupyter Lab

```bash
# Start Jupyter
jupyter lab

# With custom port
jupyter lab --port 8888
```

---

## Project Structure

```
vegetation-change-platform/
├── engine/                 # Core GEE logic
│   ├── composites/         # Composite creation
│   ├── indices/            # Spectral indices
│   ├── change/             # Change detection
│   └── io/                 # Input/output
├── services/               # Business logic
│   └── change_orchestrator.py
├── app/
│   ├── api/                # FastAPI REST API
│   └── dashboard/          # Streamlit app
├── veg_change_engine/      # Backward compat re-exports
├── cli/                    # Command-line interface
├── notebooks/              # Educational notebooks
├── tests/                  # Test suite
├── docs/                   # Documentation
└── scripts/                # Utility scripts
```

---

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Earth Engine
EE_PROJECT=your-project-id

# API settings
API_HOST=0.0.0.0
API_PORT=8000

# Streamlit settings
STREAMLIT_SERVER_PORT=8501

# Output settings
OUTPUT_DIR=./output
```

Load in Python:

```python
from dotenv import load_dotenv
import os

load_dotenv()
project = os.getenv('EE_PROJECT')
```

### Application Config

Create `config.yaml`:

```yaml
earth_engine:
  project: your-project-id
  default_scale: 30

analysis:
  default_periods:
    - 1990s
    - present
  default_indices:
    - ndvi
  cloud_threshold: 20

export:
  drive_folder: VegChange
  scale: 30
```

---

## IDE Setup

### VS Code

Recommended extensions:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "ms-toolsai.jupyter"
  ]
}
```

Settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### PyCharm

1. Open project folder
2. Configure Python interpreter: Settings > Project > Python Interpreter
3. Add venv interpreter
4. Enable Black formatter: Settings > Tools > Black

---

## Common Development Tasks

### Adding a New Index

1. Create index class in `engine/indices/`:

```python
# engine/indices/custom.py
from .base import SpectralIndex, register_index

@register_index
class MyIndex(SpectralIndex):
    name = "myindex"
    full_name = "My Custom Index"
    formula = "(B1 - B2) / (B1 + B2)"

    def compute(self, image):
        b1 = image.select('band1')
        b2 = image.select('band2')
        return b1.subtract(b2).divide(b1.add(b2)).rename(self.name)
```

2. Export in `__init__.py`:

```python
from .custom import MyIndex
```

3. Add tests:

```python
# tests/test_indices.py
def test_myindex():
    ...
```

### Adding a New API Endpoint

1. Create route in `app/api/routes/`:

```python
# app/api/routes/custom.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/custom")
async def get_custom():
    return {"data": "value"}
```

2. Include in `main.py`:

```python
from app.api.routes.custom import router as custom_router
app.include_router(custom_router)
```

---

## Troubleshooting

### Earth Engine Errors

```bash
# Re-authenticate
earthengine authenticate --force

# Check credentials
earthengine ls users/your-username
```

### Import Errors

```bash
# Verify package installation
pip show veg-change-engine

# Check Python path
python -c "import sys; print(sys.path)"
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Memory Issues

```python
# For large analyses, increase batch size
import ee
ee.data.setMaxBatchSize(100)
```

---

## Next Steps

- [Production Deployment](production.md)
- [Docker Deployment](docker.md)
