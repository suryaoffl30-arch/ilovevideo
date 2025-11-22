# 🚀 AWS Deployment Guide

Complete guide for deploying the Video Downloader application to AWS with multiple deployment options.

## 📋 Deployment Options

### Option 1: EC2 (Simplest) ⭐ Recommended for Start
- Single EC2 instance with Docker
- Cost: ~$20-50/month
- Best for: MVP, small-medium traffic

### Option 2: ECS Fargate (Scalable)
- Managed containers, auto-scaling
- Cost: ~$50-150/month
- Best for: Production, high traffic

### Option 3: ECS on EC2 (Cost-Effective)
- Self-managed containers
- Cost: ~$30-80/month
- Best for: Budget-conscious production

### Option 4: Lambda + API Gateway (Serverless)
- Pay per use
- Cost: ~$10-100/month (usage-based)
- Best for: Sporadic traffic

---

## 🎯 Option 1: EC2 Deployment (Recommended)

### Step 1: Launch EC2 Instance

**Instance Specs:**
- **Type**: t3.medium (2 vCPU, 4GB RAM) or t3.large (2 vCPU, 8GB RAM)
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 50GB gp3 SSD (expandable)
- **Region**: Choose closest to your users

**Launch via AWS Console:**
```bash
1. Go to EC2 Dashboard
2. Click "Launch Instance"
3. Name: video-downloader-prod
4. AMI: Ubuntu Server 22.04 LTS
5. Instance type: t3.medium
6. Key pair: Create new or use existing
7. Security Group: Create new
   - SSH (22): Your IP
   - HTTP (80): 0.0.0.0/0
   - HTTPS (443): 0.0.0.0/0
   - Custom (8000): 0.0.0.0/0 (temporary)
8. Storage: 50GB gp3
9. Launch!
```

### Step 2: Connect and Setup

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

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

### Step 3: Deploy Application

```bash
# Clone repository
git clone https://github.com/your-repo/video-downloader.git
cd video-downloader

# Create environment file
nano .env.prod
# Add your environment variables

# Create data directories
mkdir -p data/downloads data/logs data/temp ssl

# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 4: Setup Domain & SSL

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
sudo chown ubuntu:ubuntu ssl/*

# Restart with SSL
docker-compose -f docker-compose.prod.yml restart nginx
```

### Step 5: Setup Auto-Renewal

```bash
# Add cron job
sudo crontab -e

# Add this line:
0 0 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/*.pem /home/ubuntu/video-downloader/ssl/ && docker-compose -f /home/ubuntu/video-downloader/docker-compose.prod.yml restart nginx
```

### Step 6: Setup Monitoring

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure CloudWatch
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/home/ubuntu/video-downloader/cloudwatch-config.json
```

---

## 🐳 Option 2: ECS Fargate Deployment

### Prerequisites
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS
aws configure
```

### Step 1: Push Docker Image to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name video-downloader

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -f Dockerfile.prod -t video-downloader:latest .
docker tag video-downloader:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/video-downloader:latest

# Push
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/video-downloader:latest
```

### Step 2: Create ECS Cluster

```bash
# Create cluster
aws ecs create-cluster --cluster-name video-downloader-cluster

# Create task definition (see ecs-task-definition.json below)
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster video-downloader-cluster \
  --service-name video-downloader-service \
  --task-definition video-downloader:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Step 3: Setup Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name video-downloader-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Create target group
aws elbv2 create-target-group \
  --name video-downloader-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx \
  --target-type ip \
  --health-check-path /api

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

---

## 📦 Infrastructure as Code (Terraform)

### terraform/main.tf

