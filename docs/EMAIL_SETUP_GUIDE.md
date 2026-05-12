# 📧 Email Setup Guide - Complete Manual Instructions

This guide walks you through setting up email receiving for your AI Support Agent step-by-step.

---

## Quick Start (Choose One Method)

| Method | Difficulty | Setup Time | Best For |
|--------|-----------|------------|----------|
| **Method 1: Gmail Polling Script** | ⭐ Easy | 15 minutes | Development & Testing |
| **Method 2: Email Forwarding Service** | ⭐⭐ Medium | 30 minutes | Production without coding |
| **Method 3: Gmail Pub/Sub Webhook** | ⭐⭐⭐ Advanced | 1 hour | Production (Recommended) |

---

## Method 1: Gmail Polling Script (Easiest)

### Step 1: Get Gmail OAuth Token

#### 1.1 Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click **Select a project** → **New Project**
3. Name it "AI Support Agent"
4. Click **Create**

#### 1.2 Enable Gmail API

1. In your new project, go to **APIs & Services** → **Library**
2. Search for "Gmail API"
3. Click **Enable**

#### 1.3 Create OAuth Credentials

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** user type
3. Fill in:
   - App name: "AI Support Agent"
   - User support email: Your email
   - Developer contact email: Your email
4. Click **Save and Continue**
5. Skip scopes (we'll add them manually)
6. Add test users: Add your Gmail address
7. Click **Save and Continue** → **Back to Dashboard**

#### 1.4 Create OAuth Client ID

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: "AI Support Agent"
5. Click **Create**
6. **Download the JSON** file (save as `credentials.json`)

#### 1.5 Generate Token

Install required packages:

```bash
cd /home/saadahmed/hk-5
source .venv/bin/activate
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

Create token generation script:

```python
# save as scripts/get_gmail_token.py
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json',  # The file you downloaded
    SCOPES
)

print("\n=== Gmail OAuth Token Generator ===")
print("Opening browser for authentication...\n")

creds = flow.run_local_server(port=8080)

print("\n✓ Authentication successful!")
print(f"\nYour Access Token:\n{creds.token}")
print(f"\nYour Refresh Token:\n{creds.refresh_token}")
print("\nCopy the Access Token to your .env file as GMAIL_OAUTH_TOKEN")
```

Run it:

```bash
python scripts/get_gmail_token.py
```

A browser window will open. Login with your Gmail account and grant permissions.

**Copy the Access Token** it prints.

### Step 2: Configure Your Application

Edit your `.env` file:

```bash
nano /home/saadahmed/hk-5/.env
```

Add/update these lines:

```env
# Gmail Configuration
GMAIL_OAUTH_TOKEN=paste_your_access_token_here
SUPPORT_EMAIL=your-support-email@gmail.com
```

### Step 3: Test Email Fetching

Run the polling script:

```bash
cd /home/saadahmed/hk-5
source .venv/bin/activate

# Edit the script first to add your token
nano scripts/fetch_gmail_emails.py
# Replace "your_oauth_token_here" with your actual token

# Run the script
python scripts/fetch_gmail_emails.py
```

You should see:

```
2026-04-11 12:00:00 [INFO] Starting Gmail email fetcher...
2026-04-11 12:00:00 [INFO] Webhook URL: http://localhost:8000/webhooks/email
2026-04-11 12:00:00 [INFO] Poll interval: 60 seconds
2026-04-11 12:00:01 [INFO] Found 2 unread emails
2026-04-11 12:00:02 [INFO] Processing: Test Support from user@example.com
2026-04-11 12:00:03 [INFO] ✓ Forwarded: Test Support from user@example.com
```

### Step 4: Send Test Email

1. Send an email to your support Gmail account
2. Wait up to 60 seconds (poll interval)
3. Check your AI Support Agent logs:

```bash
sudo journalctl -u ai-support-worker -f | grep "email"
```

---

## Method 2: Email Forwarding Service (Production Alternative)

Use a service like **SendGrid Inbound Parse** or **Mailgun Routes** to receive emails and forward to your webhook.

### Using SendGrid (Free Tier: 100 emails/day)

#### Step 1: Create SendGrid Account

1. Go to https://sendgrid.com/
2. Sign up for free account
3. Verify your email

#### Step 2: Setup Inbound Parse

1. Go to **Settings** → **Inbound Parse**
2. Click **Add Host & URL**
3. Receiving Domain: Add your domain (e.g., `yourdomain.com`)
4. Destination URL: `https://your-api-domain.com/webhooks/email`
5. Check "POST the raw, full MIME message"
6. Click **Save**

#### Step 3: Configure DNS MX Records

Add MX record to your domain's DNS:

```
Type: MX
Name: yourdomain.com
Value: mx.sendgrid.net
Priority: 10
```

#### Step 4: Test

Send an email to `support@yourdomain.com` and check your webhook logs.

---

## Method 3: Gmail Pub/Sub (Production Recommended)

### Prerequisites

