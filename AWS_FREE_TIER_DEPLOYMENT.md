# 🆓 AWS Free Tier Deployment Guide

Deploy your Video Downloader application **FREE** for 12 months using AWS Free Tier!

## ✅ What's Included in AWS Free Tier (12 Months)

| Service | Free Tier Limit | Perfect For |
|---------|----------------|-------------|
| **EC2** | 750 hours/month of t2.micro or t3.micro | ✅ Your app! |
| **EBS Storage** | 30 GB SSD | ✅ Enough |
| **Data Transfer** | 100 GB/month outbound | ✅ Good start |
| **S3 Storage** | 5 GB standard storage | ✅ For downloads |
| **S3 Requests** | 20,000 GET, 2,000 PUT | ✅ Sufficient |
| **CloudWatch** | 10 custom metrics, 10 alarms | ✅ Monitoring |
| **Elastic IP** | 1 IP (if attached to running instance) | ✅ Free |

**Total Cost: $0/month for first 12 months!** 🎉

## ⚠️ Important Limitations

### What's NOT Free:
- ❌ Data transfer over 100 GB/month (~$9 per additional 100GB)
- ❌ EBS storage over 30 GB (~$0.10/GB/month)
- ❌ Multiple EC2 instances (only 750 hours total)
- ❌ Load Balancers (~$16/month)
- ❌ NAT Gateways (~$32/month)

### Recommended Configuration for Free Tier:
```
✅ 1x t3.micro instance (1 vCPU, 1GB RAM)
✅ 30 GB EBS storage
✅ 1 Elastic IP
✅ S3 for temporary file storage
✅ CloudWatch basic monitoring
```

## 🚀 Free Tier Deployment (Step-by-Step)

