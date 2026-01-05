# Production Deployment

Guide to deploying the Vegetation Change Platform in production environments.

## Deployment Options

| Option | Best For | Complexity |
|--------|----------|------------|
| Cloud VM (GCE, EC2) | Single instance | Low |
| Container (Cloud Run, ECS) | Auto-scaling | Medium |
| Kubernetes (GKE, EKS) | Enterprise scale | High |

---

## Pre-Deployment Checklist

- [ ] Earth Engine service account configured
- [ ] API keys and secrets secured
- [ ] SSL certificates obtained
- [ ] Domain name configured
- [ ] Monitoring and logging set up
- [ ] Backup strategy defined

---

## Google Cloud Platform

### Cloud Run (Recommended)

Serverless, auto-scaling container deployment.

#### 1. Build Container

```bash
# Build with Cloud Build
gcloud builds submit --tag gcr.io/PROJECT_ID/vegchange-api

# Or build locally
docker build -t gcr.io/PROJECT_ID/vegchange-api .
docker push gcr.io/PROJECT_ID/vegchange-api
```

#### 2. Deploy to Cloud Run

```bash
gcloud run deploy vegchange-api \
  --image gcr.io/PROJECT_ID/vegchange-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --set-env-vars EE_PROJECT=your-project-id \
  --service-account vegchange@PROJECT_ID.iam.gserviceaccount.com
```

#### 3. Configure Service Account

```bash
# Create service account
gcloud iam service-accounts create vegchange \
  --display-name "Vegetation Change Service"

# Grant Earth Engine access
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member serviceAccount:vegchange@PROJECT_ID.iam.gserviceaccount.com \
  --role roles/earthengine.admin
```

### Compute Engine

For persistent VMs with full control.

#### 1. Create VM

```bash
gcloud compute instances create vegchange-server \
  --machine-type e2-standard-4 \
  --zone us-central1-a \
  --image-family debian-11 \
  --image-project debian-cloud \
  --boot-disk-size 50GB \
  --tags http-server,https-server
```

#### 2. Install Dependencies

```bash
# SSH into VM
gcloud compute ssh vegchange-server

# Install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx

# Clone and install
git clone https://github.com/your-org/vegetation-change-platform.git
cd vegetation-change-platform
python3 -m venv venv
source venv/bin/activate
pip install -e ".[api]"
```

#### 3. Configure Systemd Service

```ini
# /etc/systemd/system/vegchange-api.service
[Unit]
Description=Vegetation Change API
After=network.target

[Service]
Type=simple
User=vegchange
WorkingDirectory=/opt/vegetation-change-platform
Environment=PATH=/opt/vegetation-change-platform/venv/bin
ExecStart=/opt/vegetation-change-platform/venv/bin/uvicorn \
  app.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable vegchange-api
sudo systemctl start vegchange-api
```

#### 4. Configure Nginx

```nginx
# /etc/nginx/sites-available/vegchange
server {
    listen 80;
    server_name api.vegchange.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/vegchange /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. Enable HTTPS

```bash
sudo certbot --nginx -d api.vegchange.example.com
```

---

## AWS Deployment

### Elastic Container Service (ECS)

#### Task Definition

```json
{
  "family": "vegchange-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/vegchange-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "EE_PROJECT",
          "value": "your-project-id"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/vegchange-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Lambda (Serverless)

For lightweight, event-driven deployments using Mangum:

```python
# lambda_handler.py
from mangum import Mangum
from app.api.main import app

handler = Mangum(app)
```

```yaml
# serverless.yml
service: vegchange-api

provider:
  name: aws
  runtime: python3.11
  timeout: 300
  memorySize: 1024

functions:
  api:
    handler: lambda_handler.handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
```

---

## Environment Configuration

### Environment Variables

```bash
# Required
EE_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://app.example.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
MAX_CONCURRENT_JOBS=10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Secrets Management

#### Google Secret Manager

```python
from google.cloud import secretmanager

def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/PROJECT_ID/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Usage
api_key = get_secret("vegchange-api-key")
```

#### AWS Secrets Manager

```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']
```

---

## Monitoring and Logging

### Structured Logging

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

### Health Checks

```python
from fastapi import FastAPI
import ee

app = FastAPI()

@app.get("/health")
async def health_check():
    try:
        # Check Earth Engine connection
        ee.Number(1).getInfo()
        ee_status = "healthy"
    except Exception as e:
        ee_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if ee_status == "healthy" else "degraded",
        "earth_engine": ee_status,
        "version": "1.0.0"
    }

@app.get("/ready")
async def readiness_check():
    # Check all dependencies
    return {"ready": True}
```

### Metrics (Prometheus)

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# Define metrics
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency')
ANALYSIS_JOBS = Counter('analysis_jobs_total', 'Analysis jobs', ['status'])

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Security

### API Authentication

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/analysis", dependencies=[Depends(verify_api_key)])
async def create_analysis(...):
    ...
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/analysis")
@limiter.limit("10/minute")
async def create_analysis(request: Request, ...):
    ...
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

---

## Scaling

### Horizontal Scaling

```bash
# Cloud Run auto-scaling
gcloud run services update vegchange-api \
  --min-instances 1 \
  --max-instances 10

# Kubernetes HPA
kubectl autoscale deployment vegchange-api \
  --min=2 --max=10 --cpu-percent=70
```

### Load Balancer Health Checks

```yaml
# GCP Load Balancer
healthCheck:
  httpHealthCheck:
    port: 8000
    requestPath: /health
  checkIntervalSec: 10
  timeoutSec: 5
  healthyThreshold: 2
  unhealthyThreshold: 3
```

---

## Backup and Recovery

### Database Backup (if using)

```bash
# PostgreSQL backup
pg_dump -h localhost -U vegchange vegchange_db > backup.sql

# Restore
psql -h localhost -U vegchange vegchange_db < backup.sql
```

### Configuration Backup

```bash
# Backup environment and config
tar -czvf config-backup.tar.gz \
  .env \
  config.yaml \
  /etc/nginx/sites-available/vegchange \
  /etc/systemd/system/vegchange-api.service
```

---

## Deployment Checklist

- [ ] Service account configured with minimal permissions
- [ ] Environment variables set securely
- [ ] HTTPS enabled
- [ ] Health checks configured
- [ ] Logging enabled
- [ ] Monitoring dashboards created
- [ ] Alerts configured
- [ ] Backup strategy implemented
- [ ] Runbook documented
- [ ] Load testing completed

---

## Next Steps

- [Docker Deployment](docker.md)
- [Local Development](local-development.md)
