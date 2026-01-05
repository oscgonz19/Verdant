# Tutorial 4: REST API Integration

Learn how to use the REST API for automation and integration with external systems.

## Prerequisites

- API server running (`uvicorn app.api.main:app`)
- Basic understanding of REST APIs
- HTTP client (curl, requests, fetch)

## What You'll Learn

1. Start the API server
2. Submit analysis jobs
3. Monitor job progress
4. Retrieve results
5. Integrate with external applications

---

## Starting the API Server

### Development Mode

```bash
# Start with auto-reload
uvicorn app.api.main:app --reload --port 8000

# Or using make
make api
```

### Production Mode

```bash
# With multiple workers
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with gunicorn
gunicorn app.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Verify Server

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "earth_engine": true
}
```

---

## API Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/analysis` | Create analysis job |
| GET | `/analysis/{job_id}` | Get job status/results |
| DELETE | `/analysis/{job_id}` | Cancel job |
| GET | `/analysis` | List all jobs |
| POST | `/analysis/preview` | Quick preview |
| GET | `/periods` | List temporal periods |
| GET | `/indices` | List spectral indices |

---

## Creating an Analysis Job

### Using cURL

```bash
curl -X POST http://localhost:8000/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "Amazon Test Site",
    "bbox": {
      "min_lon": -62.5,
      "min_lat": -4.0,
      "max_lon": -62.0,
      "max_lat": -3.5
    },
    "periods": ["1990s", "present"],
    "indices": ["ndvi"],
    "reference_period": "1990s"
  }'
```

Response:
```json
{
  "job_id": "abc12345",
  "status": "pending",
  "message": "Analysis job created successfully",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Using Python requests

```python
import requests

API_URL = "http://localhost:8000"

# Create analysis job
response = requests.post(
    f"{API_URL}/analysis",
    json={
        "site_name": "Amazon Test Site",
        "bbox": {
            "min_lon": -62.5,
            "min_lat": -4.0,
            "max_lon": -62.0,
            "max_lat": -3.5
        },
        "periods": ["1990s", "present"],
        "indices": ["ndvi"],
        "reference_period": "1990s"
    }
)

job = response.json()
print(f"Job ID: {job['job_id']}")
print(f"Status: {job['status']}")
```

### Using JavaScript fetch

```javascript
const response = await fetch('http://localhost:8000/analysis', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    site_name: 'Amazon Test Site',
    bbox: {
      min_lon: -62.5,
      min_lat: -4.0,
      max_lon: -62.0,
      max_lat: -3.5
    },
    periods: ['1990s', 'present'],
    indices: ['ndvi'],
    reference_period: '1990s'
  })
});

const job = await response.json();
console.log(`Job ID: ${job.job_id}`);
```

### Using GeoJSON AOI

```python
# Instead of bbox, use GeoJSON geometry
response = requests.post(
    f"{API_URL}/analysis",
    json={
        "site_name": "Custom Polygon",
        "aoi_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [-62.5, -4.0],
                [-62.0, -4.0],
                [-62.0, -3.5],
                [-62.5, -3.5],
                [-62.5, -4.0]
            ]]
        },
        "periods": ["1990s", "2010s", "present"],
        "indices": ["ndvi", "nbr"]
    }
)
```

---

## Monitoring Job Progress

### Poll for Status

```python
import time

def wait_for_completion(job_id, timeout=600, interval=5):
    """Wait for job to complete with progress updates."""
    start = time.time()

    while time.time() - start < timeout:
        response = requests.get(f"{API_URL}/analysis/{job_id}")
        status = response.json()

        print(f"Status: {status['status']}, Progress: {status['progress']:.0%}")
        print(f"  Step: {status.get('current_step', 'N/A')}")

        if status['status'] == 'completed':
            return status
        elif status['status'] == 'failed':
            raise Exception(f"Job failed: {status.get('error')}")

        time.sleep(interval)

    raise TimeoutError(f"Job {job_id} did not complete in {timeout}s")

# Usage
job_id = "abc12345"
results = wait_for_completion(job_id)
print(f"\nResults: {results['results']}")
```

### Output During Processing

```
Status: running, Progress: 20%
  Step: Creating composites...
Status: running, Progress: 40%
  Step: Calculating indices...
Status: running, Progress: 60%
  Step: Detecting changes...
Status: running, Progress: 80%
  Step: Generating statistics...
Status: completed, Progress: 100%
  Step: Complete
```

---

## Retrieving Results

### Get Full Results

```python
response = requests.get(f"{API_URL}/analysis/{job_id}")
data = response.json()

