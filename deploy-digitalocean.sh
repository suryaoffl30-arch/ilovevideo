#!/bin/bash

# DigitalOcean Droplet Setup Script
# Run this on a fresh Ubuntu 22.04 droplet

set -e

echo "🚀 Video Downloader - DigitalOcean Setup"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Updating system...${NC}"
apt update && apt upgrade -y

echo -e "${GREEN}Step 2: Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker already installed"
fi

echo -e "${GREEN}Step 3: Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    apt install docker-compose -y
else
    echo "Docker Compose already installed"
fi

echo -e "${GREEN}Step 4: Installing additional tools...${NC}"
apt install -y git nginx certbot python3-certbot-nginx ufw fail2ban

echo -e "${GREEN}Step 5: Setting up firewall...${NC}"
ufw --force enable
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
echo "Firewall configured"

echo -e "${GREEN}Step 6: Creating deployer user...${NC}"
if ! id "deployer" &>/dev/null; then
    adduser --disabled-password --gecos "" deployer
    usermod -aG sudo deployer
    usermod -aG docker deployer
    echo "deployer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
    echo "User 'deployer' created"
else
    echo "User 'deployer' already exists"
fi

echo -e "${GREEN}Step 7: Enabling swap (2GB)...${NC}"
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap enabled"
else
    echo "Swap already configured"
fi

echo ""
echo -e "${GREEN}✅ Server setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Switch to deployer user: su - deployer"
echo "2. Clone your repository: git clone https://github.com/YOUR_USERNAME/ilovevideo.git"
echo "3. cd ilovevideo"
echo "4. Copy .env.example to .env and configure"
echo "5. Run: docker-compose -f docker-compose.prod.yml up -d --build"
echo "6. Configure NGINX (see DIGITALOCEAN_DEPLOYMENT.md)"
echo "7. Setup SSL: sudo certbot --nginx -d yourdomain.com"
echo ""
echo -e "${GREEN}Installation complete! 🎉${NC}"
