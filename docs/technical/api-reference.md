# API Reference

Complete reference for the Vegetation Change Intelligence Platform REST API.

## Overview

The API provides RESTful endpoints for vegetation change analysis. It is built with FastAPI and provides automatic OpenAPI documentation.

**Base URL**: `http://localhost:8000` (development)

**Interactive Docs**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Authentication

Currently, the API does not require authentication. Future versions will support:
- API key authentication
- OAuth2 integration

## Endpoints

### Health Check

#### GET /health

Check API health and Earth Engine status.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "earth_engine": true
}
```

---

### Analysis

#### POST /analysis

Create a new vegetation change analysis job.

**Request Body**:
```json
{
  "site_name": "My Analysis",
  "bbox": {
    "min_lon": -62.5,
    "min_lat": -4.0,
    "max_lon": -62.0,
    "max_lat": -3.5
  },
  "periods": ["1990s", "present"],
  "indices": ["ndvi"],
  "reference_period": "1990s",
  "buffer_distance": 500.0,
  "cloud_threshold": 20.0,
  "export_to_drive": false
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| site_name | string | No | Name for the site (default: "Analysis Site") |
| bbox | BoundingBox | * | Bounding box coordinates |
| aoi_geojson | GeoJSON | * | GeoJSON geometry |
| periods | array | No | Temporal periods (default: ["1990s", "present"]) |
| indices | array | No | Spectral indices (default: ["ndvi"]) |
| reference_period | string | No | Baseline period (default: "1990s") |
| buffer_distance | float | No | Buffer in meters (default: 500) |
| cloud_threshold | float | No | Max cloud cover % (default: 20) |
| export_to_drive | bool | No | Export to Drive (default: false) |

*Either `bbox` or `aoi_geojson` is required, but not both.

**Response** (201 Created):
```json
{
  "job_id": "abc12345",
  "status": "pending",
  "message": "Analysis job created successfully",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

#### GET /analysis/{job_id}

Get status and results of an analysis job.

**Path Parameters**:
- `job_id` (string): Job identifier

**Response** (200 OK):
```json
{
  "job_id": "abc12345",
  "status": "completed",
  "progress": 1.0,
  "current_step": "Complete",
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:05Z",
  "completed_at": "2024-01-15T10:32:15Z",
  "error": null,
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
    }
  }
}
```

**Status Values**:
- `pending`: Job created, not started
- `running`: Analysis in progress
- `completed`: Successfully finished
- `failed`: Error occurred
- `cancelled`: User cancelled

---

#### DELETE /analysis/{job_id}

Cancel a pending analysis job.

**Path Parameters**:
- `job_id` (string): Job identifier

**Response** (200 OK):
```json
{
  "message": "Job abc12345 cancelled"
}
```

**Errors**:
- 404: Job not found
- 409: Cannot cancel running job

---

#### GET /analysis

List analysis jobs.

**Query Parameters**:
- `status` (optional): Filter by status
- `limit` (optional): Max jobs to return (default: 50, max: 100)

**Response** (200 OK):
```json
{
  "jobs": [
    {
      "job_id": "abc12345",
      "status": "completed",
      "progress": 1.0,
      "current_step": "Complete",
      "created_at": "2024-01-15T10:30:00Z",
      ...
    }
  ],
  "total": 1
}
```

---

#### POST /analysis/preview

Generate a preview tile URL for quick visualization.

**Request Body**:
```json
{
  "bbox": {
    "min_lon": -62.5,
    "min_lat": -4.0,
    "max_lon": -62.0,
    "max_lat": -3.5
  },
  "period": "present",
  "index": "ndvi"
}
```

**Response** (200 OK):
```json
{
  "tile_url": "https://earthengine.googleapis.com/v1alpha/...",
  "center": {
    "lat": -3.75,
    "lon": -62.25
  },
  "bounds": {
    "min_lat": -4.0,
    "min_lon": -62.5,
    "max_lat": -3.5,
    "max_lon": -62.0
  },
  "vis_params": {
    "min": -0.2,
    "max": 0.8,
    "palette": ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"]
  }
}
```

---

### Metadata

#### GET /periods

List available temporal periods.

**Response** (200 OK):
```json
{
  "periods": [
    {
      "name": "1990s",
      "start": "1985-01-01",
      "end": "1999-12-31",
      "sensors": ["LANDSAT/LT05/C02/T1_L2"],
      "description": "Pre-2000 baseline (Landsat 5 TM)"
    },
    {
      "name": "2000s",
      "start": "2000-01-01",
      "end": "2012-12-31",
      "sensors": ["LANDSAT/LE07/C02/T1_L2", "LANDSAT/LT05/C02/T1_L2"],
      "description": "Early 2000s (Landsat 5/7)"
    },
    ...
  ]
}
```

---

#### GET /indices

List available spectral indices.

**Response** (200 OK):
```json
{
  "indices": [
    {
      "name": "ndvi",
      "full_name": "Normalized Difference Vegetation Index",
      "description": "Measures vegetation greenness and health",
      "formula": "(NIR - Red) / (NIR + Red)",
      "range": {"min": -1.0, "max": 1.0}
    },
    {
      "name": "nbr",
      "full_name": "Normalized Burn Ratio",
      "description": "Detects burned areas and fire severity",
      "formula": "(NIR - SWIR2) / (NIR + SWIR2)",
      "range": {"min": -1.0, "max": 1.0}
    },
    ...
  ]
}
```

---

## Data Models

### BoundingBox

```json
{
  "min_lon": -180.0,  // Minimum longitude (-180 to 180)
  "min_lat": -90.0,   // Minimum latitude (-90 to 90)
  "max_lon": 180.0,   // Maximum longitude
  "max_lat": 90.0     // Maximum latitude
}
```

### GeoJSONGeometry

```json
{
  "type": "Polygon",  // or "MultiPolygon"
  "coordinates": [
    [
      [-62.5, -4.0],
      [-62.0, -4.0],
      [-62.0, -3.5],
      [-62.5, -3.5],
      [-62.5, -4.0]
    ]
  ]
}
```

### TemporalPeriod (enum)

- `1990s`
- `2000s`
- `2010s`
- `present`

### SpectralIndexType (enum)

- `ndvi`
- `nbr`
- `ndwi`
- `evi`
- `ndmi`

### AnalysisStatus (enum)

- `pending`
- `running`
- `completed`
- `failed`
- `cancelled`

---

## Error Handling

### Error Response Format

```json
{
  "error": "ValidationError",
  "message": "Invalid request parameters",
  "details": {
    "field": "periods",
    "issue": "Minimum 2 periods required"
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Operation not allowed |
| 500 | Internal Server Error |

---

## Rate Limits

Current limits (subject to change):
- 100 requests per minute
- 10 concurrent analysis jobs
- 1000 exports per day (Earth Engine limit)

---

## Examples

### Python (requests)

```python
import requests

# Create analysis
response = requests.post(
    "http://localhost:8000/analysis",
    json={
        "site_name": "Amazon Test",
        "bbox": {
            "min_lon": -62.5,
            "min_lat": -4.0,
            "max_lon": -62.0,
            "max_lat": -3.5
        },
        "periods": ["1990s", "present"],
        "indices": ["ndvi"]
    }
)
job = response.json()
print(f"Job ID: {job['job_id']}")

# Poll for results
import time
while True:
    status = requests.get(f"http://localhost:8000/analysis/{job['job_id']}").json()
    if status['status'] in ['completed', 'failed']:
        break
    print(f"Progress: {status['progress']:.0%}")
    time.sleep(5)

print(f"Results: {status['results']}")
```

### JavaScript (fetch)

```javascript
// Create analysis
const response = await fetch('http://localhost:8000/analysis', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    site_name: 'Amazon Test',
    bbox: {
      min_lon: -62.5,
      min_lat: -4.0,
      max_lon: -62.0,
      max_lat: -3.5
    },
    periods: ['1990s', 'present'],
    indices: ['ndvi']
  })
});

const job = await response.json();
console.log(`Job ID: ${job.job_id}`);
```

### cURL

```bash
# Create analysis
curl -X POST http://localhost:8000/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "Amazon Test",
    "bbox": {
      "min_lon": -62.5,
      "min_lat": -4.0,
      "max_lon": -62.0,
      "max_lat": -3.5
    }
  }'

# Check status
curl http://localhost:8000/analysis/abc12345

# List jobs
curl "http://localhost:8000/analysis?status=completed&limit=10"
```

---

## WebSocket Support (Future)

Future versions will support WebSocket for real-time progress updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/analysis/abc12345');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.progress}%`);
};
```