if data['status'] == 'completed':
    results = data['results']

    # Access statistics
    stats = results['statistics']['1990s_to_present_ndvi']

    print("Change Statistics:")
    for class_name, area in stats['area_by_class'].items():
        print(f"  {class_name}: {area:,.1f} ha")
```

### Response Structure

```json
{
  "job_id": "abc12345",
  "status": "completed",
  "progress": 1.0,
  "current_step": "Complete",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:32:15Z",
  "results": {
    "statistics": {
      "1990s_to_present_ndvi": {
        "total_pixels": 125000,
        "area_by_class": {
          "Strong Loss": 1234.5,
          "Moderate Loss": 2345.6,
          "Stable": 15000.2,
          "Moderate Gain": 4567.8,
          "Strong Gain": 1852.4
        }
      }
    },
    "composites": {
      "1990s": {"asset_id": "..."},
      "present": {"asset_id": "..."}
    },
    "tile_urls": {
      "1990s_ndvi": "https://earthengine.googleapis.com/...",
      "present_ndvi": "https://earthengine.googleapis.com/...",
      "change_ndvi": "https://earthengine.googleapis.com/..."
    }
  }
}
```

---

## Quick Preview

For fast visualization without full analysis:

```python
response = requests.post(
    f"{API_URL}/analysis/preview",
    json={
        "bbox": {
            "min_lon": -62.5,
            "min_lat": -4.0,
            "max_lon": -62.0,
            "max_lat": -3.5
        },
        "period": "present",
        "index": "ndvi"
    }
)

preview = response.json()
print(f"Tile URL: {preview['tile_url']}")
print(f"Center: {preview['center']}")
```

---

## Listing Jobs

```python
# List all jobs
response = requests.get(f"{API_URL}/analysis")
jobs = response.json()

print(f"Total jobs: {jobs['total']}")
for job in jobs['jobs']:
    print(f"  {job['job_id']}: {job['status']}")

# Filter by status
response = requests.get(f"{API_URL}/analysis?status=completed&limit=10")
completed = response.json()
```

---

## Canceling Jobs

```python
# Cancel a pending job
response = requests.delete(f"{API_URL}/analysis/{job_id}")

if response.status_code == 200:
    print("Job cancelled")
elif response.status_code == 409:
    print("Cannot cancel running job")
```

---

## Complete Python Client

```python
"""
VegChange API Client
"""

import requests
import time
from typing import Dict, List, Optional

class VegChangeClient:
    """Client for VegChange REST API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def health_check(self) -> Dict:
        """Check API health."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def create_analysis(
        self,
        site_name: str,
        bbox: Optional[Dict] = None,
        aoi_geojson: Optional[Dict] = None,
        periods: List[str] = ["1990s", "present"],
        indices: List[str] = ["ndvi"],
        reference_period: str = "1990s"
    ) -> Dict:
        """Create a new analysis job."""
        payload = {
            "site_name": site_name,
            "periods": periods,
            "indices": indices,
            "reference_period": reference_period
        }

        if bbox:
            payload["bbox"] = bbox
        elif aoi_geojson:
            payload["aoi_geojson"] = aoi_geojson
        else:
            raise ValueError("Either bbox or aoi_geojson required")

        response = requests.post(f"{self.base_url}/analysis", json=payload)
        response.raise_for_status()
        return response.json()

    def get_status(self, job_id: str) -> Dict:
        """Get job status and results."""
        response = requests.get(f"{self.base_url}/analysis/{job_id}")
        response.raise_for_status()
        return response.json()

    def wait_for_completion(
        self,
        job_id: str,
        timeout: int = 600,
        poll_interval: int = 5,
        progress_callback=None
    ) -> Dict:
        """Wait for job completion with progress updates."""
        start = time.time()

        while time.time() - start < timeout:
            status = self.get_status(job_id)

            if progress_callback:
                progress_callback(status)

            if status['status'] == 'completed':
                return status
            elif status['status'] == 'failed':
                raise Exception(f"Job failed: {status.get('error')}")

            time.sleep(poll_interval)

        raise TimeoutError(f"Job {job_id} timed out after {timeout}s")

    def analyze(
        self,
        site_name: str,
        bbox: Optional[Dict] = None,
        aoi_geojson: Optional[Dict] = None,
        **kwargs
    ) -> Dict:
        """Create job and wait for results (synchronous)."""
        job = self.create_analysis(site_name, bbox, aoi_geojson, **kwargs)
        print(f"Created job: {job['job_id']}")

        def progress(status):
            print(f"  {status['progress']:.0%} - {status.get('current_step', '')}")

        results = self.wait_for_completion(job['job_id'], progress_callback=progress)
        return results

    def list_jobs(self, status: Optional[str] = None, limit: int = 50) -> Dict:
        """List analysis jobs."""
        params = {"limit": limit}
        if status:
            params["status"] = status

        response = requests.get(f"{self.base_url}/analysis", params=params)
        response.raise_for_status()
        return response.json()

    def cancel_job(self, job_id: str) -> Dict:
        """Cancel a pending job."""
        response = requests.delete(f"{self.base_url}/analysis/{job_id}")
        response.raise_for_status()
        return response.json()


