# Render.com Quick Start Guide

Deploy your video downloader to Render in 5 minutes!

## Method 1: One-Click Blueprint Deploy (Easiest)

1. **Push render.yaml to GitHub:**
   ```bash
   git add render.yaml RENDER_DEPLOYMENT.md RENDER_QUICKSTART.md
   git commit -m "Add Render deployment config"
   git push origin main
   ```

2. **Deploy on Render:**
   - Go to https://dashboard.render.com/
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Select your `video-downloader` repository
   - Click "Apply"
   - Wait 5-10 minutes for deployment

3. **Update URLs:**
   After deployment, you'll get URLs like:
   - Backend: `https://video-downloader-api.onrender.com`
   - Frontend: `https://video-downloader-web.onrender.com`

   Update environment variables:
   - Backend → Environment → `BACKEND_CORS_ORIGINS` = `https://video-downloader-web.onrender.com`
   - Frontend → Environment → `VITE_API_URL` = `https://video-downloader-api.onrender.com`

4. **Done!** Visit your frontend URL and start downloading videos! 🎉

## Method 2: Manual Deploy

### Step 1: Deploy Backend

1. Dashboard → "New" → "Web Service"
2. Connect repository
3. Settings:
   - **Name:** `video-downloader-api`
   - **Environment:** Docker
   - **Dockerfile Path:** `./Dockerfile.prod`
   - **Plan:** Free
4. Add environment variable:
   ```
   BACKEND_CORS_ORIGINS=https://YOUR-FRONTEND-URL.onrender.com
   ```
5. Click "Create Web Service"

**Note:** Free tier doesn't support persistent disks. The app uses `/tmp` for temporary storage, which is perfect for a video downloader since files are served immediately.

### Step 2: Deploy Frontend

1. Dashboard → "New" → "Static Site"
2. Connect repository
3. Settings:
   - **Name:** `video-downloader-web`
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/dist`
4. Add environment variable:
   ```
   VITE_API_URL=https://YOUR-BACKEND-URL.onrender.com
   ```
5. Add redirect (Redirects/Rewrites tab):
   - **Source:** `/*`
   - **Destination:** `/index.html`
   - **Action:** Rewrite
6. Click "Create Static Site"

### Step 3: Update CORS

Go back to backend service and update `BACKEND_CORS_ORIGINS` with the actual frontend URL.

## Important Notes

### Free Tier Limitations:
- Services spin down after 15 minutes of inactivity
- First request after spin down takes 30-60 seconds (cold start)
- 512 MB RAM per service
- No persistent disk storage (uses /tmp - files deleted on restart)
- This is fine for video downloads since files are served immediately

### Recommended for Production:
- Upgrade backend to Starter plan ($7/month) for:
  - No spin down
  - 2 GB RAM
  - Better performance

### Keep Service Warm (Optional):
Use a service like UptimeRobot to ping your backend every 14 minutes:
- URL: `https://video-downloader-api.onrender.com/health`
- Interval: 14 minutes

## Testing Your Deployment

1. Visit your frontend URL
2. Try these tests:
   - Extract video from a simple website
   - Download a YouTube video (use 480p or 720p)
   - Download Instagram video
   - Convert video to MP3

## Troubleshooting

### Service Won't Start:
- Check logs in Render dashboard
- Verify Dockerfile.prod exists
- Check environment variables

### CORS Errors:
- Verify `BACKEND_CORS_ORIGINS` matches your frontend URL exactly
- No trailing slash in URL
- Use HTTPS (not HTTP)

### Frontend Shows "Network Error":
- Verify `VITE_API_URL` points to your backend URL
- Check backend is running (visit `/health` endpoint)
- Check browser console for errors

### Out of Memory:
- Free tier has 512 MB RAM
- Large videos may fail
- Upgrade to Starter plan for 2 GB RAM

## Monitoring

### View Logs:
1. Go to service in dashboard
2. Click "Logs" tab
3. Real-time logs appear

### Check Health:
Visit: `https://your-backend.onrender.com/health`

Should return: `{"status": "healthy"}`

## Updating Your App

Just push to GitHub:
```bash
git add .
git commit -m "Update feature"
git push origin main
```

Render automatically rebuilds and deploys! 🚀

## Cost

- **Free Tier:** $0/month (with spin down)
- **Starter:** $7/month (no spin down, 2 GB RAM)
- **Professional:** $25/month (4 GB RAM, priority support)

## Support

- Full guide: See `RENDER_DEPLOYMENT.md`
- Render docs: https://render.com/docs
- Issues: Check GitHub repository issues

---

**That's it!** Your video downloader is now live on Render! 🎊
