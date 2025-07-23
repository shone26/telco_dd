# Docker Deployment Guide - Telecom Application

This guide provides comprehensive instructions for deploying the Telecom Application using Docker and Docker Compose.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- At least 10GB disk space

## 🏗️ Architecture Overview

The dockerized application consists of the following services:

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Nginx    │  │  Frontend   │  │   Backend   │        │
│  │   (Proxy)   │  │  (Node.js)  │  │  (Python)   │        │
│  │   Port 80   │  │  Port 3002  │  │  Port 5001  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                 │                 │              │
│         └─────────────────┼─────────────────┘              │
│                           │                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ PostgreSQL  │  │    Redis    │  │    Tests    │        │
│  │ Port 5432   │  │  Port 6379  │  │ (On-demand) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd telecom_application

# Copy environment configuration
cp .env.example .env

# Edit environment variables (optional)
nano .env
```

### 2. Build and Start Services

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### 3. Access the Application

- **Frontend**: http://localhost:3002
- **Backend API**: http://localhost:5001/api
- **Nginx Proxy**: http://localhost:80
- **Database**: localhost:5432

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Database
POSTGRES_DB=telecom_db
POSTGRES_USER=telecom_user
POSTGRES_PASSWORD=telecom_password

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key
SECRET_KEY=your-flask-secret-key

# URLs
API_BASE_URL=http://backend:5001/api
FRONTEND_URL=http://frontend:3002
```

### Service Configuration

Each service can be configured through environment variables:

#### Backend Service
```yaml
environment:
  - FLASK_ENV=production
  - DATABASE_URL=postgresql://telecom_user:telecom_password@database:5432/telecom_db
  - JWT_SECRET_KEY=your-super-secret-jwt-key
```

#### Frontend Service
```yaml
environment:
  - NODE_ENV=production
  - API_BASE_URL=http://backend:5001/api
  - PORT=3002
```

## 📦 Service Details

### Database Service (PostgreSQL)
- **Image**: postgres:15-alpine
- **Port**: 5432
- **Volume**: postgres_data
- **Initialization**: database/init.sql

### Backend Service (Python/Flask)
- **Build**: backend/Dockerfile
- **Port**: 5001
- **Dependencies**: Database
- **Health Check**: /api/health/

### Frontend Service (Node.js/Express)
- **Build**: frontend/Dockerfile
- **Port**: 3002
- **Dependencies**: Backend
- **Health Check**: /

### Nginx Service (Reverse Proxy)
- **Image**: nginx:alpine
- **Ports**: 80, 443
- **Configuration**: nginx/nginx.conf
- **Features**: Load balancing, SSL termination, rate limiting

### Redis Service (Caching)
- **Image**: redis:7-alpine
- **Port**: 6379
- **Volume**: redis_data

### Test Runner Service
- **Build**: tests/Dockerfile
- **Profile**: testing
- **Dependencies**: Backend, Frontend

## 🛠️ Development Workflow

### Development Mode

```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or use development profile
docker-compose --profile development up
```

### Running Tests

```bash
# Run all tests
docker-compose --profile testing up test_runner

# Run specific test types
docker-compose run --rm test_runner python run_all_tests.py --tests unit integration

# Run tests with custom backend URL
docker-compose run --rm test_runner python run_all_tests.py --backend-url http://backend:5001
```

### Database Operations

```bash
# Access database
docker-compose exec database psql -U telecom_user -d telecom_db

# Backup database
docker-compose exec database pg_dump -U telecom_user telecom_db > backup.sql

# Restore database
docker-compose exec -T database psql -U telecom_user telecom_db < backup.sql

# Reset database
docker-compose down -v
docker-compose up database
```

### Logs and Monitoring

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f

# View health status
docker-compose ps
```

## 🔒 Production Deployment

### Security Considerations

1. **Environment Variables**
   ```bash
   # Use strong passwords
   POSTGRES_PASSWORD=<strong-random-password>
   JWT_SECRET_KEY=<strong-random-key>
   SECRET_KEY=<strong-random-key>
   ```

2. **SSL/TLS Configuration**
   ```bash
   # Generate SSL certificates
   mkdir -p nginx/ssl
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/ssl/key.pem \
     -out nginx/ssl/cert.pem
   ```

3. **Network Security**
   ```yaml
   # Limit exposed ports
   services:
     database:
       ports: []  # Remove external port exposure
     redis:
       ports: []  # Remove external port exposure
   ```

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    environment:
      - FLASK_ENV=production
      - DEBUG=false
    restart: always

  frontend:
    environment:
      - NODE_ENV=production
    restart: always

  nginx:
    ports:
      - "443:443"
    volumes:
      - ./nginx/ssl:/etc/nginx/ssl:ro
    restart: always

  database:
    ports: []  # Remove external access
    restart: always

  redis:
    ports: []  # Remove external access
    restart: always
```

Deploy with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Scaling Services

```bash
# Scale backend service
docker-compose up --scale backend=3

# Scale with load balancer
docker-compose up --scale backend=3 --scale frontend=2
```

## 📊 Monitoring and Health Checks

### Health Check Endpoints

- **Backend**: http://localhost:5001/api/health/
- **Frontend**: http://localhost:3002/
- **Nginx**: http://localhost:80/health
- **Database**: Built-in PostgreSQL health check
- **Redis**: Built-in Redis health check

### Monitoring Commands

```bash
# Check service health
docker-compose ps

# View resource usage
docker stats

# Check service dependencies
docker-compose config

# Validate compose file
docker-compose config --quiet
```

## 🐛 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -tulpn | grep :5000
   
   # Change ports in docker-compose.yml
   ports:
     - "5001:5000"  # Use different external port
   ```

2. **Database Connection Issues**
   ```bash
   # Check database logs
   docker-compose logs database
   
   # Test connection
   docker-compose exec backend python -c "
   import psycopg2
   conn = psycopg2.connect('postgresql://telecom_user:telecom_password@database:5432/telecom_db')
   print('Connected successfully')
   "
   ```

3. **Build Issues**
   ```bash
   # Clean build
   docker-compose build --no-cache
   
   # Remove all containers and volumes
   docker-compose down -v --remove-orphans
   
   # Prune Docker system
   docker system prune -a
   ```

4. **Memory Issues**
   ```bash
   # Check memory usage
   docker stats
   
   # Increase memory limits
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 1G
   ```

### Debug Mode

```bash
# Run with debug output
docker-compose --verbose up

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend sh

# Run commands in container
docker-compose exec backend python -c "print('Debug info')"
```

## 🔄 Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec database pg_dump -U telecom_user telecom_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR
docker-compose exec -T database pg_dump -U telecom_user telecom_db > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v telecom_application_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v telecom_application_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## 📈 Performance Optimization

### Resource Limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  frontend:
    deploy:
      resources:
        limits:
          cpus: '0.3'
          memory: 256M
```

### Caching

```yaml
# Enable Redis caching
services:
  backend:
    environment:
      - REDIS_URL=redis://redis:6379/0
      - CACHE_ENABLED=true
```

### Database Optimization

```sql
-- Add to database/init.sql
-- Optimize PostgreSQL settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
```

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to server
        run: |
          docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
          
      - name: Run health checks
        run: |
          docker-compose exec -T backend curl -f http://localhost:5001/api/health/
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Nginx Docker Hub](https://hub.docker.com/_/nginx)
- [Redis Docker Hub](https://hub.docker.com/_/redis)

---

**Happy Dockerizing! 🐳**
