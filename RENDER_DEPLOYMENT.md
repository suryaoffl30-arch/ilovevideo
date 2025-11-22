# Render.com Deployment Guide

Complete guide for deploying the Video Downloader to Render.com with automatic deployments from GitHub.

## Prerequisites

- GitHub account with your repository pushed
- Render.com account (free tier available)
- Repository: https://github.com/YOUR_USERNAME/video-downloader

## Deployment Options

### Option 1: Blueprint (Automated - Recommended)

This uses the `render.yaml` file for automatic setup.

1. **Connect Repository:**
   - Go to https://dashboard.render.com/
   - Click "New" → "Blueprint"
   - Connect your GitHub account
   - Select your `video-downloader` repository
   - Click "Connect"

2. **Configure Services:**
   - Render will read `render.yaml` and create:
     - Backend API (Docker service)
     - Frontend (Static site)
     - Redis cache
   - Review the services and click "Apply"

3. **Update Environment Variables:**
   - Go to Backend API service settings
   - Update `BACKEND_CORS_ORIGINS` with your frontend URL
   - Go to Frontend service settings
   - Update `VITE_API_URL` with your backend URL

4. **Deploy:**
   - Services will auto-deploy
   - Wait 5-10 minutes for initial build
   - Access your app at the provided URLs

### Option 2: Manual Setup

#### Step 1: Deploy Backend API

1. **Create Web Service:**
   - Dashboard → "New" → "Web Service"
   - Connect your repository
   - Configure:
     - **Name:** `video-downloader-api`
     - **Region:** Oregon (or closest to you)
     - **Branch:** `main`
     - **Root Directory:** Leave empty
     - **Environment:** Docker
     - **Dockerfile Path:** `./Dockerfile.prod`
     - **Plan:** Free

2. **Add Environment Variables:**
   ```
   ENVIRONMENT=production
   BACKEND_CORS_ORIGINS=https://YOUR-FRONTEND-URL.onrender.com
   MAX_UPLOAD_SIZE=524288000
   DOWNLOAD_TIMEOUT=300
   PLAYWRIGHT_TIMEOUT=60000
   ```

3. **Disk Storage (Optional - Paid Plans Only):**
   - Free tier uses temporary storage (/tmp)
   - Files are deleted on service restart
   - For persistent storage, upgrade to Starter plan and add disk:
     - **Name:** downloads
     - **Mount Path:** `/app/downloads`
     - **Size:** 1 GB+

4. **Health Check:**
   - Path: `/health`
   - This ensures the service restarts if unhealthy

#### Step 2: Deploy Redis (Optional but Recommended)

1. **Create Redis:**
   - Dashboard → "New" → "Redis"
   - Configure:
     - **Name:** `video-downloader-redis`
     - **Plan:** Free (25 MB)
     - **Max Memory Policy:** allkeys-lru

2. **Connect to Backend:**
   - Copy the Internal Redis URL
   - Add to backend environment variables:
     ```
     REDIS_URL=redis://...
     ```

#### Step 3: Deploy Frontend

1. **Create Static Site:**
   - Dashboard → "New" → "Static Site"
   - Connect your repository
   - Configure:
     - **Name:** `video-downloader-web`
     - **Branch:** `main`
     - **Root Directory:** Leave empty
     - **Build Command:** `cd frontend && npm install && npm run build`
     - **Publish Directory:** `frontend/dist`

2. **Add Environment Variable:**
   ```
   VITE_API_URL=https://YOUR-BACKEND-URL.onrender.com
   ```

3. **Configure Redirects:**
   - Go to "Redirects/Rewrites" tab
   - Add rewrite rule:
     - **Source:** `/*`
     - **Destination:** `/index.html`
     - **Action:** Rewrite

#### Step 4: Update CORS

1. Go to backend service
2. Update `BACKEND_CORS_ORIGINS` with actual frontend URL
3. Redeploy backend

## Post-Deployment Configuration

### 1. Update Frontend API URL

If you deployed manually, update the frontend environment variable:

```bash
# In Render dashboard → Frontend service → Environment
VITE_API_URL=https://video-downloader-api.onrender.com
```

### 2. Update Backend CORS

```bash
# In Render dashboard → Backend service → Environment
BACKEND_CORS_ORIGINS=https://video-downloader-web.onrender.com
```

### 3. Test the Deployment

1. Visit your frontend URL
2. Try extracting a video from a simple site
3. Test YouTube download
4. Check logs in Render dashboard if issues occur

## Free Tier Limitations

### Render Free Tier Includes:
- ✅ 750 hours/month of runtime (per service)
- ✅ Automatic HTTPS
- ✅ Auto-deploy from GitHub
- ✅ Temporary storage (/tmp directory)
- ✅ 25 MB Redis

### Limitations:
- ⚠️ Services spin down after 15 minutes of inactivity
- ⚠️ Cold start takes 30-60 seconds
- ⚠️ 512 MB RAM per service
- ⚠️ Shared CPU
- ⚠️ **No persistent disk storage** (files deleted on restart)
- ⚠️ No custom domains on free tier

### Important: File Storage on Free Tier
- Downloaded files are stored in `/tmp` (temporary storage)
- Files are automatically deleted when service restarts or spins down
- This works fine for a video downloader since files are immediately served to users
- For persistent storage, upgrade to Starter plan ($7/month) which includes disk storage

