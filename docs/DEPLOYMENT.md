# Deployment Guide

Complete guide for deploying Ultra Doc-Intelligence to various platforms.

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Production Checklist](#production-checklist)

---

## Local Development

### Quick Start

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY='your-key'
python app.py

# Frontend (new terminal)
cd frontend
python -m http.server 3000
```

### Development Tips

**Hot Reload:**
```bash
# Backend with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Environment Variables:**
```bash
# Create .env file
ANTHROPIC_API_KEY=sk-ant-xxx
DEBUG=True
LOG_LEVEL=INFO
```

**VS Code Setup:**
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

---

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Set environment variable
export ANTHROPIC_API_KEY='your-key'

# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Manual Docker Build

**Backend:**
```bash
cd backend
docker build -t ultra-doc-backend .
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY='your-key' \
  ultra-doc-backend
```

**Frontend:**
```bash
cd frontend
docker run -p 3000:80 \
  -v $(pwd):/usr/share/nginx/html \
  nginx:alpine
```

### Docker Production Configuration

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - uploads:/app/uploads
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./frontend:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - backend

  postgres:
    image: postgres:15
    restart: always
    environment:
      - POSTGRES_DB=ultradoc
      - POSTGRES_USER=ultradoc
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  uploads:
  postgres_data:
```

---

## Cloud Deployment

### AWS Deployment

#### Option 1: AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 ultra-doc-intelligence

# Create environment
eb create ultra-doc-prod

# Set environment variables
eb setenv ANTHROPIC_API_KEY=your-key

# Deploy
eb deploy

# Open in browser
eb open
```

**Dockerrun.aws.json:**
```json
{
  "AWSEBDockerrunVersion": 2,
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-ecr-repo/ultra-doc-backend:latest",
      "essential": true,
      "memory": 512,
      "portMappings": [
        {
          "hostPort": 8000,
          "containerPort": 8000
        }
      ],
      "environment": [
        {
          "name": "ANTHROPIC_API_KEY",
          "value": "your-key"
        }
      ]
    }
  ]
}
```

#### Option 2: AWS ECS (Fargate)

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ECR_URL

docker build -t ultra-doc-backend ./backend
docker tag ultra-doc-backend:latest YOUR_ECR_URL/ultra-doc-backend:latest
docker push YOUR_ECR_URL/ultra-doc-backend:latest

# Create ECS task definition and service (via AWS Console or Terraform)
```

**ECS Task Definition:**
```json
{
  "family": "ultra-doc-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "YOUR_ECR_URL/ultra-doc-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ANTHROPIC_API_KEY",
          "value": "your-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ultra-doc-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform

#### Cloud Run Deployment

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/ultra-doc-backend ./backend

# Deploy to Cloud Run
gcloud run deploy ultra-doc-backend \
  --image gcr.io/PROJECT_ID/ultra-doc-backend \
  --platform managed \
  --region us-central1 \
  --set-env-vars ANTHROPIC_API_KEY=your-key \
  --allow-unauthenticated
```

**cloudbuild.yaml:**
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/ultra-doc-backend', './backend']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/ultra-doc-backend']
  
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'ultra-doc-backend'
      - '--image'
      - 'gcr.io/$PROJECT_ID/ultra-doc-backend'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
```

### Heroku Deployment

```bash
# Install Heroku CLI
# Create app
heroku create ultra-doc-intelligence

# Set environment variables
heroku config:set ANTHROPIC_API_KEY=your-key

# Deploy
git push heroku main

# Open
heroku open
```

**Procfile:**
```
web: cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT
```

**runtime.txt:**
```
python-3.11.0
```

### DigitalOcean App Platform

**app.yaml:**
```yaml
name: ultra-doc-intelligence
region: nyc

services:
  - name: backend
    dockerfile_path: backend/Dockerfile
    source_dir: /
    github:
      repo: your-username/ultra-doc-intelligence
      branch: main
      deploy_on_push: true
    envs:
      - key: ANTHROPIC_API_KEY
        value: ${ANTHROPIC_API_KEY}
    http_port: 8000
    instance_count: 1
    instance_size_slug: basic-xxs
    routes:
      - path: /api

  - name: frontend
    build_command: echo "No build needed"
    run_command: python -m http.server 3000
    source_dir: frontend
    http_port: 3000
    routes:
      - path: /
```

---

## Production Checklist

### Security

- [ ] **Environment Variables**
  - Never commit API keys to Git
  - Use secrets management (AWS Secrets Manager, etc.)
  
- [ ] **HTTPS/SSL**
  - Enable SSL certificates (Let's Encrypt)
  - Force HTTPS redirect
  
- [ ] **Authentication**
  - Implement JWT-based auth
  - Add user management
  
- [ ] **Rate Limiting**
  - Add per-user rate limits
  - Prevent API abuse
  
- [ ] **Input Validation**
  - File size limits (e.g., 10MB max)
  - File type validation
  - Sanitize inputs
  
- [ ] **CORS**
  - Restrict allowed origins
  - No wildcard in production

### Database

- [ ] **Migration to PostgreSQL**
  - Replace in-memory store
  - Add pgvector extension
  - Create proper indexes
  
- [ ] **Backups**
  - Daily automated backups
  - Point-in-time recovery
  - Test restore process
  
- [ ] **Connection Pooling**
  - Use connection pooler (PgBouncer)
  - Prevent connection exhaustion

### Performance

- [ ] **Caching**
  - Redis for response caching
  - Cache embeddings
  - CDN for frontend assets
  
- [ ] **Load Balancing**
  - Multiple backend instances
  - Health checks
  - Auto-scaling
  
- [ ] **Monitoring**
  - Application monitoring (Datadog, New Relic)
  - Error tracking (Sentry)
  - Log aggregation (ELK, CloudWatch)
  
- [ ] **Optimization**
  - Enable gzip compression
  - Minify frontend assets
  - Optimize Docker images (multi-stage builds)

### Reliability

- [ ] **Health Checks**
  - `/health` endpoint returns 200
  - Database connectivity check
  - Dependency health checks
  
- [ ] **Graceful Degradation**
  - Fallback when LLM unavailable
  - Queue for heavy operations
  - Circuit breakers
  
- [ ] **Error Handling**
  - Comprehensive error logging
  - User-friendly error messages
  - Automatic retries for transient failures

### Compliance

- [ ] **Data Privacy**
  - GDPR compliance
  - Data retention policies
  - User data deletion
  
- [ ] **Audit Logging**
  - Log all document uploads
  - Log all API calls
  - Immutable audit trail
  
- [ ] **Terms of Service**
  - Acceptable use policy
  - Privacy policy
  - Data processing agreement

---

## Nginx Configuration

**nginx.conf:**
```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    
    # Frontend
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ =404;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        
        # File upload size
        client_max_body_size 10M;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

---

## Environment Variables Reference

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxx

# Optional
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
MAX_FILE_SIZE=10485760  # 10MB in bytes
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=https://xxx@sentry.io/xxx

# Production
SECRET_KEY=your-secret-key-for-jwt
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## Monitoring & Alerts

### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    checks = {
        "api": "healthy",
        "anthropic": client is not None,
        "database": await check_database(),
        "redis": await check_redis(),
        "disk_space": check_disk_space()
    }
    
    status = "healthy" if all(checks.values()) else "unhealthy"
    status_code = 200 if status == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content={"status": status, "checks": checks}
    )
```

### Sample Alerts (PagerDuty/Datadog)

```yaml
# High error rate
- name: High Error Rate
  condition: error_rate > 5%
  window: 5 minutes
  action: page_on_call

# Low confidence rate
- name: Low Confidence Answers
  condition: avg(confidence) < 0.5
  window: 15 minutes
  action: notify_team

# API latency
- name: High Latency
  condition: p95_latency > 5s
  window: 10 minutes
  action: page_on_call
```

---

## Rollback Procedure

```bash
# Docker
docker-compose down
docker-compose up -d --build <previous-version>

# Kubernetes
kubectl rollout undo deployment/ultra-doc-backend

# AWS ECS
aws ecs update-service \
  --cluster ultra-doc-cluster \
  --service ultra-doc-service \
  --task-definition ultra-doc-backend:<previous-revision>

# Heroku
heroku releases:rollback v<previous-version>
```

---

## Cost Optimization

### Anthropic API Costs

**Estimated Usage:**
- Question answering: ~500 tokens/request
- Extraction: ~1500 tokens/request
- Claude Sonnet 4: $3/MTok input, $15/MTok output

**Monthly estimate (1000 users, 10 requests/day):**
- Questions: 1000 * 10 * 30 * 500 * $3/1M = $450/mo
- Extractions: 1000 * 2 * 30 * 1500 * $15/1M = $900/mo
- **Total: ~$1350/mo**

**Optimization:**
- Cache frequent questions
- Use Haiku for simple queries (70% cheaper)
- Batch extraction requests

### Infrastructure Costs

**AWS (example):**
- EC2 t3.small (backend): $15/mo
- RDS PostgreSQL db.t3.micro: $15/mo
- S3 storage: $1/mo
- CloudFront CDN: $5/mo
- **Total: ~$36/mo**

**Total Monthly Cost: ~$1400/mo**

---

## Performance Benchmarks

```bash
# Load testing with Locust
pip install locust

# locustfile.py
from locust import HttpUser, task, between

class DocumentUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def ask_question(self):
        self.client.post("/ask", json={
            "doc_id": "doc_test",
            "question": "What is the rate?"
        })

# Run
locust -f locustfile.py --host=http://localhost:8000
```

**Target Metrics:**
- Upload: < 3s for 10-page PDF
- Question: < 2s with LLM
- Extraction: < 3s
- P95 latency: < 5s
- Throughput: 100 req/sec

---

**Ready to deploy!** Choose your platform and follow the steps above.