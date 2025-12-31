# Deployment Guide

## Docker Deployment (Recommended)

### Using Docker Compose

1. **Prepare environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   docker-compose logs -f
   ```

4. **Stop services**
   ```bash
   docker-compose down
   ```

### Individual Services

Start only specific services:

```bash
# Only backend and RabbitMQ
docker-compose up -d rabbitmq backend

# Only worker
docker-compose up -d rabbitmq worker

# Only frontend
docker-compose up -d frontend
```

## Manual Deployment

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run API server
python main.py

# In another terminal, run worker
python worker.py
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Development
npm start

# Production build
npm run build

# Serve build with nginx or serve
npx serve -s build -l 3000
```

### RabbitMQ

Install RabbitMQ locally:

**Ubuntu/Debian:**
```bash
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
```

**macOS:**
```bash
brew install rabbitmq
brew services start rabbitmq
```

**Windows:**
Download and install from: https://www.rabbitmq.com/download.html

## Cloud Deployment

### AWS

1. **EC2 Instance**
   - Launch Ubuntu 20.04 instance
   - Install Docker and Docker Compose
   - Clone repository
   - Configure .env
   - Run docker-compose up -d

2. **Load Balancer**
   - Create Application Load Balancer
   - Configure target groups for frontend and backend
   - Set up health checks

3. **RDS (Optional)**
   - If you add database requirements later

### Google Cloud Platform

1. **Cloud Run**
   - Build container images
   - Deploy to Cloud Run
   - Configure environment variables

2. **Cloud Build**
   - Set up automated builds from GitHub

### Heroku

1. **Install Heroku CLI**
   ```bash
   heroku login
   ```

2. **Create apps**
   ```bash
   heroku create auto-code-backend
   heroku create auto-code-frontend
   ```

3. **Add RabbitMQ addon**
   ```bash
   heroku addons:create cloudamqp:lemur
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

## Kubernetes Deployment

### Create Kubernetes manifests

**namespace.yaml**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: auto-code
```

**rabbitmq-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rabbitmq
  namespace: auto-code
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rabbitmq
  template:
    metadata:
      labels:
        app: rabbitmq
    spec:
      containers:
      - name: rabbitmq
        image: rabbitmq:3-management
        ports:
        - containerPort: 5672
        - containerPort: 15672
```

**backend-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: auto-code
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/auto-code-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: RABBITMQ_HOST
          value: rabbitmq
        envFrom:
        - secretRef:
            name: auto-code-secrets
```

Apply:
```bash
kubectl apply -f namespace.yaml
kubectl apply -f rabbitmq-deployment.yaml
kubectl apply -f backend-deployment.yaml
```

## Environment Variables

Required environment variables:

```bash
# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
GITHUB_OWNER=username
GITHUB_REPO=repository

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# API
API_HOST=0.0.0.0
API_PORT=8000

# Claude AI
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

## SSL/TLS Configuration

### Using Let's Encrypt with Nginx

1. **Install Certbot**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   ```

2. **Get certificate**
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Auto-renewal**
   ```bash
   sudo systemctl enable certbot.timer
   ```

## Monitoring

### Health Checks

- Backend: `GET /health`
- RabbitMQ: http://localhost:15672

### Logging

View logs:
```bash
# Docker Compose
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f rabbitmq

# Kubernetes
kubectl logs -f deployment/backend -n auto-code
```

### Metrics

Integrate with:
- Prometheus
- Grafana
- Datadog
- New Relic

## Scaling

### Horizontal Scaling

Scale workers:
```bash
docker-compose up -d --scale worker=5
```

Scale in Kubernetes:
```bash
kubectl scale deployment/worker --replicas=5 -n auto-code
```

### Vertical Scaling

Increase resource limits in docker-compose.yml:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Backup and Recovery

### Backup RabbitMQ

```bash
# Export definitions
curl -u guest:guest http://localhost:15672/api/definitions > rabbitmq-backup.json

# Import
curl -u guest:guest -H "Content-Type: application/json" \
  -X POST http://localhost:15672/api/definitions \
  -d @rabbitmq-backup.json
```

## Troubleshooting

### Service won't start
```bash
docker-compose ps
docker-compose logs service-name
```

### Connection refused
- Check firewall rules
- Verify port mappings
- Check service health

### Out of memory
- Increase container limits
- Scale horizontally
- Optimize code

## Security Checklist

- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/TLS
- [ ] Implement authentication
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Use strong passwords
- [ ] Implement rate limiting
