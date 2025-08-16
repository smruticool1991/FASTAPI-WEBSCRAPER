# 🐳 Docker Deployment Guide

Complete Docker deployment setup for the Website Analysis API with development and production configurations.

## 📁 Files Overview

- `Dockerfile` - Main application container
- `docker-compose.yml` - Development environment
- `docker-compose.prod.yml` - Production environment with monitoring
- `nginx.conf` - Reverse proxy configuration
- `prometheus.yml` - Monitoring configuration
- `docker-run.sh` - Deployment automation script

## 🚀 Quick Start

### Development Environment

```bash
# Start development environment
./docker-run.sh dev

# Or manually
docker-compose up -d
```

**Access Points:**
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Production Environment

```bash
# Set environment variables
export DB_PASSWORD="your_secure_password"
export GRAFANA_PASSWORD="your_grafana_password"

# Start production environment
./docker-run.sh prod

# Or manually
docker-compose -f docker-compose.prod.yml up -d
```

**Access Points:**
- API: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## 📋 Available Commands

```bash
./docker-run.sh dev      # Start development
./docker-run.sh prod     # Start production
./docker-run.sh stop     # Stop all containers
./docker-run.sh logs     # Show container logs
./docker-run.sh status   # Show container status
./docker-run.sh clean    # Remove everything (data will be lost!)
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONCURRENT_REQUESTS` | 10 | Max concurrent HTTP requests |
| `DEFAULT_TIMEOUT` | 15 | Default request timeout (seconds) |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `RATE_LIMIT_MAX_CONCURRENT` | 10 | Rate limiter concurrent requests |
| `RATE_LIMIT_DELAY` | 1.0 | Delay between requests (seconds) |
| `DB_PASSWORD` | - | PostgreSQL password (production) |
| `GRAFANA_PASSWORD` | admin | Grafana admin password |

### Resource Limits

#### Development
- **CPU**: 0.5-2.0 cores
- **Memory**: 512MB-1GB

#### Production  
- **API**: 1.0-4.0 cores, 1GB-2GB RAM
- **Database**: 0.5-2.0 cores, 256MB-1GB RAM
- **Redis**: 0.2-1.0 cores, 128MB-512MB RAM

## 🏗️ Architecture

### Development Stack
```
┌─────────────────┐
│   FastAPI App   │ :8000
└─────────────────┘
```

### Production Stack
```
┌─────────────────┐    ┌─────────────────┐
│      Nginx      │    │   Grafana       │ :3000
│   (Reverse      │    │  (Dashboard)    │
│    Proxy)       │ :80├─────────────────┤
├─────────────────┤    │  Prometheus     │ :9090
│   FastAPI App   │    │ (Monitoring)    │
│                 │:8000├─────────────────┤
├─────────────────┤    │  PostgreSQL     │ :5432
│     Redis       │    │  (Database)     │
│   (Caching)     │:6379└─────────────────┘
└─────────────────┘
```

## 🔒 Security Features

### Application Security
- ✅ Non-root container user
- ✅ SSL certificate verification disabled (for scraping)
- ✅ CORS protection
- ✅ Request rate limiting
- ✅ Input validation and sanitization

### Network Security
- ✅ Nginx reverse proxy
- ✅ Security headers (X-Frame-Options, etc.)
- ✅ Rate limiting at proxy level
- ✅ SSL/TLS ready (certificate required)

### Resource Security
- ✅ Memory and CPU limits
- ✅ Health checks with automatic restart
- ✅ Log rotation
- ✅ Volume isolation

## 📊 Monitoring & Logging

### Health Monitoring
- **Endpoint**: `/health`
- **Interval**: 30s (dev) / 15s (prod)
- **Timeout**: 10s (dev) / 5s (prod)
- **Auto-restart**: On failure

### Metrics (Production)
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Custom metrics**: Request count, response time, error rate

### Logging
- **Format**: JSON structured logs
- **Rotation**: 10MB/file, 3 files (dev) / 50MB/file, 5 files (prod)
- **Location**: `./logs/` directory

## 🗄️ Data Persistence

### Volumes
- `redis_data` - Redis cache and sessions
- `postgres_data` - PostgreSQL database
- `prometheus_data` - Metrics storage
- `grafana_data` - Dashboard configurations
- `./logs` - Application logs
- `./backups` - Database backups

### Backup Strategy
```bash
# Database backup
docker exec website-analyzer-postgres-prod pg_dump -U analyzer website_analyzer > backup.sql

# Volume backup
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

## 🚨 Troubleshooting

### Common Issues

**Container fails to start:**
```bash
# Check logs
docker-compose logs website-analyzer-api

# Check resource usage
docker stats
```

**API not responding:**
```bash
# Check health endpoint
curl http://localhost:8000/health

# Check container status
./docker-run.sh status
```

**Database connection issues:**
```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test database connection
docker exec -it website-analyzer-postgres-prod psql -U analyzer -d website_analyzer
```

**High memory usage:**
```bash
# Monitor resource usage
docker stats --no-stream

# Adjust resource limits in docker-compose files
```

### Performance Tuning

**For high-traffic scenarios:**
1. Increase `MAX_CONCURRENT_REQUESTS` (20-50)
2. Reduce `RATE_LIMIT_DELAY` (0.1-0.5)
3. Scale with multiple container instances
4. Add Redis caching for repeated requests
5. Use nginx load balancing

**Resource optimization:**
```yaml
# In docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Increase for heavy load
      memory: 4G       # Increase for many concurrent requests
```

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy API
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          docker-compose -f docker-compose.prod.yml pull
          docker-compose -f docker-compose.prod.yml up -d
```

### Automated Deployment
```bash
# Create deployment script
#!/bin/bash
git pull origin main
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d --remove-orphans
```

## 📈 Scaling

### Horizontal Scaling
```yaml
# Add to docker-compose.prod.yml
services:
  website-analyzer-api:
    deploy:
      replicas: 3  # Run 3 instances
    
  nginx:
    # Configure load balancing
    upstream api {
      server website-analyzer-api:8000;
    }
```

### Database Scaling
```yaml
# Add read replicas
postgres-read:
  image: postgres:15-alpine
  environment:
    - POSTGRES_MASTER_SERVICE=postgres
  # Configure as read replica
```

This Docker setup provides a complete, production-ready deployment solution for your Website Analysis API! 🚀