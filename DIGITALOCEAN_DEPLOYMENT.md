# DigitalOcean Deployment Guide

Complete guide for deploying the Video Downloader to DigitalOcean with Docker.

## Prerequisites

- DigitalOcean account
- GitHub repository with your code
- Domain name (optional but recommended)
- Basic SSH knowledge

## Deployment Options

### Option 1: App Platform (Easiest - PaaS)
Managed platform, similar to Heroku/Render
- **Cost:** $5-12/month
- **Pros:** Easy setup, auto-scaling, managed
- **Cons:** Less control, higher cost

### Option 2: Droplet (Recommended - Full Control)
Virtual private server with Docker
- **Cost:** $6-12/month
- **Pros:** Full control, cheaper, more powerful
- **Cons:** Manual setup, you manage everything

### Option 3: Kubernetes (Advanced)
For high-traffic production apps
- **Cost:** $12+/month
- **Pros:** Auto-scaling, high availability
- **Cons:** Complex, overkill for most use cases

---

## Option 1: App Platform Deployment

### Step 1: Create App

1. **Go to DigitalOcean Dashboard:**
   - https://cloud.digitalocean.com/apps

2. **Create New App:**
   - Click "Create" → "Apps"
   - Choose "GitHub" as source
   - Authorize DigitalOcean to access your repository
   - Select your `ilovevideo` repository
   - Branch: `main`
   - Click "Next"

### Step 2: Configure Services

**Backend Service:**
- **Name:** video-downloader-api
- **Type:** Web Service
- **Dockerfile Path:** `Dockerfile.prod`
- **HTTP Port:** 8000
- **Instance Size:** Basic ($5/month - 512 MB RAM) or Professional ($12/month - 1 GB RAM)
- **Instance Count:** 1

**Environment Variables:**
```
ENVIRONMENT=production
BACKEND_CORS_ORIGINS=${video-downloader-web.ONDIGITALOCEAN_APP_URL}
MAX_UPLOAD_SIZE=524288000
DOWNLOAD_TIMEOUT=300
PLAYWRIGHT_TIMEOUT=60000
```

**Frontend Service:**
- **Name:** video-downloader-web
- **Type:** Static Site
- **Build Command:** `cd frontend && npm install && npm run build`
- **Output Directory:** `frontend/dist`

**Environment Variables:**
```
VITE_API_URL=${video-downloader-api.ONDIGITALOCEAN_APP_URL}
```

### Step 3: Add Database (Optional)

- **Type:** Redis
- **Plan:** Basic ($15/month) or Dev ($7/month)
- Add to backend environment: `REDIS_URL=${redis.DATABASE_URL}`

### Step 4: Deploy

1. Review configuration
2. Click "Create Resources"
3. Wait 5-10 minutes for deployment
4. Access your app at the provided URLs

### Step 5: Custom Domain (Optional)

1. Go to app settings
2. Click "Domains"
3. Add your domain
4. Update DNS records as shown
5. SSL certificate is automatic

---

## Option 2: Droplet Deployment (Recommended)

This gives you full control and is more cost-effective.

### Step 1: Create Droplet

1. **Go to DigitalOcean Dashboard:**
   - https://cloud.digitalocean.com/droplets

2. **Create Droplet:**
   - Click "Create" → "Droplets"
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** 
     - Basic: $6/month (1 GB RAM, 1 vCPU, 25 GB SSD)
     - Regular: $12/month (2 GB RAM, 1 vCPU, 50 GB SSD) - Recommended
   - **Datacenter:** Choose closest to your users
   - **Authentication:** SSH Key (recommended) or Password
   - **Hostname:** video-downloader
   - Click "Create Droplet"

3. **Wait for droplet to be created** (1-2 minutes)

### Step 2: Initial Server Setup

SSH into your droplet:
```bash
ssh root@YOUR_DROPLET_IP
```

**Update system:**
```bash
apt update && apt upgrade -y
```