# Usage example
if __name__ == "__main__":
    client = VegChangeClient()

    # Check health
    print(f"API Status: {client.health_check()['status']}")

    # Run analysis
    results = client.analyze(
        site_name="Test Site",
        bbox={
            "min_lon": -62.5,
            "min_lat": -4.0,
            "max_lon": -62.0,
            "max_lat": -3.5
        },
        periods=["1990s", "present"],
        indices=["ndvi"]
    )

    # Print results
    stats = results['results']['statistics']['1990s_to_present_ndvi']
    print("\nResults:")
    for class_name, area in stats['area_by_class'].items():
        print(f"  {class_name}: {area:,.1f} ha")
```

---

## Integration Examples

### Web Application (JavaScript)

```javascript
// React hook for analysis
import { useState, useEffect } from 'react';

function useVegChangeAnalysis(config) {
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const runAnalysis = async () => {
    setStatus('starting');
    setError(null);

    try {
      // Create job
      const createResponse = await fetch('/api/analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const job = await createResponse.json();

      setStatus('running');

      // Poll for results
      while (true) {
        const statusResponse = await fetch(`/api/analysis/${job.job_id}`);
        const statusData = await statusResponse.json();

        setProgress(statusData.progress);

        if (statusData.status === 'completed') {
          setResults(statusData.results);
          setStatus('completed');
          break;
        } else if (statusData.status === 'failed') {
          throw new Error(statusData.error);
        }

        await new Promise(r => setTimeout(r, 3000));
      }
    } catch (err) {
      setError(err.message);
      setStatus('failed');
    }
  };

  return { status, progress, results, error, runAnalysis };
}
```

### Automation Script

```python
#!/usr/bin/env python3
"""
Automated vegetation monitoring script.
Run daily via cron to check for changes.
"""

import json
from datetime import datetime
from pathlib import Path
from vegchange_client import VegChangeClient

# Configuration
SITES = [
    {"name": "Site A", "bbox": {...}},
    {"name": "Site B", "bbox": {...}},
]

OUTPUT_DIR = Path("monitoring_results")
OUTPUT_DIR.mkdir(exist_ok=True)

def main():
    client = VegChangeClient()
    today = datetime.now().strftime("%Y-%m-%d")

    for site in SITES:
        print(f"Analyzing {site['name']}...")

        results = client.analyze(
            site_name=site["name"],
            bbox=site["bbox"],
            periods=["present"],
            indices=["ndvi"]
        )

        # Save results
        output_file = OUTPUT_DIR / f"{site['name']}_{today}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Alert if significant loss detected
        stats = results['results']['statistics']
        # Add alerting logic...

if __name__ == "__main__":
    main()
```

---

## Error Handling

```python
import requests
from requests.exceptions import HTTPError, ConnectionError

try:
    response = requests.post(f"{API_URL}/analysis", json=data)
    response.raise_for_status()
    job = response.json()

except ConnectionError:
    print("Error: Cannot connect to API server")

except HTTPError as e:
    if e.response.status_code == 400:
        error = e.response.json()
        print(f"Validation error: {error['message']}")
        print(f"Details: {error.get('details')}")
    elif e.response.status_code == 404:
        print("Job not found")
    elif e.response.status_code == 500:
        print("Server error - please try again")
    else:
        print(f"HTTP error: {e}")
```

---

## Rate Limiting

The API has rate limits:

- 100 requests per minute
- 10 concurrent analysis jobs
- 1000 exports per day

Handle rate limits:

```python
import time
from requests.exceptions import HTTPError

def make_request_with_retry(method, url, **kwargs):
    for attempt in range(3):
        try:
            response = method(url, **kwargs)
            response.raise_for_status()
            return response
        except HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                wait = int(e.response.headers.get('Retry-After', 60))
                print(f"Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")
```

---

## Exercises

1. **Build a Dashboard**: Create a web dashboard that displays analysis results
2. **Batch Processing**: Write a script to process multiple AOIs from a CSV file
3. **Monitoring System**: Set up automated daily checks with email alerts

---

## Next Steps

- [Deployment Guide](../deployment/local-development.md) - Deploy the API
- [API Reference](../technical/api-reference.md) - Full API documentation
