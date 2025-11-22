# 🚀 Production Deployment Guide

Complete checklist for deploying the Video Downloader to production with security, scaling, and stability.

## 📋 Pre-Deployment Checklist

### ✅ 1. Prepare Production Build

- [ ] Set `DEBUG=false` in environment
- [ ] Remove all `print()` statements
- [ ] Disable `reload=True` in uvicorn
- [ ] Build frontend: `npm run build`
- [ ] Test production build locally
- [ ] Review all environment variables

### ✅ 2. Docker Production Setup

```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check health
docker-compose -f docker-compose.prod.yml ps
```

**Production Command:**
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --timeout 300
```

### ✅ 3. Reverse Proxy & HTTPS

**NGINX Configuration:**
- [x] HTTP → HTTPS redirect
- [x] SSL/TLS certificates (Let's Encrypt)
- [x] Gzip compression
- [x] Request size limits (500MB)
- [x] Caching headers
- [x] Security headers

**Setup SSL:**
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### ✅ 4. Security & Anti-Bot Controls

#### A. Rate Limiting (NGINX)
```nginx
# API endpoints: 10 requests/second
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# Downloads: 3 requests/minute
limit_req_zone $binary_remote_addr zone=download_limit:10m rate=3r/m;
```

#### B. User-Agent Validation
```nginx
# Block bots
if ($http_user_agent ~* (bot|crawler|spider|scraper|curl|wget)) {
    return 403;
}
```

#### C. Token-Based Downloads
Add to backend:
```python
from itsdangerous import URLSafeTimedSerializer

def generate_download_token(filename: str, expires_in: int = 3600):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(filename, salt='download-salt')

def verify_download_token(token: str, max_age: int = 3600):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        filename = serializer.loads(token, salt='download-salt', max_age=max_age)
        return filename
    except:
        return None
```

#### D. Cloudflare Protection
1. Add site to Cloudflare
2. Enable "Under Attack" mode if needed
3. Set up WAF rules
4. Enable Bot Fight Mode

### ✅ 5. Logging & Monitoring

**Log Files:**
```
/app/logs/access.log    # HTTP access logs
/app/logs/error.log     # Application errors
/app/logs/download.log  # Download tracking
```

**Monitoring Stack:**
```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=your_password
```

**Track:**
- Downloads per user/IP
- Failed extractions
- CPU/RAM usage
- Disk space
- Request patterns

### ✅ 6. Long-Running Stability

#### Auto-Cleanup Cron
```bash
# Add to crontab
0 */6 * * * docker exec video-downloader-prod python -c "from app.livestream import LivestreamManager; LivestreamManager().cleanup_old_recordings(1)"

# Or use systemd timer
```

#### Split Large Files
```python
# In livestream.py, add file splitting
async def split_large_file(input_file: str, segment_time: int = 1800):
    """Split recordings larger than 30 minutes"""
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-c', 'copy',
        '-map', '0',
        '-segment_time', str(segment_time),
        '-f', 'segment',
        f'{input_file}_part_%03d.mp4'
    ]
    # Execute command
```

#### Temp File Cleanup
```bash
# Add to docker-compose.prod.yml
command: >
  sh -c "
    (while true; do
      find /tmp -type f -mtime +1 -delete
      sleep 3600
    done) &
    gunicorn app.main:app ...
  "
```

### ✅ 7. Persistent Storage

**Option 1: Local Storage**
```yaml
volumes:
  - ./data/downloads:/tmp/downloads
```

**Option 2: S3-Compatible Storage**
```python
import boto3

s3_client = boto3.client(
    's3',
    endpoint_url='https://your-endpoint.com',
    aws_access_key_id='KEY',
    aws_secret_access_key='SECRET'
)

# Upload after download
s3_client.upload_file(local_file, 'bucket', 'key')

# Generate presigned URL
url = s3_client.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'bucket', 'Key': 'key'},
    ExpiresIn=3600
)
```

**Option 3: Cloudflare R2**
```python
# Same as S3 but with R2 endpoint
endpoint_url='https://account.r2.cloudflarestorage.com'
```

### ✅ 8. Deployment & CI/CD

**GitHub Actions Workflow:**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker Image
        run: docker build -f Dockerfile.prod -t video-downloader:latest .
      
      - name: Push to Registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push video-downloader:latest
      
      - name: Deploy to Server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d
```

### ✅ 9. Scalability Strategy

#### Stage 1: Single VPS (MVP)
```
1 VPS (4 CPU, 8GB RAM)
├── Docker Compose
├── NGINX
├── Redis
└── Application
```

