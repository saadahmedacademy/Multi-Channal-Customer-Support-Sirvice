# Deploy Backend to Hugging Face Spaces

**Platform**: Hugging Face Spaces  
**Cost**: FREE (no credit card required)  
**Best for**: AI/ML applications, permanent free hosting

---

## Prerequisites

- Hugging Face account (free)
- GitHub repository with backend code
- Supabase database (already configured)

---

## Step-by-Step Deployment

### Step 1: Create Hugging Face Account

1. Go to: https://huggingface.co/join
2. Sign up with email or GitHub
3. Verify your email

### Step 2: Create New Space

1. Go to: https://huggingface.co/new-space
2. Fill in details:
   - **Space name**: `ai-support-backend`
   - **License**: MIT
   - **Select SDK**: Docker
   - **Space hardware**: CPU basic (free)
   - **Visibility**: Public (or Private if you prefer)

3. Click "Create Space"

### Step 3: Configure Space

You'll see a repository page. We need to add files:

#### Option A: Link to GitHub (Recommended)

1. In your Space settings, go to "Files and versions"
2. Click "Connect to GitHub"
3. Select your repository: `Multi-Channal-Customer-Support-Sirvice`
4. Set path: `/backend`
5. Enable auto-sync

#### Option B: Manual Upload

1. Clone the Space repository:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/ai-support-backend
   cd ai-support-backend
   ```

2. Copy backend files:
   ```bash
   cp -r /path/to/your/backend/* .
   cp -r /path/to/your/database .
   cp -r /path/to/your/context .
   cp /path/to/your/alembic.ini .
   ```

3. Create `Dockerfile` (use existing backend/Dockerfile)

4. Create `README.md` with Space configuration:
   ```yaml
   ---
   title: AI Support Backend
   emoji: 🤖
   colorFrom: blue
   colorTo: purple
   sdk: docker
   pinned: false
   ---
   ```

### Step 4: Add Environment Variables (Secrets)

1. Go to Space Settings → Repository secrets
2. Add the following secrets:

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
```

**Note**: Replace all `<placeholder>` values with your actual credentials from your local `.env` file.

**Important**: Update `CORS_ORIGINS` with your actual Vercel frontend URL after deployment.

### Step 5: Deploy

1. Commit and push files:
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push
   ```

2. Hugging Face will automatically build and deploy
3. Build takes 5-10 minutes
4. Watch build logs in the Space page

### Step 6: Get Your Backend URL

Your backend will be available at:
```
https://YOUR_USERNAME-ai-support-backend.hf.space
```

### Step 7: Test Deployment

```bash
# Test health endpoint
curl https://YOUR_USERNAME-ai-support-backend.hf.space/health

# Expected response:
# {"status":"healthy","channels":{...},"services":{...}}
```

### Step 8: Update Frontend

1. Go to Vercel dashboard
2. Open your frontend project
3. Go to Settings → Environment Variables
4. Update `BACKEND_URL`:
   ```
   BACKEND_URL=https://YOUR_USERNAME-ai-support-backend.hf.space
   ```
5. Redeploy frontend

---

## Troubleshooting

### Build Fails

**Issue**: Docker build fails
**Solution**: Check Dockerfile path and syntax

**Issue**: Missing dependencies
**Solution**: Ensure requirements.txt includes all packages

### Runtime Errors

**Issue**: Database connection fails
**Solution**: Verify DATABASE_URL secret is correct

**Issue**: CORS errors
**Solution**: Update CORS_ORIGINS with correct frontend URL

### Performance Issues

**Issue**: Slow response times
**Solution**: Upgrade to better hardware (paid tier)

**Issue**: Cold starts
**Solution**: Keep Space active or upgrade to persistent hardware

---

## Limitations (Free Tier)

- CPU basic hardware (2 vCPU, 16GB RAM)
- May sleep after inactivity
- Community support only
- No SLA guarantees

---

## Upgrading

To upgrade hardware:
1. Go to Space Settings
2. Select "Space hardware"
3. Choose paid tier (starts at $0.60/hour)

---

## Next Steps

After deployment:
1. ✅ Test all API endpoints
2. ✅ Submit test support request
3. ✅ Verify worker processing
4. ✅ Check email/WhatsApp integration
5. ✅ Monitor logs for errors

---

**Deployment Complete!** 🎉

Your AI Customer Support Agent is now live on Hugging Face Spaces.