- Google Cloud project with billing enabled
- Gmail API enabled
- Pub/Sub API enabled

### Step 1: Enable Pub/Sub API

1. Go to https://console.cloud.google.com/
2. Navigate to **APIs & Services** → **Library**
3. Search "Cloud Pub/Sub API"
4. Click **Enable**

### Step 2: Create Pub/Sub Topic

```bash
# Install gcloud CLI if not installed
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Create topic
gcloud pubsub topics create gmail-notifications
```

### Step 3: Grant Gmail Service Account Access

```bash
# Get service account email
gcloud iam service-accounts list

# Grant Pub/Sub publisher role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
```

### Step 4: Create Push Subscription

```bash
gcloud pubsub subscriptions create gmail-webhook-sub \
  --topic=gmail-notifications \
  --push-endpoint=https://your-api-domain.com/webhooks/email \
  --ack-deadline=600
```

### Step 5: Watch Gmail Inbox

Create watch script:

```python
# scripts/watch_gmail.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
import base64

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
SERVICE_ACCOUNT_FILE = 'service-account.json'  # Download from Google Cloud

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('gmail', 'v1', credentials=credentials)

# Setup watch
request = {
    'labelIds': ['INBOX', 'UNREAD'],
    'topicName': 'projects/YOUR_PROJECT_ID/topics/gmail-notifications'
}

result = service.users().watch(userId='me', body=request).execute()
print(f"Watching Gmail inbox. History ID: {result['historyId']}")
```

---

## Testing Your Setup

### Test 1: Send Email to Support

```bash
# Send test email using curl (simulates webhook)
curl -X POST http://localhost:8000/webhooks/email \
  -H "Content-Type: application/json" \
  -d '{
    "from_email": "test@example.com",
    "from": "Test User <test@example.com>",
    "subject": "Test Support Request",
    "body": "I need help with my account. Can you assist?",
    "message_id": "test-123",
    "in_reply_to": "",
    "is_reply": false
  }'
```

Expected response:
```json
{"status": "received"}
```

### Test 2: Check Worker Logs

```bash
# Check if worker received the email
sudo journalctl -u ai-support-worker -f
```

Look for:
```
Received email from test@example.com: Test Support Request
Email message queued: test-123
Processing ticket XXXXX from email
```

### Test 3: Verify Database

```bash
psql $DATABASE_URL -c "
  SELECT t.id, t.source_channel, t.status, m.content
  FROM tickets t
  JOIN messages m ON t.conversation_id = m.conversation_id
  WHERE t.source_channel = 'email'
  ORDER BY t.created_at DESC
  LIMIT 1;
"
```

---

## Troubleshooting

### Issue: "Invalid OAuth token"

**Solution**:
```bash
# Regenerate token
python scripts/get_gmail_token.py
# Update .env with new token
```

### Issue: "No unread emails found"

**Solutions**:
1. Make sure emails are actually unread in Gmail
2. Check you're using the correct Gmail account
3. Verify OAuth scopes include `gmail.readonly`

### Issue: "Webhook returned 400/500"

**Solutions**:
```bash
# Check backend logs
sudo journalctl -u ai-support-api -n 50

# Test webhook directly
curl -X POST http://localhost:8000/webhooks/email \
  -H "Content-Type: application/json" \
  -d '{"from_email": "test@test.com", "subject": "Test", "body": "Test"}'
```

### Issue: Email not being processed by worker

**Checklist**:
- [ ] Worker service is running: `sudo systemctl status ai-support-worker`
- [ ] Redpanda is running: `docker ps | grep redpanda`
- [ ] Queue topic exists: `docker exec -it redpanda rpk topic list`
- [ ] Worker logs show processing: `sudo journalctl -u ai-support-worker -f`

---

## Auto-Start Polling Script on Boot

If using Method 1 (polling script), create a systemd service:

```bash
sudo nano /etc/systemd/system/gmail-fetcher.service
```

Content:

```ini
[Unit]
Description=Gmail Email Fetcher for AI Support
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/saadahmed/hk-5
Environment=PATH=/home/saadahmed/hk-5/.venv/bin
ExecStart=/home/saadahmed/hk-5/.venv/bin/python scripts/fetch_gmail_emails.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gmail-fetcher
sudo systemctl start gmail-fetcher
sudo systemctl status gmail-fetcher
```

---

## Next Steps

After email is working:

1. ✅ Test with real customer emails
2. ✅ Configure email signatures in responses
3. ✅ Set up email templates for common responses
4. ✅ Monitor email processing metrics
5. ✅ Configure email rate limits if needed

---

## Support

- **API Documentation**: http://localhost:8000/docs
- **Email Webhook Test**: http://localhost:8000/webhooks/email/test
- **Worker Logs**: `sudo journalctl -u ai-support-worker -f`
- **API Logs**: `sudo journalctl -u ai-support-api -f`

---

**Last Updated**: 2026-04-11  
**Difficulty**: ⭐ Easy (Method 1) to ⭐⭐⭐ Advanced (Method 3)
