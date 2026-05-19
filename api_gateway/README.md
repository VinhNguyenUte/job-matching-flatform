# README - API Gateway Documentation

## Overview
API Gateway là một reverse proxy sử dụng Nginx để:
- **Định tuyến yêu cầu** đến các backend services (Core Services, AI Processing)
- **Giảm tải** thông qua load balancing
- **Bảo vệ** backend bằng rate limiting và security headers
- **Caching** và nén response
- **Logging** tập trung và monitoring

## Architecture

```
Client
  ↓
[API Gateway - Nginx:80]
  ├─ /api/v1/* → [Core Services:8000]
  │   ├─ POST /api/v1/auth/login
  │   ├─ POST /api/v1/auth/register
  │   ├─ POST /api/v1/cv/upload
  │   ├─ GET /api/v1/cv/{cv_id}
  │   ├─ POST /api/v1/jobs/ingest
  │   ├─ GET /api/v1/jobs/search
  │   └─ GET /api/v1/recommend/match-cv/{cv_id}
  │
  ├─ /api/ai/* → [AI Processing:8001]
  │   ├─ POST /process/cv
  │   ├─ POST /process/job
  │   └─ POST /embed
  │
  └─ /health → Health check
```

## Files

- **Dockerfile** - Container image cho API Gateway
- **nginx.conf** - Main Nginx configuration
- **conf.d/rate_limits.conf** - Rate limiting policies
- **conf.d/security_headers.conf** - Security headers
- **conf.d/backends.conf** - Backend upstream configurations

## Features

### 1. Request Routing
- `/api/v1/*` → Core Services (Port 8000)
- `/api/ai/*` → AI Processing (Port 8001)
- `/health` → Health check endpoint
- `/docs` → API Documentation (Swagger UI)

### 2. Rate Limiting
- **General API**: 10 req/s
- **Auth Endpoints**: 5 req/s
- **Search**: 30 req/s
- **File Upload**: 2 req/min
- **AI Processing**: 20 req/min

### 3. Performance Optimization
- **Gzip compression** cho text/json/images
- **Connection pooling** với upstream servers
- **HTTP/1.1 keep-alive** để reuse connections
- **Buffering** cho large responses
- **Client max body size**: 100MB

### 4. Security Features
- **Security headers** (X-Frame-Options, CSP, etc.)
- **Rate limiting** per IP address
- **Connection limiting**
- **Deny access** to hidden files (.*/)
- **Error page normalization** (không leak backend info)

### 5. High Availability
- **Least connections** load balancing
- **Health check** với fail_timeout=30s
- **Automatic failover** (max_fails=3)
- **Keep-alive connections**

## Docker Compose Integration

```yaml
api_gateway:
  build:
    context: ./api_gateway
    dockerfile: Dockerfile
  container_name: job_platform_api_gateway
  ports:
    - "80:80"
  depends_on:
    - core_services
    - ai_processing
  environment:
    - NGINX_HOST=api_gateway
    - NGINX_PORT=80
```

## Usage

### Local Development
```bash
# Start API Gateway
docker compose up api_gateway

# Test health endpoint
curl http://localhost/health

# Test API endpoint
curl http://localhost/api/v1/jobs/search

# View Nginx logs
docker compose logs -f api_gateway
```

### Production Considerations
1. **HTTPS/SSL**:
   ```nginx
   listen 443 ssl;
   ssl_certificate /etc/nginx/certs/cert.pem;
   ssl_certificate_key /etc/nginx/certs/key.pem;
   ```

2. **Load Balancing** with multiple core_services:
   ```nginx
   upstream core_services {
       server core_services_1:8000;
       server core_services_2:8000;
       server core_services_3:8000;
   }
   ```

3. **Custom Error Pages**:
   ```nginx
   error_page 502 503 504 /error.html;
   location = /error.html { ... }
   ```

4. **Monitoring**:
   - Enable Prometheus metrics module
   - Setup log aggregation (ELK, Loki)
   - Configure alerting (alert on 5xx errors)

## Common Issues

### 1. 502 Bad Gateway
- Kiểm tra backend services đang chạy
- Xem Nginx logs: `docker compose logs api_gateway`

### 2. 429 Too Many Requests
- Rate limiting được active, hãy retry sau vài giây

### 3. Timeouts
- Tăng proxy_*_timeout cho long-running operations
- Check backend service performance

## Monitoring & Logging

```bash
# View access logs
docker compose exec api_gateway tail -f /var/log/nginx/access.log

# View error logs
docker compose exec api_gateway tail -f /var/log/nginx/error.log

# Test configuration
docker compose exec api_gateway nginx -t
```

## Configuration Changes

Để update Nginx configuration:
```bash
# Edit file
nano api_gateway/nginx.conf

# Reload without restart
docker compose exec api_gateway nginx -s reload
```

## References
- Nginx Documentation: https://nginx.org/en/docs/
- Reverse Proxy Best Practices: https://nginx.org/en/docs/http/ngx_http_proxy_module.html
- Rate Limiting: https://nginx.org/en/docs/http/ngx_http_limit_req_module.html
