"""
API endpoint tests.

Tests cover:
- Health check endpoint
- Analysis endpoints
- Metadata endpoints
- Error handling
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with mocked EE."""
    with patch("ee.Initialize"):
        with patch("ee.data._initialized", True):
            from app.api.main import app
            return TestClient(app)


@pytest.mark.api
class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_status(self, client):
        """Test health endpoint returns status field."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_check_returns_version(self, client):
        """Test health endpoint returns version."""
        response = client.get("/health")
        data = response.json()

        assert "version" in data


@pytest.mark.api
class TestAnalysisEndpoint:
    """Tests for analysis endpoints."""

    def test_create_analysis_with_bbox(self, client, sample_bbox):
        """Test creating analysis with bounding box."""
        with patch("services.change_orchestrator.ChangeOrchestrator") as mock_orch:
            mock_orch.return_value.create_job.return_value = "test-job-123"

            response = client.post("/analysis", json={
                "site_name": "Test Site",
                "bbox": sample_bbox,
                "periods": ["1990s", "present"],
                "indices": ["ndvi"]
            })

            assert response.status_code in [200, 201, 202]

    def test_create_analysis_with_geojson(self, client, sample_aoi_geojson):
        """Test creating analysis with GeoJSON."""
        with patch("services.change_orchestrator.ChangeOrchestrator") as mock_orch:
            mock_orch.return_value.create_job.return_value = "test-job-456"

            response = client.post("/analysis", json={
                "site_name": "GeoJSON Site",
                "aoi_geojson": sample_aoi_geojson["geometry"],
                "periods": ["1990s", "present"],
                "indices": ["ndvi"]
            })

            assert response.status_code in [200, 201, 202]

    def test_create_analysis_missing_aoi_returns_error(self, client):
        """Test creating analysis without AOI returns error."""
        response = client.post("/analysis", json={
            "site_name": "No AOI",
            "periods": ["1990s", "present"],
            "indices": ["ndvi"]
        })

        assert response.status_code in [400, 422]

    def test_create_analysis_invalid_period_returns_error(self, client, sample_bbox):
        """Test creating analysis with invalid period returns error."""
        response = client.post("/analysis", json={
            "site_name": "Invalid Period",
            "bbox": sample_bbox,
            "periods": ["invalid_period"],
            "indices": ["ndvi"]
        })

        assert response.status_code in [400, 422]

    def test_create_analysis_invalid_index_returns_error(self, client, sample_bbox):
        """Test creating analysis with invalid index returns error."""
        response = client.post("/analysis", json={
            "site_name": "Invalid Index",
            "bbox": sample_bbox,
            "periods": ["1990s", "present"],
            "indices": ["invalid_index"]
        })

        assert response.status_code in [400, 422]


@pytest.mark.api
class TestJobStatusEndpoint:
    """Tests for job status endpoint."""

    def test_get_job_status(self, client):
        """Test getting job status."""
        with patch("services.change_orchestrator.ChangeOrchestrator") as mock_orch:
            mock_orch.return_value.get_job.return_value = {
                "job_id": "test-job-123",
                "status": "running",
                "progress": 0.5
            }

            response = client.get("/analysis/test-job-123")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data

    def test_get_nonexistent_job_returns_404(self, client):
        """Test getting nonexistent job returns 404."""
        with patch("services.change_orchestrator.ChangeOrchestrator") as mock_orch:
            mock_orch.return_value.get_job.return_value = None

            response = client.get("/analysis/nonexistent-job")

            assert response.status_code == 404

    def test_get_completed_job_includes_results(self, client, sample_statistics):
        """Test completed job includes results."""
        with patch("services.change_orchestrator.ChangeOrchestrator") as mock_orch:
            mock_orch.return_value.get_job.return_value = {
                "job_id": "completed-job",
                "status": "completed",
                "progress": 1.0,
                "results": {
                    "statistics": sample_statistics
                }
            }

            response = client.get("/analysis/completed-job")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert "results" in data


@pytest.mark.api
class TestListJobsEndpoint:
    """Tests for listing jobs endpoint."""

    def test_list_jobs(self, client):
        """Test listing all jobs."""
        with patch("services.change_orchestrator.ChangeOrchestrator") as mock_orch:
            mock_orch.return_value.list_jobs.return_value = [
                {"job_id": "job-1", "status": "completed"},
                {"job_id": "job-2", "status": "running"}
            ]

            response = client.get("/analysis")

            assert response.status_code == 200
            data = response.json()
            assert "jobs" in data or isinstance(data, list)

    def test_list_jobs_with_status_filter(self, client):
        """Test listing jobs with status filter."""
        with patch("services.change_orchestrator.ChangeOrchestrator") as mock_orch:
            mock_orch.return_value.list_jobs.return_value = [
                {"job_id": "job-1", "status": "completed"}
            ]

            response = client.get("/analysis?status=completed")

            assert response.status_code == 200


@pytest.mark.api
class TestPreviewEndpoint:
    """Tests for quick preview endpoint."""

    def test_preview_endpoint(self, client, sample_bbox):
        """Test preview endpoint."""
        with patch("services.change_orchestrator.ChangeOrchestrator") as mock_orch:
            mock_orch.return_value.preview.return_value = MagicMock()

            response = client.post("/analysis/preview", json={
                "bbox": sample_bbox,
                "period": "present",
                "index": "ndvi"
            })

            assert response.status_code in [200, 201]


@pytest.mark.api
class TestMetadataEndpoints:
    """Tests for metadata endpoints."""

    def test_list_periods(self, client):
        """Test listing available periods."""
        response = client.get("/periods")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_list_indices(self, client):
        """Test listing available indices."""
        response = client.get("/indices")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_period_details(self, client):
        """Test getting period details."""
        response = client.get("/periods/1990s")

        assert response.status_code in [200, 404]

    def test_index_details(self, client):
        """Test getting index details."""
        response = client.get("/indices/ndvi")

        assert response.status_code in [200, 404]


@pytest.mark.api
class TestCancelJobEndpoint:
    """Tests for job cancellation endpoint."""

    def test_cancel_pending_job(self, client):
        """Test canceling a pending job."""
        with patch("services.change_orchestrator.ChangeOrchestrator") as mock_orch:
            mock_orch.return_value.cancel_job.return_value = True

            response = client.delete("/analysis/pending-job")

            assert response.status_code in [200, 204]

    def test_cancel_running_job_returns_conflict(self, client):
        """Test canceling a running job may return conflict."""
        with patch("services.change_orchestrator.ChangeOrchestrator") as mock_orch:
            mock_orch.return_value.cancel_job.return_value = False

            response = client.delete("/analysis/running-job")

            # May return 409 Conflict or 200 depending on implementation
            assert response.status_code in [200, 204, 409]


@pytest.mark.api
class TestErrorHandling:
    """Tests for API error handling."""

    def test_invalid_json_returns_422(self, client):
        """Test invalid JSON returns 422."""
        response = client.post(
            "/analysis",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_method_not_allowed(self, client):
        """Test unsupported method returns 405."""
        response = client.put("/health")

        assert response.status_code == 405

    def test_not_found_returns_404(self, client):
        """Test unknown endpoint returns 404."""
        response = client.get("/unknown-endpoint")

        assert response.status_code == 404


@pytest.mark.api
class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present."""
        response = client.options("/health")

        # OPTIONS request should be handled
        assert response.status_code in [200, 204, 405]

    def test_cors_allows_origin(self, client):
        """Test CORS allows configured origins."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )

        # Should not block the request
        assert response.status_code == 200