### Step 1: Create AWS Account

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Enter email, password, account name
4. **Provide credit card** (required but won't be charged in free tier)
5. Verify phone number
6. Choose "Basic Support - Free"
7. Complete!

### Step 2: Launch Free Tier EC2 Instance

**Via AWS Console:**

```
1. Login to AWS Console
2. Go to EC2 Dashboard
3. Click "Launch Instance"

Configuration:
├── Name: video-downloader-free
├── AMI: Ubuntu Server 22.04 LTS (Free tier eligible)
├── Instance type: t3.micro (Free tier eligible) ⭐
├── Key pair: Create new → Download .pem file
├── Network settings:
│   ├── Create security group
│   ├── Allow SSH (22) from My IP
│   ├── Allow HTTP (80) from Anywhere
│   └── Allow HTTPS (443) from Anywhere
├── Storage: 30 GB gp3 (Free tier eligible)
└── Launch!
```

**Important:** Make sure you see "Free tier eligible" labels!

### Step 3: Connect to Instance

```bash
# Make key file secure
chmod 400 your-key.pem

# Connect via SSH
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# You're in! 🎉
```

### Step 4: Install Docker (Optimized for t3.micro)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

### Step 5: Deploy Application (Free Tier Optimized)

```bash
# Clone repository
git clone https://github.com/your-repo/video-downloader.git
cd video-downloader

# Create free tier docker-compose
nano docker-compose.free-tier.yml
```

**docker-compose.free-tier.yml** (Optimized for 1GB RAM):

```yaml
version: '3.8'

services:
  video-downloader:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: video-downloader
    restart: unless-stopped
    ports:
      - "80:8000"
      - "443:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - WORKERS=1  # Only 1 worker for 1GB RAM
      - LOG_LEVEL=warning
      - MAX_DOWNLOAD_SIZE=200MB  # Reduced for free tier
      - CLEANUP_DAYS=1
    volumes:
      - ./data/downloads:/tmp/downloads
      - ./data/logs:/app/logs
    deploy:
      resources:
        limits:
          cpus: '0.8'
          memory: 900M  # Leave some for system
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  downloads:
    driver: local
```

**Deploy:**

```bash
# Create directories
mkdir -p data/downloads data/logs

# Build and start (this may take 10-15 minutes on t3.micro)
docker-compose -f docker-compose.free-tier.yml up -d --build

# Check status
docker-compose -f docker-compose.free-tier.yml ps

# View logs
docker-compose -f docker-compose.free-tier.yml logs -f
```

### Step 6: Setup S3 for File Storage (Free Tier)

```bash
# Install AWS CLI
sudo apt install awscli -y

# Configure AWS CLI
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Region: us-east-1
# Output format: json

# Create S3 bucket
aws s3 mb s3://video-downloader-$(date +%s)

# Set lifecycle policy (auto-delete after 1 day)
cat > lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "Id": "DeleteAfter1Day",
      "Status": "Enabled",
      "Expiration": {
        "Days": 1
      }
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket your-bucket-name \
  --lifecycle-configuration file://lifecycle.json
```

### Step 7: Setup Free SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot -y

# Stop Docker temporarily
docker-compose -f docker-compose.free-tier.yml down

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Restart Docker
docker-compose -f docker-compose.free-tier.yml up -d
```

### Step 8: Setup Auto-Cleanup (Important for Free Tier!)

```bash
# Create cleanup script
cat > cleanup.sh << 'EOF'
#!/bin/bash
# Clean old downloads
find /home/ubuntu/video-downloader/data/downloads -type f -mtime +1 -delete

# Clean Docker
docker system prune -af --volumes

# Clean logs
find /home/ubuntu/video-downloader/data/logs -type f -mtime +7 -delete
EOF

chmod +x cleanup.sh

# Add to crontab (runs every 6 hours)
(crontab -l 2>/dev/null; echo "0 */6 * * * /home/ubuntu/video-downloader/cleanup.sh") | crontab -
```

## 💰 Staying Within Free Tier Limits

### Monitor Your Usage

**Check EC2 Hours:**
```bash
# AWS Console → Billing → Free Tier
# Should show: 750 hours available, X hours used
```

**Check Data Transfer:**
```bash
# AWS Console → CloudWatch → Metrics → EC2 → NetworkOut
# Keep under 100 GB/month
```

**Set Billing Alarm:**
```bash
# AWS Console → CloudWatch → Alarms → Create Alarm
# Metric: EstimatedCharges
# Threshold: $1
# Action: Email notification
```

### Tips to Stay Free:

1. ✅ **Use only 1 EC2 instance** (t3.micro)
2. ✅ **Keep storage under 30 GB**
3. ✅ **Auto-delete old files** (daily cleanup)
4. ✅ **Use S3 for temporary storage** (with lifecycle policy)
5. ✅ **Stop instance when not in use** (saves hours)
6. ✅ **Monitor data transfer** (keep under 100 GB/month)
7. ✅ **Don't use Load Balancers** (not free)
8. ✅ **Don't use NAT Gateways** (not free)

### Performance Optimization for t3.micro (1GB RAM):

```bash
# Add swap space (helps with low RAM)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Optimize Docker
sudo nano /etc/docker/daemon.json
```

Add:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

```bash
sudo systemctl restart docker
```

## 📊 Expected Performance (Free Tier)

| Feature | Performance |
|---------|-------------|
| **Video Downloads** | ✅ Works well |
| **YouTube Extraction** | ✅ Works (slower) |
| **Playlist Downloads** | ⚠️ 1-2 videos at a time |
| **Livestream Recording** | ⚠️ Up to 720p |
| **Video Compression** | ⚠️ Slow but works |
| **Concurrent Users** | ⚠️ 2-3 users max |

## 🚨 What Happens After 12 Months?

After 12 months, you'll be charged:

| Resource | Monthly Cost |
|----------|--------------|
| t3.micro EC2 | ~$7.50 |
| 30 GB EBS | ~$3 |
| Data Transfer (100GB) | ~$9 |
| **Total** | **~$20/month** |

**Options:**
1. Continue paying (~$20/month)
2. Migrate to cheaper VPS (DigitalOcean, Linode ~$5/month)
3. Create new AWS account (not recommended)

## 🎯 Quick Start Commands

```bash
# 1. Launch t3.micro instance (Free Tier)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. One-command setup
curl -fsSL https://raw.githubusercontent.com/your-repo/video-downloader/main/scripts/aws-free-tier-setup.sh | bash

# 4. Access your app
http://your-ec2-ip
```

## ✅ Free Tier Checklist

- [ ] Created AWS account
- [ ] Launched t3.micro instance (Free tier eligible)
- [ ] Used 30 GB or less storage
- [ ] Configured 1 Elastic IP
- [ ] Setup auto-cleanup cron
- [ ] Created S3 bucket with lifecycle policy
- [ ] Set billing alarm at $1
- [ ] Enabled CloudWatch monitoring
- [ ] Tested application
- [ ] Documented public IP/domain

## 🆘 Troubleshooting

### "Out of Memory" Errors
```bash
# Add more swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### "Disk Full" Errors
```bash
# Clean Docker
docker system prune -af --volumes

# Clean downloads
rm -rf /home/ubuntu/video-downloader/data/downloads/*
```

### Slow Performance
```bash
# Reduce workers to 1
# In docker-compose: WORKERS=1

# Limit concurrent downloads
# In backend: MAX_CONCURRENT_DOWNLOADS=1
```

## 📚 Resources

- [AWS Free Tier Details](https://aws.amazon.com/free/)
- [AWS Free Tier FAQ](https://aws.amazon.com/free/free-tier-faqs/)
- [AWS Billing Dashboard](https://console.aws.amazon.com/billing/)
- [AWS Cost Calculator](https://calculator.aws/)

---

**Deploy for FREE for 12 months!** 🎉

**After 12 months: ~$20/month or migrate to $5/month VPS**
