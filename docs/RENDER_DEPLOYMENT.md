# Deploy Backend to Render

**Platform**: Render  
**Cost**: Free tier available (with limitations)  
**Best for**: Side projects, demos, quick deployment

---

## Prerequisites

- Render account (free, no credit card required)
- GitHub repository with backend code
- Supabase database (already configured)

---

## Step-by-Step Deployment

### Step 1: Create Render Account

1. Go to: https://render.com/register
2. Click "Sign up with GitHub"
3. Authorize Render
4. Complete account setup (no credit card needed)

### Step 2: Create New Web Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Select "Multi-Channal-Customer-Support-Sirvice"
4. Click "Connect"

### Step 3: Configure Service

Fill in the configuration:

**Basic Settings:**
- **Name**: `ai-support-backend`
- **Region**: Choose closest to your users
- **Branch**: `main`
- **Root Directory**: `backend`
- **Runtime**: Docker
- **Instance Type**: Free

**Build Settings:**
- **Dockerfile Path**: `backend/Dockerfile`
- Render will auto-detect the Dockerfile

**Advanced Settings:**
- **Auto-Deploy**: Yes (deploy on every push)
- **Health Check Path**: `/health`

### Step 4: Add Environment Variables

Scroll to "Environment Variables" section and add:

```
# Copy these from your .env file - DO NOT commit actual values to git
DATABASE_URL=<your-supabase-database-url>

OPENROUTER_API_KEY=<your-openrouter-api-key>

META_WHATSAPP_TOKEN=<your-meta-whatsapp-token>

META_WHATSAPP_PHONE_ID=<your-whatsapp-phone-id>

WHATSAPP_APP_SECRET=<your-whatsapp-app-secret>

GMAIL_CLIENT_ID=<your-gmail-client-id>

GMAIL_CLIENT_SECRET=<your-gmail-client-secret>

GMAIL_REFRESH_TOKEN=<your-gmail-refresh-token>

SUPPORT_EMAIL=<your-support-email>

KAFKA_BOOTSTRAP_SERVERS=localhost:9092

HUGGINGFACE_API_KEY=<your-huggingface-api-key>

SECRET_KEY=<generate-random-secret-key>

CORS_ORIGINS=https://your-frontend-url.vercel.app

ENVIRONMENT=production

LOG_LEVEL=INFO

PORT=8000
```

**Note**: Replace all `<placeholder>` values with your actual credentials from your local `.env` file.

**Important**: Update `CORS_ORIGINS` with your actual Vercel frontend URL after deployment.

### Step 5: Deploy

1. Click "Create Web Service"
2. Render will start building
3. Build takes 5-10 minutes
4. Watch build logs in real-time

### Step 6: Get Your Backend URL

After deployment completes:
- Your backend URL: `https://ai-support-backend.onrender.com`
- Copy this URL for frontend configuration

### Step 7: Test Deployment

```bash
# Test health endpoint
curl https://ai-support-backend.onrender.com/health

# Expected response:
# {"status":"healthy","channels":{...},"services":{...}}
```

### Step 8: Update Frontend

1. Go to Vercel dashboard
2. Open your frontend project
3. Go to Settings → Environment Variables
4. Update `BACKEND_URL`:
   ```
   BACKEND_URL=https://ai-support-backend.onrender.com
   ```
5. Redeploy frontend

---

## Add Worker Service (Optional)

For background processing:

1. Click "New +" → "Background Worker"
2. Connect same GitHub repository
3. Configure:
   - **Name**: `ai-support-worker`
   - **Root Directory**: `backend`
   - **Dockerfile Path**: `backend/Dockerfile.worker`
4. Add same environment variables
5. Deploy

---

## Important: Free Tier Limitations

### Spin Down After Inactivity

⚠️ **Critical**: Free tier services spin down after 15 minutes of inactivity

**Impact:**
- First request after spin down takes 30-60 seconds (cold start)
- Subsequent requests are fast
- Not suitable for production with strict SLA requirements

**Workaround:**
- Upgrade to paid tier ($7/month) for always-on service
- Use external monitoring to ping service every 10 minutes
- Accept cold starts for demo/development

