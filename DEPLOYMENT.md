# Deployment Guide

## Local Development

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium

# Copy environment file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Copy environment file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edit .env and set:
# VITE_API_BASE_URL=http://localhost:8000

npm run dev
```

Access at: http://localhost:3000

---

## Docker Deployment

### Build and Run

```bash
# Copy environment file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Build and start
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

Access at: http://localhost:8000

### Production with Nginx

```bash
docker-compose --profile production up -d
```

Access at: http://localhost:80

---

## Cloud Deployment

### Railway

1. Create new project on Railway
2. Connect your GitHub repository
3. Add environment variables:
   ```
   APP_PORT=8000
   DOWNLOAD_DIR=/app/downloads
   DEBUG=false
   CORS_ORIGINS=https://your-domain.com
   MAX_VIDEO_SIZE_MB=500
   PLAYWRIGHT_TIMEOUT=30000
   ENABLE_FFMPEG_CONVERSION=true
   ```
4. Deploy from Dockerfile
5. Railway will automatically assign a domain

### Render

1. Create new Web Service
2. Connect repository
3. Set build command: `docker build -t video-downloader .`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as Railway)
6. Choose instance type (at least 2GB RAM recommended)
7. Deploy

### AWS EC2

```bash
# SSH into EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu

# Clone repository
git clone https://github.com/your-repo/video-downloader.git
cd video-downloader

# Configure environment
cp .env.example .env
nano .env  # Edit as needed

# Run with Docker Compose
docker-compose up -d

# Set up Nginx reverse proxy (optional)
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/video-downloader
```

Nginx config for EC2:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/video-downloader /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### DigitalOcean App Platform

1. Create new App
2. Connect GitHub repository
3. Detect Dockerfile automatically
4. Add environment variables
5. Choose Basic plan ($5/month minimum)
6. Deploy

---

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APP_PORT` | Backend port | 8000 | No |
| `DOWNLOAD_DIR` | Download directory path | ./downloads | No |
| `DEBUG` | Enable debug logging | false | No |
| `CORS_ORIGINS` | Allowed CORS origins | localhost:3000 | Yes |
| `MAX_VIDEO_SIZE_MB` | Max video size limit | 500 | No |
| `PLAYWRIGHT_TIMEOUT` | Browser timeout (ms) | 30000 | No |
| `ENABLE_FFMPEG_CONVERSION` | Enable HLS conversion | true | No |
| `VITE_API_BASE_URL` | Frontend API URL | http://localhost:8000 | Yes |

---

## Troubleshooting

### Playwright Issues

```bash
# Reinstall browsers
playwright install chromium --with-deps

# Check browser installation
playwright install --dry-run
```

### FFmpeg Not Found

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Docker Build Fails

```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

---

## Performance Optimization

1. **Increase timeout for slow sites:**
   ```
   PLAYWRIGHT_TIMEOUT=60000
   ```

2. **Limit concurrent extractions:**
   Use a task queue (Redis + Celery) for production

3. **Enable caching:**
   Cache extracted URLs for repeated requests

4. **Use CDN:**
   Serve frontend through CloudFlare or similar

5. **Scale horizontally:**
   Run multiple instances behind a load balancer

---

## Security Considerations

1. **Rate limiting:** Implement rate limiting to prevent abuse
2. **Input validation:** Already implemented in Pydantic models
3. **CORS:** Configure strict CORS origins in production
4. **File size limits:** Set MAX_VIDEO_SIZE_MB appropriately
5. **DRM check:** Basic DRM detection is implemented
6. **HTTPS:** Always use HTTPS in production
7. **Authentication:** Add authentication for production use

---

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000

# Docker health
docker-compose ps
```

### Logs

```bash
# Docker logs
docker-compose logs -f video-downloader

# Backend logs (local)
tail -f logs/app.log
```

### Metrics

Consider adding:
- Prometheus for metrics
- Grafana for visualization
- Sentry for error tracking