**Install Docker:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Verify installation
docker --version
docker-compose --version
```

**Create non-root user (recommended):**
```bash
adduser deployer
usermod -aG sudo deployer
usermod -aG docker deployer
su - deployer
```

### Step 3: Setup Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

### Step 4: Clone Repository

```bash
# Install Git
sudo apt install git -y

# Clone your repository
git clone https://github.com/YOUR_USERNAME/ilovevideo.git
cd ilovevideo
```

### Step 5: Configure Environment

```bash
# Copy environment file
cp .env.example .env

# Edit environment variables
nano .env
```

**Update .env file:**
```bash
ENVIRONMENT=production
BACKEND_CORS_ORIGINS=https://yourdomain.com
MAX_UPLOAD_SIZE=524288000
DOWNLOAD_TIMEOUT=300
PLAYWRIGHT_TIMEOUT=60000
```

### Step 6: Deploy with Docker Compose

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 7: Setup NGINX Reverse Proxy

**Install NGINX:**
```bash
sudo apt install nginx -y
```

**Create NGINX configuration:**
```bash
sudo nano /etc/nginx/sites-available/video-downloader
```

**Add this configuration:**
```nginx
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

    client_max_body_size 500M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    root /home/deployer/ilovevideo/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/video-downloader /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 8: Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 9: Setup Auto-Deployment (Optional)

**Create deployment script:**
```bash
nano ~/deploy.sh
```

**Add this content:**
```bash
#!/bin/bash
cd /home/deployer/ilovevideo
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
docker system prune -f
```

**Make executable:**
```bash
chmod +x ~/deploy.sh
```

**Setup GitHub webhook (optional):**
```bash
# Install webhook listener
sudo apt install webhook -y

# Configure webhook to run deploy.sh on push
# See: https://github.com/adnanh/webhook
```

### Step 10: Monitoring & Maintenance

**View logs:**
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# NGINX logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

**Restart services:**
```bash
docker-compose -f docker-compose.prod.yml restart
```

**Update application:**
```bash
cd ~/ilovevideo
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
```

**Check disk space:**
```bash
df -h
docker system df
```

**Clean up Docker:**
```bash
docker system prune -a -f
```

---

## Option 3: Kubernetes Deployment (Advanced)

For high-traffic production deployments.

### Prerequisites
- DigitalOcean Kubernetes cluster ($12+/month)
- kubectl installed locally
- Basic Kubernetes knowledge

### Quick Setup

1. **Create Kubernetes Cluster:**
   - Dashboard → Kubernetes → Create Cluster
   - Choose plan and region
   - Download kubeconfig

2. **Deploy with kubectl:**
```bash
# Set kubeconfig
export KUBECONFIG=~/Downloads/k8s-config.yaml

# Create namespace
kubectl create namespace video-downloader

# Create secrets
kubectl create secret generic app-secrets \
  --from-literal=BACKEND_CORS_ORIGINS=https://yourdomain.com \
  -n video-downloader

# Apply manifests (create these based on docker-compose.prod.yml)
kubectl apply -f k8s/ -n video-downloader
```

---

## Cost Comparison

### App Platform:
- Basic: $5/month (512 MB RAM)
- Professional: $12/month (1 GB RAM)
- **Total:** $5-12/month + $7-15 for Redis

### Droplet (Recommended):
- Basic: $6/month (1 GB RAM)
- Regular: $12/month (2 GB RAM)
- **Total:** $6-12/month (includes everything)

### Kubernetes:
- Cluster: $12/month (2 GB RAM)
- Load Balancer: $12/month
- **Total:** $24+/month

---

## Performance Optimization

### 1. Enable Swap (for low RAM droplets)

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 2. Optimize Docker

```bash
# Limit container resources in docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

### 3. Setup Redis Caching

Already configured in docker-compose.prod.yml

### 4. Enable NGINX Caching

Add to NGINX config:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;
proxy_cache my_cache;
proxy_cache_valid 200 60m;
```

