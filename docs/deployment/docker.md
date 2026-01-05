# Docker Deployment

Guide to containerizing and deploying the platform with Docker.

## Prerequisites

- Docker installed (20.10+)
- Docker Compose (2.0+)
- Earth Engine service account credentials

---

## Quick Start

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Dockerfile

### API Service

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Set work directory
WORKDIR /app

# Copy requirements first (for caching)
COPY pyproject.toml setup.py ./
COPY veg_change_engine/ ./veg_change_engine/
COPY engine/ ./engine/
COPY services/ ./services/
COPY app/ ./app/

# Install dependencies
RUN pip install -e ".[api]"

# Copy remaining files
COPY . .

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dashboard Service

```dockerfile
# Dockerfile.dashboard
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY pyproject.toml setup.py ./
COPY veg_change_engine/ ./veg_change_engine/
COPY engine/ ./engine/
COPY services/ ./services/
COPY app/ ./app/

RUN pip install -e ".[app]"

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health

CMD ["streamlit", "run", "app/Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## Docker Compose

### Development Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - EE_PROJECT=${EE_PROJECT}
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json
    volumes:
      - ./credentials:/app/credentials:ro
      - ./output:/app/output
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    ports:
      - "8501:8501"
    environment:
      - EE_PROJECT=${EE_PROJECT}
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json
    volumes:
      - ./credentials:/app/credentials:ro
    depends_on:
      - api
    restart: unless-stopped

  # Optional: nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - api
      - dashboard
    restart: unless-stopped
```

### Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: gcr.io/${GCP_PROJECT}/vegchange-api:${VERSION}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      - EE_PROJECT=${EE_PROJECT}
      - API_WORKERS=4
      - LOG_LEVEL=INFO
    secrets:
      - google_credentials
    networks:
      - vegchange-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  dashboard:
    image: gcr.io/${GCP_PROJECT}/vegchange-dashboard:${VERSION}
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 2G
    environment:
      - EE_PROJECT=${EE_PROJECT}
    secrets:
      - google_credentials
    networks:
      - vegchange-net

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - certbot-certs:/etc/letsencrypt
      - certbot-www:/var/www/certbot
    depends_on:
      - api
      - dashboard
    networks:
      - vegchange-net

secrets:
  google_credentials:
    file: ./credentials/service-account.json

networks:
  vegchange-net:
    driver: overlay

volumes:
  certbot-certs:
  certbot-www:
```

---

## Nginx Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    upstream dashboard {
        server dashboard:8501;
    }

    server {
        listen 80;
        server_name api.vegchange.example.com;

        location / {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }
    }

    server {
        listen 80;
        server_name app.vegchange.example.com;

        location / {
            proxy_pass http://dashboard;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 86400;
        }

        location /_stcore/stream {
            proxy_pass http://dashboard/_stcore/stream;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400;
        }
    }
}
```

---

## Building Images

### Local Build

```bash
# Build API image
docker build -t vegchange-api:latest .

# Build dashboard image
docker build -t vegchange-dashboard:latest -f Dockerfile.dashboard .

# Build with specific version
docker build -t vegchange-api:1.0.0 .
```

### Multi-Stage Build (Optimized)

```dockerfile
# Dockerfile.optimized
# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgdal-dev

COPY pyproject.toml setup.py ./
COPY veg_change_engine/ ./veg_change_engine/
COPY engine/ ./engine/
COPY services/ ./services/
COPY app/ ./app/

RUN pip install --user -e ".[api]"

# Production stage
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal30 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /app /app

WORKDIR /app

RUN chown -R appuser:appuser /app
USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Environment Configuration

### .env File

```bash
# .env
# Earth Engine
EE_PROJECT=your-gcp-project-id

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Dashboard Settings
STREAMLIT_SERVER_PORT=8501

# Logging
LOG_LEVEL=INFO

# Version
VERSION=1.0.0
GCP_PROJECT=your-gcp-project
```

### Docker Secrets

```bash
# Create secret from file
docker secret create google_credentials credentials/service-account.json

# List secrets
docker secret ls

# Use in service
docker service create \
  --name vegchange-api \
  --secret google_credentials \
  vegchange-api:latest
```

---

## Common Commands

### Development

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Restart service
docker-compose restart api

# Rebuild after code changes
docker-compose up -d --build

# Shell into container
docker-compose exec api bash

# Run tests in container
docker-compose exec api pytest tests/

# Stop and remove
docker-compose down

# Stop and remove with volumes
docker-compose down -v
```

### Production

```bash
# Deploy stack
docker stack deploy -c docker-compose.prod.yml vegchange

# List services
docker service ls

# Scale service
docker service scale vegchange_api=5

# Update service
docker service update --image vegchange-api:1.1.0 vegchange_api

# View service logs
docker service logs vegchange_api

# Remove stack
docker stack rm vegchange
```

---

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/docker.yml
name: Docker Build and Deploy

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  REGISTRY: gcr.io
  PROJECT_ID: your-gcp-project

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to GCR
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: _json_key
          password: ${{ secrets.GCR_JSON_KEY }}

      - name: Build and push API
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/vegchange-api:latest
            ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/vegchange-api:${{ github.sha }}

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: vegchange-api
          image: ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/vegchange-api:${{ github.sha }}
          region: us-central1
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs vegchange-api

# Check container status
docker inspect vegchange-api

# Verify image
docker run -it vegchange-api:latest /bin/bash
```

### Memory Issues

```bash
# Check memory usage
docker stats

# Increase memory limit
docker run -m 4g vegchange-api:latest
```

### Network Issues

```bash
# List networks
docker network ls

# Inspect network
docker network inspect vegchange_default

# Test connectivity
docker exec vegchange-api curl http://dashboard:8501
```

### Credentials Issues

```bash
# Verify credentials mount
docker exec vegchange-api ls -la /app/credentials/

# Test Earth Engine
docker exec vegchange-api python -c "import ee; ee.Initialize(); print('OK')"
```

---

## Best Practices

1. **Use multi-stage builds** to reduce image size
2. **Run as non-root user** for security
3. **Pin dependency versions** in requirements
4. **Use health checks** for container orchestration
5. **Keep secrets out of images** - use environment variables or secrets
6. **Tag images with versions** - avoid using `latest` in production
7. **Use `.dockerignore`** to exclude unnecessary files

### .dockerignore

```
# .dockerignore
.git
.gitignore
__pycache__
*.pyc
*.pyo
.pytest_cache
.mypy_cache
.env
*.md
docs/
tests/
notebooks/
.vscode/
.idea/
```

---

## Next Steps

- [Production Deployment](production.md)
- [Local Development](local-development.md)
