# Deployment Runbook

This guide covers deploying and operating the AI Customer Support Agent in production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Worker Deployment](#worker-deployment)
7. [Redpanda Setup](#redpanda-setup)
8. [Verification](#verification)
9. [Monitoring & Alerts](#monitoring--alerts)
10. [Troubleshooting](#troubleshooting)
11. [Rollback Procedures](#rollback-procedures)
12. [Scaling Guidelines](#scaling-guidelines)

---

## Prerequisites

### Hardware Requirements
- **Minimum**: 4GB RAM, 2 CPU cores, 20GB disk
- **Recommended**: 8GB RAM, 4 CPU cores, 50GB disk
- **OS**: Linux (Ubuntu 20.04+ or equivalent)

### Software Requirements
- Python 3.11+
- Node.js 18+
- Docker (for Redpanda only)
- PostgreSQL 14+ (Supabase recommended)
- OpenSSL (for SSL certificates)

### External Services
- **Supabase Account**: Free tier available at https://supabase.com
- **AI API Key**: OpenRouter (recommended) or Google Gemini
- **WhatsApp Cloud API**: Meta Developer account (optional)
- **Gmail API**: Google Cloud project with Gmail API enabled (optional)

---

## Environment Setup

### 1. Create `.env` file

```bash
cd /path/to/project
cp .env.example .env
nano .env
```

### 2. Configure Environment Variables

```env
# ================== DATABASE ==================
# Get from: Supabase Dashboard → Settings → Database
DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_KEY=[your-anon-key]

# ================== AI API ==================
# OpenRouter (recommended - supports many models)
OPENROUTER_API_KEY=sk-or-[your-key]
AI_MODEL=meta-llama/llama-3.3-70b-instruct:free

# OR Google Gemini (alternative)
# GEMINI_API_KEY=[your-gemini-key]

# ================== WHATSAPP (Optional) ==================
# Get from: Meta Developers → Your App → WhatsApp
META_WHATSAPP_TOKEN=[your-access-token]
META_WHATSAPP_PHONE_ID=[your-phone-id]
META_WHATSAPP_BUSINESS_ID=[your-business-id]
WHATSAPP_APP_SECRET=[your-app-secret]
WHATSAPP_VERIFY_TOKEN=your-custom-verify-token

# ================== EMAIL (Optional) ==================
# Get from: Google Cloud Console → OAuth 2.0
GMAIL_OAUTH_TOKEN=[your-oauth-token]
SUPPORT_EMAIL=support@yourdomain.com

# ================== REDPANDA ==================
# Local deployment
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# ================== APPLICATION ==================
ENVIRONMENT=production
LOG_LEVEL=INFO
SECRET_KEY=[generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"]
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# ================== RATE LIMITING ==================
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### 3. Generate Secret Key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Database Setup

### 1. Connect to Supabase

```bash
# Install psql if not installed
sudo apt-get install postgresql-client

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### 2. Run Schema Migration

```bash
psql $DATABASE_URL -f database/schema.sql
```

**Expected output:**
```
CREATE EXTENSION
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
...
```

### 3. Verify Schema

```bash
psql $DATABASE_URL -c "\dt"
```

**Expected tables:**
- `customers`
- `customer_identifiers`
- `conversations`
- `messages`
- `tickets`
- `knowledge_base`

### 4. Seed Knowledge Base (Optional)

```bash
# Convert JSON to SQL inserts
python3 scripts/seed_knowledge.py $DATABASE_URL
```

---

## Backend Deployment

### 1. Install Dependencies

```bash
cd /path/to/project
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 2. Test Backend

```bash
# Run tests
pytest tests/ -v --tb=short

# Check imports
python3 -c "from backend.api.main import app; print('✓ Backend imports successful')"
```

### 3. Start Backend with systemd

Create service file:

```bash
sudo nano /etc/systemd/system/ai-support-api.service
```

Content:

```ini
[Unit]
Description=AI Customer Support API
After=network.target redpanda.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project
Environment=PATH=/path/to/project/.venv/bin
ExecStart=/path/to/project/.venv/bin/uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-support-api
sudo systemctl start ai-support-api
sudo systemctl status ai-support-api
```

### 4. Configure Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/ai-support-api
```

Content:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/ai-support-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Setup SSL (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

---

## Frontend Deployment

### 1. Build Frontend

```bash
cd /path/to/project/frontend
npm install
npm run build
```

### 2. Start with PM2

```bash
npm install -g pm2
pm2 start npm --name "ai-support-frontend" -- start
pm2 save
pm2 startup
```

### 3. Configure Nginx for Frontend

```nginx
server {
    listen 80;
    server_name support.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Worker Deployment

The worker processes messages from the queue asynchronously.

### 1. Create Worker Service

```bash
sudo nano /etc/systemd/system/ai-support-worker.service
```

Content:

```ini
[Unit]
Description=AI Support Message Worker
After=network.target redpanda.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project
Environment=PATH=/path/to/project/.venv/bin
ExecStart=/path/to/project/.venv/bin/python3 backend/worker/message_processor.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-support-worker
sudo systemctl start ai-support-worker
sudo systemctl status ai-support-worker
```

### 3. Monitor Worker Logs

```bash
sudo journalctl -u ai-support-worker -f
```

---

## Redpanda Setup

### 1. Start Redpanda

```bash
cd /path/to/project
docker-compose -f docker-compose.redpanda.yml up -d
```

### 2. Verify Redpanda

```bash
# Check container status
docker ps | grep redpanda

# Test connection
docker exec -it redpanda rpk cluster info
```

### 3. Create Topics (if not auto-created)

```bash
docker exec -it redpanda rpk topic create fte.tickets.incoming
docker exec -it redpanda rpk topic create fte.tickets.outgoing
docker exec -it redpanda rpk topic create fte.escalations
docker exec -it redpanda rpk topic create fte.metrics
docker exec -it redpanda rpk topic create fte.dlq
```

---

## Verification

### 1. Health Check

```bash
curl https://api.yourdomain.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-11T12:00:00",
  "channels": {
    "web_form": "active",
    "whatsapp": "active",
    "email": "active"
  },
  "services": {
    "database": "connected",
    "queue": "connected",
    "ai_api": "configured"
  }
}
```

### 2. Test Web Form Submission

```bash
curl -X POST https://api.yourdomain.com/support/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "subject": "Test",
    "category": "technical",
    "priority": "medium",
    "message": "This is a test message"
  }'
```

### 3. Check Worker Processing

```bash
sudo journalctl -u ai-support-worker --since "5 minutes ago" | grep "Processing"
```

### 4. Verify Database

```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM tickets;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM messages;"
```

---

## Monitoring & Alerts

### 1. Log Monitoring

```bash
# API logs
sudo journalctl -u ai-support-api -f

# Worker logs
sudo journalctl -u ai-support-worker -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### 2. Key Metrics to Monitor

- **API Response Time**: Should be <5 seconds for form submission
- **Queue Lag**: Check with `docker exec -it redpanda rpk topic describe fte.tickets.incoming`
- **Error Rate**: Monitor 5xx responses in Nginx logs
- **Worker Processing Rate**: Messages processed per minute
- **Database Connections**: Should stay under max pool size (5)

### 3. Setup Alerts

Create alert rules for:
- Worker process down
- Database connection failures
- Queue lag > 100 messages
- API error rate > 5%
- Disk space < 10%

---

## Troubleshooting

### Issue: Worker not processing messages

**Symptoms**: Messages stuck in queue, no logs

**Resolution**:
```bash
# 1. Check worker status
sudo systemctl status ai-support-worker

# 2. Check Redpanda connectivity
docker exec -it redpanda rpk topic consume fte.tickets.incoming --offset earliest

# 3. Restart worker
sudo systemctl restart ai-support-worker

# 4. Check logs
sudo journalctl -u ai-support-worker -n 100
```

### Issue: AI API errors

**Symptoms**: Fallback responses, logs show API errors

**Resolution**:
```bash
# 1. Verify API key
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/auth/key

# 2. Test AI generation
python3 -c "
from backend.worker.ai_agent import ai_agent
import asyncio
resp = asyncio.run(ai_agent.generate_response('test', 'web_form'))
print(resp)
"

# 3. Check rate limits
# OpenRouter: https://openrouter.ai/activity
```

### Issue: Database connection errors

**Symptoms**: "Database not connected" errors

**Resolution**:
```bash
# 1. Test connection
psql $DATABASE_URL -c "SELECT 1"

# 2. Check Supabase status
# https://status.supabase.com

# 3. Verify pool size not exceeded
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'postgres';"
```

### Issue: WhatsApp webhook not receiving messages

**Symptoms**: No incoming WhatsApp messages

**Resolution**:
```bash
# 1. Verify webhook URL in Meta Dashboard
# Should be: https://api.yourdomain.com/webhooks/whatsapp

# 2. Check webhook verification
curl "https://api.yourdomain.com/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test"

# 3. Check logs
sudo journalctl -u ai-support-api | grep whatsapp
```

---

## Rollback Procedures

### Roll Backend

```bash
# 1. Stop current service
sudo systemctl stop ai-support-api

# 2. Restore previous version
cd /path/to/project
git checkout <previous-commit>

# 3. Reinstall dependencies
source .venv/bin/activate
pip install -r backend/requirements.txt

# 4. Start service
sudo systemctl start ai-support-api
sudo systemctl status ai-support-api
```

### Roll Database

```bash
# 1. Check current schema
psql $DATABASE_URL -c "\dt"

# 2. Restore from backup (if needed)
# Supabase: Dashboard → Database → Backups

# 3. Verify rollback
psql $DATABASE_URL -c "SELECT COUNT(*) FROM tickets;"
```

---

## Scaling Guidelines

### Vertical Scaling (4GB → 8GB RAM)

1. **Increase Database Pool**:
   - Edit `backend/db/connection.py`
   - Change `max_size=5` to `max_size=10`

2. **Increase Redpanda Memory**:
   - Edit `docker-compose.redpanda.yml`
   - Change `--memory 512M` to `--memory 1G`

3. **Add API Workers**:
   - Change `--workers 2` to `--workers 4` in systemd service

### Horizontal Scaling

**Not recommended** per Constitution Principle II (Simplicity Over Scalability).

If absolutely necessary:
1. Use load balancer (Nginx/HAProxy)
2. Deploy multiple backend instances
3. Use shared Redpanda cluster
4. Use Supabase connection pooling

### Performance Optimization

1. **Enable HTTP/2** in Nginx
2. **Add Redis caching** for frequent queries
3. **Use CDN** for static assets
4. **Compress responses** with gzip

---

## Emergency Contacts

- **On-Call Engineer**: [Add contact]
- **Supabase Support**: https://supabase.com/support
- **OpenRouter Status**: https://status.openrouter.ai
- **Meta WhatsApp Status**: https://developers.facebook.com/status/

---

## Maintenance Schedule

### Daily
- [ ] Check error logs
- [ ] Verify queue lag is minimal
- [ ] Monitor API response times

### Weekly
- [ ] Review database growth
- [ ] Check disk space usage
- [ ] Update knowledge base if needed

### Monthly
- [ ] Review and rotate API keys
- [ ] Check for dependency updates
- [ ] Test backup restoration
- [ ] Review rate limit settings

---

**Last Updated**: 2026-04-11  
**Version**: 1.0.0  
**Maintained By**: Development Team