### Workarounds:

**1. Keep Service Warm (Optional):**
Create a cron job to ping your service every 14 minutes:

```bash
# Use a service like cron-job.org or UptimeRobot
# Ping: https://video-downloader-api.onrender.com/health
# Interval: Every 14 minutes
```

**2. Optimize for Cold Starts:**
The Dockerfile.prod is already optimized with:
- Multi-stage builds
- Minimal base images
- Pre-installed dependencies

## Monitoring & Logs

### View Logs:
1. Go to your service in Render dashboard
2. Click "Logs" tab
3. Real-time logs appear here

### Common Issues:

**Service Won't Start:**
```bash
# Check logs for:
- Port binding errors (should use PORT env var)
- Missing dependencies
- Playwright installation issues
```

**CORS Errors:**
```bash
# Verify BACKEND_CORS_ORIGINS includes your frontend URL
# Format: https://your-frontend.onrender.com (no trailing slash)
```

**Out of Memory:**
```bash
# Free tier has 512 MB RAM
# Large video processing may fail
# Consider upgrading to Starter plan ($7/month) for 2 GB RAM
```

**Disk Full:**
```bash
# Free tier has 1 GB disk
# Downloads are cleaned up automatically
# Check cleanup logic in backend/app/main.py
```

## Upgrading from Free Tier

If you need more resources:

### Starter Plan ($7/month per service):
- 2 GB RAM
- No spin down
- Faster CPU
- 10 GB disk storage

### To Upgrade:
1. Go to service settings
2. Click "Change Plan"
3. Select "Starter"
4. Confirm billing

## Custom Domain (Paid Plans Only)

1. Go to service settings
2. Click "Custom Domain"
3. Add your domain
4. Update DNS records as shown
5. Wait for SSL certificate (automatic)

## Automatic Deployments

Render automatically deploys when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push origin main

# Render automatically:
# 1. Detects the push
# 2. Builds new Docker image
# 3. Deploys with zero downtime
# 4. Sends notification
```

### Disable Auto-Deploy:
1. Go to service settings
2. Toggle "Auto-Deploy" off
3. Deploy manually from dashboard

## Environment-Specific Builds

### Production Environment Variables:

```bash
# Backend
ENVIRONMENT=production
BACKEND_CORS_ORIGINS=https://your-frontend.onrender.com
MAX_UPLOAD_SIZE=524288000
DOWNLOAD_TIMEOUT=300
PLAYWRIGHT_TIMEOUT=60000
LOG_LEVEL=INFO

# Frontend
VITE_API_URL=https://your-backend.onrender.com
```

## Troubleshooting

### 1. Build Fails

```bash
# Check build logs
# Common issues:
- npm install fails → Check package.json
- Docker build fails → Check Dockerfile.prod
- Out of memory → Upgrade plan
```

### 2. Service Crashes

```bash
# Check runtime logs
# Common issues:
- Port not set correctly (use process.env.PORT)
- Missing environment variables
- Playwright browser crashes (needs more RAM)
```

### 3. Slow Performance

```bash
# Free tier limitations:
- Shared CPU
- 512 MB RAM
- Cold starts

# Solutions:
- Upgrade to Starter plan
- Optimize code
- Use Redis caching
- Keep service warm with pings
```

### 4. CORS Issues

```bash
# Verify:
1. Backend CORS includes frontend URL
2. Frontend API URL is correct
3. No trailing slashes in URLs
4. HTTPS is used (not HTTP)
```

## Cost Estimation

### Free Tier (Current Setup):
- Backend: Free (with spin down)
- Frontend: Free
- Redis: Free (25 MB)
- **Total: $0/month**

### Starter Tier (Recommended for Production):
- Backend: $7/month (2 GB RAM, no spin down)
- Frontend: Free
- Redis: Free or $10/month (256 MB)
- **Total: $7-17/month**

### Professional Tier:
- Backend: $25/month (4 GB RAM)
- Frontend: Free
- Redis: $25/month (1 GB)
- **Total: $25-50/month**

## Security Best Practices

1. **Environment Variables:**
   - Never commit secrets to Git
   - Use Render's environment variables
   - Rotate API keys regularly

2. **CORS Configuration:**
   - Only allow your frontend domain
   - Don't use wildcards in production

3. **Rate Limiting:**
   - Already configured in nginx.prod.conf
   - Adjust limits based on usage

4. **HTTPS:**
   - Automatic with Render
   - Always use HTTPS URLs

## Backup & Recovery

### Database Backups:
- Redis data is ephemeral (cache only)
- No persistent data to backup

### Code Backups:
- GitHub is your source of truth
- Render rebuilds from Git on deploy

### Download Files:
- Temporary storage only
- Files auto-delete after download
- No backup needed

## Support & Resources

- **Render Docs:** https://render.com/docs
- **Render Status:** https://status.render.com/
- **Community:** https://community.render.com/
- **Support:** support@render.com (paid plans)

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test all features
3. ✅ Monitor logs for errors
4. ✅ Set up uptime monitoring
5. ✅ Consider upgrading if needed
6. ✅ Add custom domain (optional)
7. ✅ Share your app!

Your video downloader is now live on Render! 🚀
