# DigitalOcean Quick Start

Deploy your video downloader to DigitalOcean in 10 minutes!

## Prerequisites

- DigitalOcean account
- Domain name (optional but recommended)
- SSH key or password

## Quick Deploy Steps

### 1. Create Droplet

1. Go to https://cloud.digitalocean.com/droplets
2. Click "Create Droplet"
3. Choose:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Regular $12/month (2 GB RAM) - Recommended
   - **Datacenter:** Closest to your users
   - **Authentication:** Add your SSH key
   - **Hostname:** video-downloader
4. Click "Create Droplet"
5. Wait 1-2 minutes

### 2. Connect to Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

### 3. Run Setup Script

```bash
# Download and run setup script
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/ilovevideo/main/deploy-digitalocean.sh -o setup.sh
chmod +x setup.sh
sudo ./setup.sh
```

This installs:
- Docker & Docker Compose
- NGINX
- Certbot (SSL)
- Firewall (UFW)
- Fail2Ban (security)
- Creates deployer user
- Enables swap

### 4. Deploy Application

```bash
# Switch to deployer user
su - deployer

# Clone repository
git clone https://github.com/YOUR_USERNAME/ilovevideo.git
cd ilovevideo

# Configure environment
cp .env.example .env
nano .env
```

**Update .env:**
```bash
ENVIRONMENT=production
BACKEND_CORS_ORIGINS=https://yourdomain.com
MAX_UPLOAD_SIZE=524288000
DOWNLOAD_TIMEOUT=300
PLAYWRIGHT_TIMEOUT=60000
```

**Deploy:**
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 5. Configure NGINX

```bash
# Exit deployer user
exit

# Create NGINX config
sudo nano /etc/nginx/sites-available/video-downloader
```

**Paste this configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

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
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/video-downloader /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Setup SSL (HTTPS)

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow prompts:
- Enter email
- Agree to terms
- Choose redirect HTTP to HTTPS (option 2)

### 7. Update DNS

Point your domain to droplet IP:
- **A Record:** `@` → `YOUR_DROPLET_IP`
- **A Record:** `www` → `YOUR_DROPLET_IP`

Wait 5-10 minutes for DNS propagation.

### 8. Test Deployment

Visit: `https://yourdomain.com`

Test features:
- Extract video from website
- Download YouTube video
- Download Instagram video
- Convert video to MP3

## Done! 🎉

Your video downloader is now live!

---

## Useful Commands

### View Logs
```bash
cd ~/ilovevideo
docker-compose -f docker-compose.prod.yml logs -f
```

### Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Update Application
```bash
cd ~/ilovevideo
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
```

### Check Status
```bash
docker-compose -f docker-compose.prod.yml ps
sudo systemctl status nginx
```

### Clean Up Docker
```bash
docker system prune -a -f
```

---

## Troubleshooting

### Can't connect to droplet
- Check firewall allows SSH (port 22)
- Verify SSH key is correct
- Try password authentication

### Service won't start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check if port is in use
sudo netstat -tulpn | grep 8000
```

### NGINX errors
```bash
# Test config
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log

# Restart
sudo systemctl restart nginx
```

### SSL certificate fails
- Verify DNS points to droplet IP
- Check domain is accessible via HTTP first
- Ensure port 80 and 443 are open

### Out of memory
```bash
# Check memory
free -h

# Check swap
swapon --show

# Upgrade droplet or add more swap
```

---

## Cost

**Recommended Setup:**
- Droplet: $12/month (2 GB RAM, 50 GB SSD)
- Bandwidth: 2 TB included
- Backups: $2.40/month (optional)
- **Total: $12-15/month**

**Budget Setup:**
- Droplet: $6/month (1 GB RAM, 25 GB SSD)
- May struggle with large videos
- **Total: $6/month**

---

## Monitoring

### DigitalOcean Monitoring (Free)
Enable in droplet settings:
- CPU usage alerts
- Memory usage alerts
- Disk usage alerts

### Uptime Monitoring
Use UptimeRobot (free):
- Monitor: https://yourdomain.com
- Alert via email/SMS if down

---

## Security

Already configured:
- ✅ Firewall (UFW)
- ✅ Fail2Ban (brute force protection)
- ✅ SSL/TLS (HTTPS)
- ✅ Non-root user
- ✅ Docker security

**Additional recommendations:**
- Change SSH port from 22
- Disable root login
- Use SSH keys only (no passwords)
- Enable automatic security updates

---

## Backup

**Code:** Backed up on GitHub
**Data:** No persistent data (cache only)
**Config:** Backup .env file manually

```bash
# Backup config
tar -czf backup-$(date +%Y%m%d).tar.gz .env docker-compose.prod.yml
```

---

## Scaling

### Vertical (Upgrade Droplet)
1. Power off droplet
2. Resize in dashboard
3. Power on
4. No data loss

### Horizontal (Multiple Droplets)
1. Create load balancer
2. Deploy to multiple droplets
3. Use managed Redis

---

## Support

- **Full Guide:** See `DIGITALOCEAN_DEPLOYMENT.md`
- **DigitalOcean Docs:** https://docs.digitalocean.com/
- **Community:** https://www.digitalocean.com/community
- **GitHub Issues:** Your repository

---

**That's it!** Your video downloader is live on DigitalOcean! 🚀

For detailed instructions, see `DIGITALOCEAN_DEPLOYMENT.md`