#### Stage 2: Load Balancer + 2 Nodes
```
Load Balancer (NGINX)
├── App Node 1
├── App Node 2
└── Shared Redis
```

#### Stage 3: Background Workers
```yaml
# Add worker service
worker:
  build: .
  command: celery -A app.tasks worker --loglevel=info
  depends_on:
    - redis
```

**Celery Tasks:**
```python
from celery import Celery

celery_app = Celery('tasks', broker='redis://redis:6379')

@celery_app.task
def download_video_task(url: str, quality: str):
    # Long-running download
    pass
```

#### Stage 4: Kubernetes
```yaml
# k8s/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-downloader
spec:
  replicas: 3
  selector:
    matchLabels:
      app: video-downloader
  template:
    metadata:
      labels:
        app: video-downloader
    spec:
      containers:
      - name: app
        image: video-downloader:latest
        resources:
          limits:
            memory: "4Gi"
            cpu: "2"
```

### ✅ 10. Environment Variables

Create `.env.prod`:
```bash
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key-here
WORKERS=4

# Database
REDIS_URL=redis://redis:6379

# Limits
MAX_DOWNLOAD_SIZE=500MB
MAX_RECORDING_TIME=7200
CLEANUP_DAYS=1

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
DOWNLOAD_LIMIT_PER_DAY=50

# Storage
STORAGE_TYPE=local  # or s3, r2
S3_BUCKET=your-bucket
S3_ENDPOINT=https://endpoint.com
S3_ACCESS_KEY=key
S3_SECRET_KEY=secret

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=info
```

## 🔥 FINAL PRODUCTION CHECKLIST

| Category | Task | Done |
|----------|------|------|
| **Build** | Disable debug mode | ☐ |
| **Build** | Remove dev logs | ☐ |
| **Build** | Build frontend | ☐ |
| **Security** | Add HTTPS + SSL | ☐ |
| **Security** | Add rate limiting | ☐ |
| **Security** | Add token-based downloads | ☐ |
| **Security** | Add bot protection | ☐ |
| **Security** | Add Cloudflare WAF | ☐ |
| **Stability** | Add file auto-deletion | ☐ |
| **Stability** | Add temp cleanup | ☐ |
| **Stability** | Add health checks | ☐ |
| **Scaling** | Use Gunicorn workers | ☐ |
| **Scaling** | Add Redis queue | ☐ |
| **Scaling** | Add background workers | ☐ |
| **Storage** | Setup external storage | ☐ |
| **Storage** | Add file expiry | ☐ |
| **Monitoring** | Enable logs | ☐ |
| **Monitoring** | Add Prometheus | ☐ |
| **Monitoring** | Add Sentry | ☐ |
| **Monitoring** | Add uptime monitoring | ☐ |
| **CI/CD** | Setup GitHub Actions | ☐ |
| **CI/CD** | Add automated tests | ☐ |
| **CI/CD** | Add deployment pipeline | ☐ |

## 🚀 Quick Start Commands

```bash
# 1. Clone and setup
git clone your-repo
cd video-downloader

# 2. Create environment file
cp .env.example .env.prod
nano .env.prod

# 3. Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# 4. Check logs
docker-compose -f docker-compose.prod.yml logs -f

# 5. Check health
curl https://your-domain.com/api

# 6. Monitor
docker stats video-downloader-prod
```

## 📊 Monitoring Commands

```bash
# View logs
docker logs video-downloader-prod --tail 100 -f

# Check disk usage
df -h

# Check memory
free -h

# Check processes
docker exec video-downloader-prod ps aux

# Cleanup old files
docker exec video-downloader-prod find /tmp -type f -mtime +1 -delete
```

## 🔧 Maintenance

### Daily
- Check disk space
- Review error logs
- Monitor download counts

### Weekly
- Update yt-dlp: `pip install --upgrade yt-dlp`
- Review rate limit logs
- Check for failed downloads

### Monthly
- Update dependencies
- Review security logs
- Optimize database
- Update SSL certificates

## 🆘 Troubleshooting

### High CPU Usage
```bash
# Check processes
docker exec video-downloader-prod top

# Reduce workers
# In docker-compose.prod.yml: WORKERS=2
```

### Disk Full
```bash
# Clean old downloads
docker exec video-downloader-prod find /tmp -type f -mtime +1 -delete

# Check sizes
du -sh /tmp/*
```

### Memory Leaks
```bash
# Restart container
docker-compose -f docker-compose.prod.yml restart

# Check memory
docker stats video-downloader-prod
```

## 📞 Support

For issues:
1. Check logs: `/app/logs/error.log`
2. Review monitoring dashboard
3. Check GitHub issues
4. Contact support

---

**Production Ready!** 🎉