```hcl
provider "aws" {
  region = "us-east-1"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "video-downloader-vpc"
  }
}

# Subnets
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "video-downloader-public-1"
  }
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = {
    Name = "video-downloader-public-2"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "video-downloader-igw"
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "video-downloader-public-rt"
  }
}

# Security Group
resource "aws_security_group" "app" {
  name        = "video-downloader-sg"
  description = "Security group for video downloader"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "video-downloader-sg"
  }
}

# EC2 Instance
resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0" # Ubuntu 22.04
  instance_type = "t3.medium"
  
  subnet_id                   = aws_subnet.public_1.id
  vpc_security_group_ids      = [aws_security_group.app.id]
  associate_public_ip_address = true
  
  root_block_device {
    volume_size = 50
    volume_type = "gp3"
  }

  user_data = file("user-data.sh")

  tags = {
    Name = "video-downloader-app"
  }
}

# Elastic IP
resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = {
    Name = "video-downloader-eip"
  }
}

# S3 Bucket for Downloads
resource "aws_s3_bucket" "downloads" {
  bucket = "video-downloader-downloads-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "video-downloader-downloads"
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket_lifecycle_configuration" "downloads" {
  bucket = aws_s3_bucket.downloads.id

  rule {
    id     = "delete-old-files"
    status = "Enabled"

    expiration {
      days = 1
    }
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "app" {
  name              = "/aws/video-downloader"
  retention_in_days = 7

  tags = {
    Name = "video-downloader-logs"
  }
}

# Outputs
output "instance_public_ip" {
  value = aws_eip.app.public_ip
}

output "s3_bucket_name" {
  value = aws_s3_bucket.downloads.id
}
```

### Deploy with Terraform

```bash
# Initialize
terraform init

# Plan
terraform plan

# Apply
terraform apply

# Get outputs
terraform output instance_public_ip
```

---

## 💰 Cost Estimation

### EC2 Option
| Resource | Specs | Monthly Cost |
|----------|-------|--------------|
| EC2 t3.medium | 2 vCPU, 4GB RAM | $30 |
| EBS 50GB gp3 | Storage | $4 |
| Data Transfer | 100GB out | $9 |
| Elastic IP | 1 IP | $0 |
| **Total** | | **~$43/month** |

### ECS Fargate Option
| Resource | Specs | Monthly Cost |
|----------|-------|--------------|
| Fargate Tasks | 2 tasks, 2 vCPU, 4GB | $60 |
| ALB | Load balancer | $16 |
| Data Transfer | 100GB out | $9 |
| **Total** | | **~$85/month** |

### With S3 Storage
| Resource | Usage | Monthly Cost |
|----------|-------|--------------|
| S3 Storage | 100GB | $2.30 |
| S3 Requests | 100K PUT, 1M GET | $0.50 |
| **Additional** | | **~$3/month** |

---

## 🔧 Post-Deployment Setup

### 1. Configure S3 for Downloads

```python
# Update backend/app/config.py
import boto3

S3_BUCKET = os.getenv('S3_BUCKET')
s3_client = boto3.client('s3')

def upload_to_s3(local_file: str, s3_key: str):
    s3_client.upload_file(local_file, S3_BUCKET, s3_key)
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': s3_key},
        ExpiresIn=3600
    )
```

### 2. Setup CloudWatch Alarms

```bash
# CPU Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name video-downloader-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# Disk Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name video-downloader-low-disk \
  --alarm-description "Alert when disk usage exceeds 80%" \
  --metric-name DiskSpaceUtilization \
  --namespace CWAgent \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

### 3. Setup Auto-Scaling (ECS)

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/video-downloader-cluster/video-downloader-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/video-downloader-cluster/video-downloader-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

---

## 🚀 Quick Deploy Script

```bash
#!/bin/bash
# deploy-aws.sh

set -e

echo "🚀 Deploying Video Downloader to AWS..."

# Variables
REGION="us-east-1"
INSTANCE_TYPE="t3.medium"
KEY_NAME="your-key-pair"

# Create EC2 instance
echo "📦 Creating EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --security-group-ids sg-xxx \
  --subnet-id subnet-xxx \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=video-downloader}]' \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "✅ Instance created: $INSTANCE_ID"

# Wait for instance
echo "⏳ Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "✅ Instance running at: $PUBLIC_IP"

# Wait for SSH
echo "⏳ Waiting for SSH..."
sleep 30

# Deploy application
echo "📦 Deploying application..."
ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP << 'EOF'
  # Install Docker
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker ubuntu
  
  # Clone and deploy
  git clone https://github.com/your-repo/video-downloader.git
  cd video-downloader
  docker-compose -f docker-compose.prod.yml up -d --build
EOF

echo "✅ Deployment complete!"
echo "🌐 Access your app at: http://$PUBLIC_IP"
```

---

## 📚 Additional Resources

- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Cost Calculator](https://calculator.aws/)

---

**Ready to deploy to AWS!** 🎉