---

## Security Best Practices

### 1. Firewall Configuration
```bash
sudo ufw status
sudo ufw allow from YOUR_IP to any port 22  # Restrict SSH
```

### 2. Fail2Ban (Prevent brute force)
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Automatic Security Updates
```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### 4. Docker Security
```bash
# Run containers as non-root (already configured in Dockerfile.prod)
# Limit container capabilities
# Use Docker secrets for sensitive data
```

### 5. Rate Limiting
Already configured in nginx.prod.conf

---

## Backup & Recovery

### Backup Strategy

**1. Code Backup:**
- GitHub is your source of truth
- No additional backup needed

**2. Data Backup:**
- Redis data is cache only (ephemeral)
- No persistent data to backup

**3. Configuration Backup:**
```bash
# Backup .env and configs
tar -czf backup-$(date +%Y%m%d).tar.gz .env docker-compose.prod.yml
```

### Disaster Recovery

**If droplet fails:**
1. Create new droplet
2. Follow setup steps
3. Clone repository
4. Deploy with Docker Compose
5. Update DNS to new IP

**Recovery time:** ~15 minutes

---

## Monitoring & Alerts

### 1. DigitalOcean Monitoring (Free)

Enable in droplet settings:
- CPU usage
- Memory usage
- Disk usage
- Bandwidth

### 2. Uptime Monitoring

Use external service:
- UptimeRobot (free)
- Pingdom
- StatusCake

Monitor:
- https://yourdomain.com
- https://api.yourdomain.com/health

### 3. Log Monitoring

```bash
# Install log monitoring
sudo apt install logwatch -y

# View Docker logs
docker-compose -f docker-compose.prod.yml logs --tail=100
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check Docker logs
docker-compose -f docker-compose.prod.yml logs

# Check container status
docker ps -a

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Add swap space (see Performance Optimization)
# Or upgrade droplet
```

### Disk Full

```bash
# Check disk usage
df -h
docker system df

# Clean up
docker system prune -a -f
sudo apt autoremove -y
```

### NGINX Errors

```bash
# Check NGINX config
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log

# Restart NGINX
sudo systemctl restart nginx
```

### SSL Certificate Issues

```bash
# Renew certificate
sudo certbot renew

# Check certificate status
sudo certbot certificates
```

---

## Scaling

### Vertical Scaling (Upgrade Droplet)

1. Power off droplet
2. Resize in dashboard
3. Power on
4. No data loss

### Horizontal Scaling (Multiple Droplets)

1. Create load balancer ($12/month)
2. Deploy to multiple droplets
3. Configure load balancer
4. Use managed Redis for shared cache

---

## Support & Resources

- **DigitalOcean Docs:** https://docs.digitalocean.com/
- **Community:** https://www.digitalocean.com/community
- **Support:** Available on paid plans
- **Status:** https://status.digitalocean.com/

---

## Quick Commands Reference

```bash
# Deploy
docker-compose -f docker-compose.prod.yml up -d --build

# Stop
docker-compose -f docker-compose.prod.yml down

# Restart
docker-compose -f docker-compose.prod.yml restart

# Logs
docker-compose -f docker-compose.prod.yml logs -f

# Update
git pull && docker-compose -f docker-compose.prod.yml up -d --build

# Clean up
docker system prune -a -f

# Check status
docker-compose -f docker-compose.prod.yml ps
systemctl status nginx
sudo ufw status
```

---

## Next Steps

1. ✅ Create DigitalOcean account
2. ✅ Create droplet
3. ✅ Setup Docker
4. ✅ Deploy application
5. ✅ Configure NGINX
6. ✅ Setup SSL
7. ✅ Configure monitoring
8. ✅ Test thoroughly
9. ✅ Share your app!

Your video downloader is now live on DigitalOcean! 🚀
