# Plain VPS Deployment Guide

Deploy your video downloader to any VPS (Ubuntu) in 15 minutes with full control.

## Prerequisites

- VPS with Ubuntu 22.04 LTS (1-2 GB RAM minimum)
- Root or sudo access
- Domain name (optional but recommended)
- SSH client (PuTTY for Windows, Terminal for Mac/Linux)

## Recommended VPS Providers

| Provider | Plan | Price | Specs |
|----------|------|-------|-------|
| **Contabo** | VPS S | $5/month | 4 GB RAM, 2 vCPU, 50 GB SSD |
| **Hetzner** | CX21 | $5/month | 2 GB RAM, 1 vCPU, 40 GB SSD |
| **Vultr** | Regular | $6/month | 1 GB RAM, 1 vCPU, 25 GB SSD |
| **Hostinger** | VPS 1 | $5/month | 1 GB RAM, 1 vCPU, 20 GB SSD |

## Quick Deploy (Copy-Paste Method)

### Step 1: Get VPS

1. Sign up with any provider above
2. Create VPS with **Ubuntu 22.04 LTS**
3. Note down:
   - IP address
   - Root password (or SSH key)

### Step 2: Connect to VPS

**Windows (using PuTTY):**
- Download PuTTY: https://www.putty.org/
- Host: Your VPS IP
- Port: 22
- Click "Open"
- Login as: `root`
- Password: Your root password

**Mac/Linux:**
```bash
ssh root@YOUR_VPS_IP
```

### Step 3: Run Automated Setup

Copy and paste this entire block:

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Install additional tools
apt install -y git nginx certbot python3-certbot-nginx ufw fail2ban htop

# Setup firewall
ufw --force enable
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp

# Enable swap (2GB)
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Create deployer user
adduser --disabled-password --gecos "" deployer
usermod -aG sudo deployer
usermod -aG docker deployer
echo "deployer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

echo "✅ Server setup complete!"
```

Wait 2-3 minutes for installation to complete.

### Step 4: Deploy Application

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

**Edit .env file** (press Ctrl+X, then Y, then Enter to save):
```bash
ENVIRONMENT=production
BACKEND_CORS_ORIGINS=https://yourdomain.com
MAX_UPLOAD_SIZE=524288000
DOWNLOAD_TIMEOUT=300
PLAYWRIGHT_TIMEOUT=60000
```

**Deploy with Docker:**
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

Wait 5-10 minutes for first build. Check progress:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

Press Ctrl+C to exit logs.

### Step 5: Configure NGINX

```bash
# Exit deployer user
exit

# Create NGINX config
nano /etc/nginx/sites-available/video-downloader
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
        proxy_connect_timeout 75s;
    }
}
```

**Enable site:**
```bash
ln -s /etc/nginx/sites-available/video-downloader /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 6: Setup SSL (HTTPS)

**Point your domain to VPS IP first:**
- Go to your domain registrar
- Add A record: `@` → `YOUR_VPS_IP`
- Add A record: `www` → `YOUR_VPS_IP`
- Wait 5-10 minutes for DNS propagation

**Get SSL certificate:**
```bash
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow prompts:
- Enter email
- Agree to terms
- Choose option 2 (redirect HTTP to HTTPS)

### Step 7: Test Deployment

Visit: `https://yourdomain.com`

Test features:
- ✅ Extract video from website
- ✅ Download YouTube video
- ✅ Download Instagram video
- ✅ Convert video to MP3
- ✅ Compress video

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

### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Start Services
```bash
docker-compose -f docker-compose.prod.yml up -d
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
systemctl status nginx
docker stats
```

### Check Disk Space
```bash
df -h
docker system df
```

### Clean Up Docker
```bash
docker system prune -a -f
```

### View NGINX Logs
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Check Memory Usage
```bash
free -h
htop  # Press q to exit
```

---

## Troubleshooting

### Can't Connect to VPS
```bash
# Check if SSH is running
systemctl status ssh

# Check firewall
ufw status

# Allow SSH if blocked
ufw allow OpenSSH
```

### Service Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check if port is in use
netstat -tulpn | grep 8000

# Restart Docker
systemctl restart docker
```

### NGINX Errors
```bash
# Test config
nginx -t

# Check logs
tail -f /var/log/nginx/error.log

# Restart NGINX
systemctl restart nginx
```

### SSL Certificate Fails
```bash
# Verify DNS points to VPS
dig yourdomain.com

# Check if port 80 is accessible
curl http://yourdomain.com

# Try again
certbot --nginx -d yourdomain.com
```

### Out of Memory
```bash
# Check memory
free -h

# Check swap
swapon --show

# Add more swap
fallocate -l 4G /swapfile2
chmod 600 /swapfile2
mkswap /swapfile2
swapon /swapfile2
```

### Disk Full
```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a -f

# Clean apt cache
apt clean
apt autoremove -y

