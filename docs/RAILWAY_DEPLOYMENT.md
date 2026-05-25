# Deploy Backend to Railway

**Platform**: Railway  
**Cost**: $5 free credit/month (requires credit card)  
**Best for**: Professional projects, easy deployment

---

## Prerequisites

- Railway account (requires credit card for free tier)
- GitHub repository with backend code
- Supabase database (already configured)

---

## Step-by-Step Deployment

### Step 1: Create Railway Account

1. Go to: https://railway.app
2. Click "Login" → "Login with GitHub"
3. Authorize Railway
4. Add credit card (required even for free tier)
5. Get $5 free credit monthly

### Step 2: Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose "Multi-Channal-Customer-Support-Sirvice"
4. Railway will detect the repository

### Step 3: Configure Backend Service

1. Railway creates a service automatically
2. Click on the service
3. Go to "Settings"
4. Configure:
   - **Name**: `backend`
   - **Root Directory**: `/backend`
   - **Build Command**: (leave empty, uses Dockerfile)
   - **Start Command**: (leave empty, uses Dockerfile CMD)

### Step 4: Add Environment Variables

1. Go to "Variables" tab
2. Click "Raw Editor"
3. Paste all variables:

```env
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

4. Click "Save"

**Important**: Update `CORS_ORIGINS` with your actual Vercel frontend URL.

### Step 5: Configure Dockerfile

Railway will automatically detect and use `backend/Dockerfile`.

If needed, create `railway.toml` in project root:

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
startCommand = "uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### Step 6: Deploy

1. Railway automatically deploys on push
2. Watch build logs in the deployment tab
3. Build takes 3-5 minutes
4. Service will be live when build completes

### Step 7: Get Your Backend URL

1. Go to "Settings" tab
2. Scroll to "Domains"
3. Click "Generate Domain"
4. Your backend URL: `https://your-service.up.railway.app`

### Step 8: Test Deployment

```bash
# Test health endpoint
curl https://your-service.up.railway.app/health

# Expected response:
# {"status":"healthy","channels":{...},"services":{...}}
```

### Step 9: Update Frontend

1. Go to Vercel dashboard
2. Open your frontend project
3. Go to Settings → Environment Variables
4. Update `BACKEND_URL`:
   ```
   BACKEND_URL=https://your-service.up.railway.app
   ```
5. Redeploy frontend

---

## Add Worker Service (Optional)

For background processing:

1. Click "New" → "Empty Service"
2. Name it `worker`
3. Link to same GitHub repo
4. Settings:
   - **Root Directory**: `/backend`
   - **Dockerfile Path**: `backend/Dockerfile.worker`
5. Add same environment variables
6. Deploy

---

## Monitoring

### View Logs

1. Click on service
2. Go to "Deployments" tab
3. Click on latest deployment
4. View real-time logs

### Metrics

1. Go to "Metrics" tab
2. View:
   - CPU usage
   - Memory usage
   - Network traffic
   - Request count

### Alerts

1. Go to "Settings" → "Alerts"
2. Configure alerts for:
   - High CPU usage
   - High memory usage
   - Deployment failures

---

## Troubleshooting

### Build Fails

**Issue**: Dockerfile not found
**Solution**: Verify `dockerfilePath` in railway.toml

**Issue**: Build timeout
**Solution**: Optimize Dockerfile (use multi-stage builds)

### Runtime Errors

**Issue**: Port binding error
**Solution**: Use `$PORT` environment variable

**Issue**: Database connection fails
**Solution**: Check DATABASE_URL format

### CORS Errors

**Issue**: Frontend can't connect
**Solution**: Update CORS_ORIGINS with correct frontend URL

---

## Cost Management

### Free Tier

- $5 credit per month
- ~500 hours of usage
- Shared CPU
- 512MB RAM

### Monitor Usage

1. Go to "Usage" tab
2. View current month's usage
3. Set up billing alerts

### Optimize Costs

- Use sleep mode for non-production
- Optimize Docker image size
- Monitor resource usage
- Scale down when not needed

---

## Upgrading

To upgrade:
1. Go to "Settings" → "Plan"
2. Choose paid plan (starts at $5/month)
3. Get more resources and features

---

## Next Steps

After deployment:
1. ✅ Test all API endpoints
2. ✅ Submit test support request
3. ✅ Verify worker processing
4. ✅ Set up monitoring alerts
5. ✅ Configure custom domain (optional)

---

**Deployment Complete!** 🎉

Your AI Customer Support Agent is now live on Railway.
