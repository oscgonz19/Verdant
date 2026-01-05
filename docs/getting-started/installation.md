# Installation Guide

This guide covers the installation of the Vegetation Change Intelligence Platform and all its dependencies.

## Prerequisites

### System Requirements

- **Python**: 3.9 or higher (3.10+ recommended)
- **Operating System**: Linux, macOS, or Windows
- **Memory**: Minimum 4GB RAM (8GB+ recommended for large analyses)
- **Storage**: ~500MB for dependencies

### Google Earth Engine Account

You need a Google Earth Engine account to use this platform:

1. Visit [Google Earth Engine](https://earthengine.google.com/)
2. Click "Sign Up" and follow the registration process
3. Wait for account approval (usually within 24 hours)

## Installation Methods

### Method 1: pip install (Recommended)

```bash
# Clone the repository
git clone https://github.com/oscgonz19/vegetation-change-platform.git
cd vegetation-change-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core package
pip install -e .

# Install with all dependencies (development + apps)
pip install -e ".[all]"
```

### Method 2: Using Make

```bash
# Clone and enter directory
git clone https://github.com/oscgonz19/vegetation-change-platform.git
cd vegetation-change-platform

# Install everything
make dev-install
```

### Method 3: Conda Environment

```bash
# Create conda environment
conda create -n vegchange python=3.10
conda activate vegchange

# Install geospatial dependencies
conda install -c conda-forge geopandas earthengine-api folium

# Clone and install package
git clone https://github.com/oscgonz19/vegetation-change-platform.git
cd vegetation-change-platform
pip install -e ".[all]"
```

## Dependency Groups

The package offers several optional dependency groups:

| Group | Command | Description |
|-------|---------|-------------|
| Core | `pip install -e .` | Essential dependencies only |
| Dev | `pip install -e ".[dev]"` | Testing, linting, formatting |
| App | `pip install -e ".[app]"` | Streamlit dashboard |
| API | `pip install -e ".[api]"` | FastAPI REST endpoints |
| All | `pip install -e ".[all]"` | Everything |

## Earth Engine Authentication

After installation, authenticate with Earth Engine:

```bash
# Run authentication flow
earthengine authenticate

# This will:
# 1. Open a browser window
# 2. Ask you to sign in with Google
# 3. Generate credentials stored locally
```

### Verify Authentication

```python
import ee
ee.Initialize()
print("Earth Engine initialized successfully!")
```

Or use our helper:

```python
from engine.ee_init import initialize_ee, is_ee_initialized

initialize_ee()
print(f"Initialized: {is_ee_initialized()}")
```

## Troubleshooting

### Common Issues

#### 1. GDAL/GEOS Installation Errors

On Ubuntu/Debian:
```bash
sudo apt-get install libgdal-dev libgeos-dev
```

On macOS:
```bash
brew install gdal geos
```

#### 2. Earth Engine Authentication Fails

```bash
# Clear existing credentials
rm -rf ~/.config/earthengine/

# Re-authenticate
earthengine authenticate
```

#### 3. Import Errors

Ensure you're in the project root and using the virtual environment:
```bash
cd vegetation-change-platform
source venv/bin/activate
python -c "from engine import initialize_ee; print('OK')"
```

#### 4. Shapely/GeoPandas Conflicts

```bash
pip uninstall shapely geopandas
pip install shapely geopandas --no-binary shapely
```

## Verifying Installation

Run the test suite to verify everything works:

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=veg_change_engine
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Run your first analysis
- [Configuration Guide](configuration.md) - Customize settings
- [CLI Guide](../guides/cli-guide.md) - Command-line usage