# Find large files
du -h --max-depth=1 / | sort -hr | head -20
```

---

## Security Hardening

### 1. Change SSH Port (Optional)
```bash
nano /etc/ssh/sshd_config
# Change Port 22 to Port 2222
systemctl restart ssh
ufw allow 2222/tcp
```

### 2. Disable Root Login
```bash
nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
systemctl restart ssh
```

### 3. Setup Fail2Ban
```bash
# Already installed, configure
nano /etc/fail2ban/jail.local
```

Add:
```ini
[sshd]
enabled = true
port = 22
maxretry = 3
bantime = 3600
```

```bash
systemctl restart fail2ban
```

### 4. Enable Automatic Updates
```bash
apt install unattended-upgrades -y
dpkg-reconfigure --priority=low unattended-upgrades
```

### 5. Setup Monitoring
```bash
# Install monitoring tools
apt install -y netdata

# Access at: http://YOUR_IP:19999
```

---

## Performance Optimization

### 1. Optimize Docker
```bash
# Edit docker-compose.prod.yml
nano ~/ilovevideo/docker-compose.prod.yml
```

Add resource limits:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1.5G
        reservations:
          memory: 512M
```

### 2. Enable NGINX Caching
```bash
nano /etc/nginx/sites-available/video-downloader
```

Add before server block:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;
```

Add in location block:
```nginx
proxy_cache my_cache;
proxy_cache_valid 200 60m;
```

### 3. Optimize Swap
```bash
# Reduce swappiness
echo "vm.swappiness=10" >> /etc/sysctl.conf
sysctl -p
```

---

## Backup & Recovery

### Backup Configuration
```bash
# Backup important files
tar -czf backup-$(date +%Y%m%d).tar.gz \
  ~/ilovevideo/.env \
  ~/ilovevideo/docker-compose.prod.yml \
  /etc/nginx/sites-available/video-downloader

# Download backup to local machine
# On your local machine:
scp root@YOUR_VPS_IP:~/backup-*.tar.gz ./
```

### Disaster Recovery
If VPS fails:
1. Create new VPS
2. Run setup script (Step 3)
3. Clone repository
4. Restore .env file
5. Deploy with Docker Compose
6. Update DNS to new IP

Recovery time: ~15 minutes

---

## Monitoring & Alerts

### 1. Setup Uptime Monitoring
Use external service (free):
- **UptimeRobot**: https://uptimerobot.com/
- **Pingdom**: https://www.pingdom.com/
- **StatusCake**: https://www.statuscake.com/

Monitor:
- `https://yourdomain.com`
- `https://yourdomain.com/health`

### 2. Email Alerts
```bash
# Install mail utilities
apt install mailutils -y

# Test email
echo "Test from VPS" | mail -s "Test" your@email.com
```

### 3. Disk Space Alerts
```bash
# Create monitoring script
nano /usr/local/bin/check-disk.sh
```

Add:
```bash
#!/bin/bash
THRESHOLD=80
USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $USAGE -gt $THRESHOLD ]; then
    echo "Disk usage is ${USAGE}%" | mail -s "Disk Alert" your@email.com
fi
```

```bash
chmod +x /usr/local/bin/check-disk.sh

# Add to crontab (run daily)
crontab -e
# Add: 0 9 * * * /usr/local/bin/check-disk.sh
```

---

## Scaling

### Vertical Scaling (Upgrade VPS)
1. Contact provider to upgrade
2. Usually no downtime
3. More RAM/CPU available immediately

### Horizontal Scaling (Multiple Servers)
1. Setup load balancer
2. Deploy to multiple VPS
3. Use external Redis for shared cache
4. Use external storage for downloads

---

## Cost Breakdown

**Monthly Costs:**
- VPS: $5-6/month
- Domain: $10-15/year (~$1/month)
- SSL: Free (Let's Encrypt)
- **Total: ~$6-7/month**

**One-time Costs:**
- Domain registration: $10-15/year
- **Total: $10-15**

---

## Support Resources

- **Ubuntu Docs**: https://ubuntu.com/server/docs
- **Docker Docs**: https://docs.docker.com/
- **NGINX Docs**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/docs/
- **Your GitHub Repo**: Issues tab

---

## Quick Reference Card

```bash
# Deploy
cd ~/ilovevideo && docker-compose -f docker-compose.prod.yml up -d --build

# Update
cd ~/ilovevideo && git pull && docker-compose -f docker-compose.prod.yml up -d --build

# Restart
docker-compose -f docker-compose.prod.yml restart

# Logs
docker-compose -f docker-compose.prod.yml logs -f

# Status
docker-compose -f docker-compose.prod.yml ps

# Clean
docker system prune -a -f

# SSL Renew
certbot renew

# Backup
tar -czf backup-$(date +%Y%m%d).tar.gz ~/ilovevideo/.env
```

---

Your video downloader is now running on a plain VPS with full control! 🚀
