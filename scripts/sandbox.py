#!/usr/bin/env python3
"""
Verdant Sandbox - Interactive Testing Environment

This script provides a sandbox environment for testing and exploring
the Verdant platform functionality without requiring full Earth Engine
authentication.

Usage:
    python scripts/sandbox.py                 # Run all tests
    python scripts/sandbox.py --quick         # Quick smoke test
    python scripts/sandbox.py --verbose       # Detailed output
    python scripts/sandbox.py --report        # Generate HTML report
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, patch


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class TestResult:
    """Container for test results."""
    name: str
    passed: bool
    duration: float
    message: str = ""
    details: Optional[Dict[str, Any]] = None


class TestMetrics:
    """Collects and reports test metrics."""

    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = datetime.now()

    def add_result(self, result: TestResult):
        self.results.append(result)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def duration(self) -> float:
        return sum(r.duration for r in self.results)

    def summary(self) -> str:
        """Generate summary report."""
        lines = [
            "",
            "=" * 60,
            "VERDANT SANDBOX TEST RESULTS",
            "=" * 60,
            f"Total Tests: {self.total}",
            f"Passed: {self.passed} ({self.passed/self.total*100:.1f}%)" if self.total > 0 else "Passed: 0",
            f"Failed: {self.failed}",
            f"Duration: {self.duration:.2f}s",
            "=" * 60,
        ]

        if self.failed > 0:
            lines.append("\nFailed Tests:")
            for r in self.results:
                if not r.passed:
                    lines.append(f"  - {r.name}: {r.message}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "timestamp": self.start_time.isoformat(),
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "duration_seconds": self.duration,
                "pass_rate": self.passed / self.total * 100 if self.total > 0 else 0
            },
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "duration": r.duration,
                    "message": r.message,
                    "details": r.details
                }
                for r in self.results
            ]
        }


# =============================================================================
# Test Utilities
# =============================================================================

def run_test(name: str, test_func, metrics: TestMetrics, verbose: bool = False):
    """Run a single test and record results."""
    print(f"  Testing: {name}...", end=" ", flush=True)
    start = time.perf_counter()

    try:
        result = test_func()
        duration = time.perf_counter() - start

        if isinstance(result, tuple):
            passed, message = result
        else:
            passed = bool(result)
            message = ""

        metrics.add_result(TestResult(
            name=name,
            passed=passed,
            duration=duration,
            message=message
        ))

        if passed:
            print(f"PASS ({duration:.3f}s)")
        else:
            print(f"FAIL ({duration:.3f}s)")
            if verbose and message:
                print(f"    -> {message}")

    except Exception as e:
        duration = time.perf_counter() - start
        metrics.add_result(TestResult(
            name=name,
            passed=False,
            duration=duration,
            message=str(e)
        ))
        print(f"ERROR ({duration:.3f}s)")
        if verbose:
            print(f"    -> {e}")


# =============================================================================
# Test Suites
# =============================================================================

def test_imports() -> Tuple[bool, str]:
    """Test all major imports work."""
    try:
        from engine.config import TEMPORAL_PERIODS, CHANGE_THRESHOLDS
        from engine.indices import INDEX_REGISTRY, get_index
        from engine.composites import create_landsat_composite
        from engine.change import classify_change
        from engine.io.aoi import load_aoi
        from services.change_orchestrator import ChangeOrchestrator
        return True, ""
    except ImportError as e:
        return False, f"Import failed: {e}"


def test_config_structure() -> Tuple[bool, str]:
    """Test configuration is properly structured."""
    from engine.config import TEMPORAL_PERIODS, CHANGE_THRESHOLDS

    # Check periods
    required_periods = ["1990s", "2000s", "2010s", "present"]
    for period in required_periods:
        if period not in TEMPORAL_PERIODS:
            return False, f"Missing period: {period}"

    # Check thresholds
    for index in ["ndvi", "nbr"]:
        if index not in CHANGE_THRESHOLDS:
            return False, f"Missing thresholds for: {index}"

    return True, ""


def test_index_registry() -> Tuple[bool, str]:
    """Test spectral index registry."""
    from engine.indices import INDEX_REGISTRY, get_index

    required_indices = ["ndvi", "nbr", "ndwi", "evi", "ndmi"]

    for index_name in required_indices:
        if index_name not in INDEX_REGISTRY:
            return False, f"Missing index: {index_name}"

        try:
            idx = get_index(index_name)
            if not hasattr(idx, 'compute'):
                return False, f"Index {index_name} missing compute method"
        except Exception as e:
            return False, f"Error getting index {index_name}: {e}"

    return True, ""


def test_aoi_loading() -> Tuple[bool, str]:
    """Test AOI loading from GeoJSON."""
    import tempfile
    import json
    from engine.io.aoi import load_aoi

    geojson = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-62.5, -4.0], [-62.0, -4.0],
                [-62.0, -3.5], [-62.5, -3.5], [-62.5, -4.0]
            ]]
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
        json.dump(geojson, f)
        filepath = f.name

    try:
        gdf = load_aoi(filepath)
        if len(gdf) != 1:
            return False, f"Expected 1 feature, got {len(gdf)}"
        return True, ""
    except Exception as e:
        return False, f"AOI loading failed: {e}"
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_threshold_ordering() -> Tuple[bool, str]:
    """Test change thresholds are in correct order."""
    from engine.config import CHANGE_THRESHOLDS

    for index, thresholds in CHANGE_THRESHOLDS.items():
        if thresholds["strong_loss"] >= thresholds["moderate_loss"]:
            return False, f"{index}: strong_loss should be < moderate_loss"
        if thresholds["moderate_loss"] >= thresholds["moderate_gain"]:
            return False, f"{index}: moderate_loss should be < moderate_gain"
        if thresholds["moderate_gain"] >= thresholds["strong_gain"]:
            return False, f"{index}: moderate_gain should be < strong_gain"

    return True, ""


def test_period_date_validity() -> Tuple[bool, str]:
    """Test temporal period dates are valid."""
    from datetime import datetime
    from engine.config import TEMPORAL_PERIODS

    for period_name, config in TEMPORAL_PERIODS.items():
        try:
            start = datetime.strptime(config["start"], "%Y-%m-%d")
            end = datetime.strptime(config["end"], "%Y-%m-%d")
            if start >= end:
                return False, f"{period_name}: start >= end"
        except Exception as e:
            return False, f"{period_name}: invalid date format - {e}"

    return True, ""


def test_orchestrator_initialization() -> Tuple[bool, str]:
    """Test ChangeOrchestrator can be initialized."""
    try:
        from services.change_orchestrator import ChangeOrchestrator
        orchestrator = ChangeOrchestrator()
        return True, ""
    except Exception as e:
        return False, f"Orchestrator init failed: {e}"


def test_mock_analysis() -> Tuple[bool, str]:
    """Test mock analysis workflow."""
    with patch('ee.Initialize'):
        with patch('ee.Geometry.Rectangle') as mock_geom:
            mock_geom.return_value = MagicMock()

            try:
                from services.change_orchestrator import ChangeOrchestrator
                orchestrator = ChangeOrchestrator()

                # Mock the analyze method
                with patch.object(orchestrator, 'analyze') as mock_analyze:
                    mock_analyze.return_value = {
                        "composites": {"1990s": MagicMock(), "present": MagicMock()},
                        "changes": {"1990s_to_present_ndvi": MagicMock()},
                        "statistics": {"1990s_to_present_ndvi": {"area_by_class": {}}}
                    }

                    result = orchestrator.analyze(
                        aoi=MagicMock(),
                        periods=["1990s", "present"],
                        indices=["ndvi"]
                    )

                    if "composites" not in result:
                        return False, "Missing composites in result"
                    if "changes" not in result:
                        return False, "Missing changes in result"
                    if "statistics" not in result:
                        return False, "Missing statistics in result"

                    return True, ""

            except Exception as e:
                return False, f"Mock analysis failed: {e}"


def test_api_models() -> Tuple[bool, str]:
    """Test API request/response models."""
    try:
        from app.api.models.requests import AnalysisRequest, BoundingBox
        from app.api.models.responses import AnalysisResponse, JobStatus

        # Test creating models
        bbox = BoundingBox(min_lon=-62.5, min_lat=-4.0, max_lon=-62.0, max_lat=-3.5)
        request = AnalysisRequest(
            site_name="Test",
            bbox=bbox,
            periods=["1990s", "present"],
            indices=["ndvi"]
        )

        if request.site_name != "Test":
            return False, "Request model field mismatch"

        return True, ""
    except Exception as e:
        return False, f"API models failed: {e}"


# =============================================================================
# Main Execution
# =============================================================================

def run_quick_tests(metrics: TestMetrics, verbose: bool = False):
    """Run quick smoke tests."""
    print("\n Quick Smoke Tests")
    print("-" * 40)

    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config_structure),
        ("Index Registry", test_index_registry),
    ]

    for name, test_func in tests:
        run_test(name, test_func, metrics, verbose)


def run_all_tests(metrics: TestMetrics, verbose: bool = False):
    """Run all tests."""
    print("\n Module Tests")
    print("-" * 40)

    tests = [
        ("Imports", test_imports),
        ("Configuration Structure", test_config_structure),
        ("Index Registry", test_index_registry),
        ("Threshold Ordering", test_threshold_ordering),
        ("Period Date Validity", test_period_date_validity),
        ("AOI Loading", test_aoi_loading),
        ("Orchestrator Init", test_orchestrator_initialization),
        ("Mock Analysis", test_mock_analysis),
        ("API Models", test_api_models),
    ]

    for name, test_func in tests:
        run_test(name, test_func, metrics, verbose)


def generate_html_report(metrics: TestMetrics, output_path: str = "sandbox_report.html"):
    """Generate HTML report."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Verdant Sandbox Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2e7d32; border-bottom: 3px solid #2e7d32; padding-bottom: 10px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ background: #e8f5e9; padding: 20px; border-radius: 8px; text-align: center; flex: 1; }}
        .stat.failed {{ background: #ffebee; }}
        .stat h2 {{ margin: 0; font-size: 36px; color: #2e7d32; }}
        .stat.failed h2 {{ color: #c62828; }}
        .stat p {{ margin: 5px 0 0 0; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; }}
        .pass {{ color: #2e7d32; font-weight: bold; }}
        .fail {{ color: #c62828; font-weight: bold; }}
        .timestamp {{ color: #666; font-size: 14px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Verdant Sandbox Test Report</h1>

        <div class="summary">
            <div class="stat">
                <h2>{metrics.total}</h2>
                <p>Total Tests</p>
            </div>
            <div class="stat">
                <h2>{metrics.passed}</h2>
                <p>Passed</p>
            </div>
            <div class="stat {'failed' if metrics.failed > 0 else ''}">
                <h2>{metrics.failed}</h2>
                <p>Failed</p>
            </div>
            <div class="stat">
                <h2>{metrics.duration:.2f}s</h2>
                <p>Duration</p>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Test</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Message</th>
                </tr>
            </thead>
            <tbody>
"""

    for result in metrics.results:
        status_class = "pass" if result.passed else "fail"
        status_text = "PASS" if result.passed else "FAIL"
        html += f"""
                <tr>
                    <td>{result.name}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{result.duration:.3f}s</td>
                    <td>{result.message}</td>
                </tr>
"""

    html += f"""
            </tbody>
        </table>

        <p class="timestamp">Generated: {metrics.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
"""

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"\n HTML report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Verdant Sandbox Testing Environment")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke tests only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--json", type=str, help="Export results to JSON file")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("VERDANT SANDBOX TESTING ENVIRONMENT")
    print("=" * 60)

    metrics = TestMetrics()

    if args.quick:
        run_quick_tests(metrics, args.verbose)
    else:
        run_all_tests(metrics, args.verbose)

    print(metrics.summary())

    if args.report:
        generate_html_report(metrics)

    if args.json:
        with open(args.json, 'w') as f:
            json.dump(metrics.to_dict(), f, indent=2)
        print(f"\n JSON results saved to: {args.json}")

    # Exit with appropriate code
    sys.exit(0 if metrics.failed == 0 else 1)


if __name__ == "__main__":
    main()
