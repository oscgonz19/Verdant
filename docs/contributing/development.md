# Contributing Guide

Thank you for your interest in contributing to the Vegetation Change Intelligence Platform!

## Ways to Contribute

- **Bug Reports**: Found a bug? Open an issue
- **Feature Requests**: Have an idea? Let's discuss
- **Code Contributions**: PRs welcome!
- **Documentation**: Help improve docs
- **Examples**: Share use cases and tutorials

---

## Getting Started

### 1. Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/vegetation-change-platform.git
cd vegetation-change-platform

# Add upstream remote
git remote add upstream https://github.com/original-org/vegetation-change-platform.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install with development dependencies
pip install -e ".[all]"

# Install pre-commit hooks
pre-commit install
```

### 3. Create a Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

---

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=veg_change_engine --cov=engine

# Run specific test file
pytest tests/test_indices.py -v

# Run specific test
pytest tests/test_indices.py::test_ndvi_calculation -v
```

### Code Quality Checks

```bash
# Format code
make format

# Run linters
make lint

# Run type checking
mypy veg_change_engine/ engine/

# Run all checks
make check
```

### Running Services Locally

```bash
# Streamlit dashboard
make app

# FastAPI server
make api

# Run demo
make demo
```

---

## Making Changes

### Adding a New Feature

1. **Discuss First**: Open an issue to discuss the feature
2. **Design**: Consider architecture and API design
3. **Implement**: Write clean, documented code
4. **Test**: Add comprehensive tests
5. **Document**: Update relevant documentation

### Fixing a Bug

1. **Reproduce**: Create a minimal reproduction
2. **Add Test**: Write a failing test for the bug
3. **Fix**: Make the minimal fix
4. **Verify**: Ensure the test passes

### Code Organization

```
engine/                 # Add new core functionality here
├── composites/         # Composite-related features
├── indices/            # New spectral indices
├── change/             # Change detection features
└── io/                 # Input/output features

services/               # Business logic and orchestration
app/api/                # API endpoints
app/dashboard/          # Streamlit pages
tests/                  # Mirror the source structure
```

---

## Pull Request Process

### Before Submitting

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   make check
   pytest tests/ -v
   ```

3. **Update documentation** if needed

4. **Write meaningful commit messages**

### PR Guidelines

- **Title**: Clear, descriptive title
- **Description**: Explain what and why
- **Link Issues**: Reference related issues
- **Small PRs**: Keep changes focused
- **Tests**: Include tests for new features

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #123

## Testing
Describe how you tested the changes.

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

---

## Commit Messages

Follow conventional commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Examples

```bash
# Feature
git commit -m "feat(indices): add SAVI spectral index"

# Bug fix
git commit -m "fix(composites): handle empty image collections"

# Documentation
git commit -m "docs: add tutorial for change detection"

# Refactor
git commit -m "refactor(io): simplify AOI loader interface"
```

---

## Adding New Features

### Adding a New Spectral Index

1. Create class in `engine/indices/`:

```python
# engine/indices/soil.py
from .base import SpectralIndex, register_index

@register_index
class SAVIIndex(SpectralIndex):
    """Soil Adjusted Vegetation Index."""

    name = "savi"
    full_name = "Soil Adjusted Vegetation Index"
    description = "Minimizes soil brightness influences"
    formula = "(NIR - Red) / (NIR + Red + L) * (1 + L)"
    value_range = (-1.0, 1.0)

    def __init__(self, L: float = 0.5):
        self.L = L

    def compute(self, image):
        nir = image.select('nir')
        red = image.select('red')
        L = self.L

        savi = (nir.subtract(red)
                .divide(nir.add(red).add(L))
                .multiply(1 + L)
                .rename(self.name))

        return image.addBands(savi)
```

2. Export in `__init__.py`:

```python
from .soil import SAVIIndex
```

3. Add tests:

```python
# tests/test_indices.py
def test_savi_index():
    from engine.indices import SAVIIndex

    index = SAVIIndex(L=0.5)
    assert index.name == "savi"

    # Test with mock image
    result = index.compute(mock_image)
    assert 'savi' in result.bandNames().getInfo()
```

4. Update documentation

### Adding a New API Endpoint

1. Create route:

```python
# app/api/routes/custom.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/custom", tags=["custom"])

class CustomRequest(BaseModel):
    param: str

class CustomResponse(BaseModel):
    result: str

@router.post("/", response_model=CustomResponse)
async def custom_endpoint(request: CustomRequest):
    """Custom endpoint description."""
    return CustomResponse(result=f"Processed: {request.param}")
```

2. Include in main app:

```python
# app/api/main.py
from app.api.routes.custom import router as custom_router
app.include_router(custom_router)
```

3. Add tests:

```python
# tests/test_api.py
def test_custom_endpoint(client):
    response = client.post("/custom/", json={"param": "test"})
    assert response.status_code == 200
    assert response.json()["result"] == "Processed: test"
```

---

## Testing Guidelines

### Test Structure

```python
# tests/test_feature.py
import pytest
from engine.feature import MyFeature

class TestMyFeature:
    """Tests for MyFeature class."""

    @pytest.fixture
    def feature(self):
        """Create feature instance for tests."""
        return MyFeature()

    def test_basic_functionality(self, feature):
        """Test basic feature operation."""
        result = feature.do_something()
        assert result is not None

    def test_edge_case(self, feature):
        """Test edge case handling."""
        with pytest.raises(ValueError):
            feature.do_something(invalid_input)

    @pytest.mark.parametrize("input,expected", [
        ("a", 1),
        ("b", 2),
        ("c", 3),
    ])
    def test_parametrized(self, feature, input, expected):
        """Test with multiple inputs."""
        assert feature.process(input) == expected
```

### Mocking Earth Engine

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_ee():
    """Mock Earth Engine for unit tests."""
    with patch('ee.Initialize'):
        with patch('ee.Image') as mock_image:
            mock_image.return_value.select.return_value = Mock()
            yield mock_image

def test_with_mocked_ee(mock_ee):
    """Test that doesn't require EE connection."""
    from engine.indices import add_ndvi

    result = add_ndvi(mock_ee())
    assert mock_ee.called
```

---

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int = 10) -> Dict[str, Any]:
    """Short description of function.

    Longer description if needed. Can span multiple lines
    and include usage examples.

    Args:
        param1: Description of param1.
        param2: Description of param2. Defaults to 10.

    Returns:
        Dictionary containing:
            - key1: Description
            - key2: Description

    Raises:
        ValueError: If param1 is empty.
        RuntimeError: If processing fails.

    Example:
        >>> result = function_name("test", 20)
        >>> print(result["key1"])
        value1
    """
    pass
```

### Updating Documentation

Documentation lives in `docs/`:

```
docs/
├── getting-started/    # Installation, quickstart
├── guides/             # User guides
├── tutorials/          # Step-by-step tutorials
├── technical/          # API reference, architecture
├── academic/           # Scientific methodology
├── deployment/         # Deployment guides
└── contributing/       # This guide
```

Build docs locally:

```bash
# If using MkDocs
mkdocs serve

# View at http://localhost:8000
```

---

## Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release branch: `release/v1.2.0`
4. Run full test suite
5. Create PR to main
6. After merge, tag release: `git tag v1.2.0`
7. Push tags: `git push --tags`

---

## Getting Help

- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Email**: contact@example.com

---

## Code of Conduct

Be respectful, inclusive, and constructive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).