### Resource Limits

- **RAM**: 512 MB
- **CPU**: Shared
- **Build time**: 15 minutes max
- **Bandwidth**: 100 GB/month

---

## Monitoring

### View Logs

1. Go to your service dashboard
2. Click "Logs" tab
3. View real-time logs
4. Filter by log level

### Metrics

1. Click "Metrics" tab
2. View:
   - Response times
   - Memory usage
   - CPU usage
   - Request count

### Events

1. Click "Events" tab
2. View deployment history
3. See service restarts
4. Monitor health checks

---

## Troubleshooting

### Build Fails

**Issue**: Dockerfile not found
**Solution**: Verify Root Directory is set to `backend`

**Issue**: Build timeout (>15 min)
**Solution**: Optimize Dockerfile, use smaller base image

**Issue**: Out of memory during build
**Solution**: Reduce dependencies or upgrade to paid tier

### Runtime Errors

**Issue**: Service keeps restarting
**Solution**: Check logs for errors, verify environment variables

**Issue**: Database connection fails
**Solution**: Verify DATABASE_URL is correct

**Issue**: Port binding error
**Solution**: Ensure app listens on `0.0.0.0:$PORT`

### Cold Start Issues

**Issue**: First request times out
**Solution**: 
- Increase health check timeout
- Optimize startup time
- Consider paid tier for always-on

**Issue**: Frequent spin downs
**Solution**:
- Upgrade to paid tier
- Set up external monitoring to keep service warm

### CORS Errors

**Issue**: Frontend can't connect
**Solution**: Update CORS_ORIGINS with correct Vercel URL

---

## Keeping Service Warm (Free Tier Hack)

To prevent spin down, ping your service every 10 minutes:

### Option 1: UptimeRobot (Free)

1. Sign up at: https://uptimerobot.com
2. Add new monitor:
   - **Type**: HTTP(s)
   - **URL**: `https://ai-support-backend.onrender.com/health`
   - **Interval**: 5 minutes
3. Service stays warm

### Option 2: Cron Job

Use a free cron service:
1. https://cron-job.org
2. Add job to ping `/health` every 10 minutes

**Note**: This uses bandwidth but keeps service responsive

---

## Upgrading to Paid Tier

Benefits of paid tier ($7/month):
- ✅ Always-on (no spin down)
- ✅ More RAM (1GB+)
- ✅ Faster CPU
- ✅ Custom domains
- ✅ Priority support

To upgrade:
1. Go to service settings
2. Click "Upgrade"
3. Select "Starter" plan
4. Add payment method

---

## Custom Domain (Optional)

1. Go to service settings
2. Click "Custom Domain"
3. Add your domain
4. Update DNS records as instructed
5. SSL certificate auto-generated

---

## Deployment Best Practices

### For Free Tier

- ✅ Use for demos and development
- ✅ Set up UptimeRobot to keep warm
- ✅ Optimize Docker image size
- ✅ Monitor bandwidth usage
- ⚠️ Don't use for production with SLA requirements

### For Paid Tier

- ✅ Suitable for production
- ✅ Enable auto-scaling
- ✅ Set up monitoring alerts
- ✅ Configure custom domain
- ✅ Enable automatic backups

---

## Next Steps

After deployment:
1. ✅ Test all API endpoints
2. ✅ Submit test support request
3. ✅ Verify worker processing (if deployed)
4. ✅ Set up UptimeRobot (free tier)
5. ✅ Monitor cold start times
6. ✅ Consider upgrading if needed

---

## Comparison: Free vs Paid

| Feature | Free | Paid ($7/mo) |
|---------|------|--------------|
| Spin down | Yes (15 min) | No |
| RAM | 512 MB | 1 GB+ |
| CPU | Shared | Dedicated |
| Cold start | 30-60s | N/A |
| Custom domain | No | Yes |
| Support | Community | Priority |

---

**Deployment Complete!** 🎉

Your AI Customer Support Agent is now live on Render.

**Remember**: Free tier spins down after 15 minutes. Set up UptimeRobot to keep it warm!
