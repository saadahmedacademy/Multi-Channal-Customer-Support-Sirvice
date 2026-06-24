# Remaining Security Fixes Implementation Plan

All changes are independent and can be applied in any order.

---

## M1 — Pin Redpanda image version

**File:** `docker-compose.yml:9`
```diff
-    image: docker.redpanda.com/redpandadata/redpanda:latest
+    image: docker.redpanda.com/redpandadata/redpanda:v24.2.18
```

---

## M2 + L6 — Remove Kafka port exposure + OUTSIDE listener

**File:** `docker-compose.yml:22-30`
```diff
-      - PLAINTEXT://0.0.0.0:29092,OUTSIDE://0.0.0.0:9092
-      - --advertise-kafka-addr
-      - PLAINTEXT://redpanda:29092,OUTSIDE://localhost:9092
+      - PLAINTEXT://0.0.0.0:29092
+      - --advertise-kafka-addr
+      - PLAINTEXT://redpanda:29092
       - --rpc-addr
       - 0.0.0.0:33145
       - --advertise-rpc-addr
       - redpanda:33145
-    ports:
-      - "9092:9092"
```

---

## M3 — Pin all Python dependencies to exact versions

**File:** `backend/requirements.txt`

Change all `>=` to `==` with known-good versions:

| Package | Before | After |
|---------|--------|-------|
| fastapi | `>=0.135.0` | `==0.115.6` |
| python-multipart | `>=0.0.31` | `==0.0.20` |
| pydantic | `>=2.5.3` | `==2.10.4` |
| aiohttp | `>=3.14.0` | `==3.11.12` |
| huggingface_hub | `>=0.23.0` | `==0.29.3` |
| bleach | `>=6.4.0` | `==6.2.0` |
| aiokafka | `==0.9.0` | `==0.12.0` |
| pydantic-settings | `==2.1.0` | `==2.7.1` |

---

## M5 — Improve rate limiting (X-Forwarded-For support)

**File:** `backend/api/middleware/rate_limiter.py:98`

Change:
```python
client_ip = request.client.host if request.client else "unknown"
```
To:
```python
forwarded_for = request.headers.get("X-Forwarded-For")
client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (
    request.client.host if request.client else "unknown"
)
```

---

## M6 — Replace dangerouslySetInnerHTML with next/script

**File:** `frontend/src/app/layout.tsx`

Add import at top:
```tsx
import Script from "next/script";
```

Replace:
```tsx
<head>
  <script dangerouslySetInnerHTML={{
    __html: `(function(){try{var t=localStorage.getItem('theme');if(t==='dark'||(t!=='light'&&window.matchMedia('(prefers-color-scheme:dark)').matches))document.documentElement.classList.add('dark')}catch(e){}})()`
  }} />
</head>
```
With:
```tsx
<head>
  <Script id="theme-init" strategy="beforeInteractive">
    {`(function(){try{var t=localStorage.getItem('theme');if(t==='dark'||(t!=='light'&&window.matchMedia('(prefers-color-scheme:dark)').matches))document.documentElement.classList.add('dark')}catch(e){}})()`}
  </Script>
</head>
```

---

## M7 — Remove frontend .env/.env.local from git tracking

```bash
git rm --cached frontend/.env frontend/.env.local
```
(Already in `.gitignore` — just need to unstage existing tracked copies.)

---

## M9 — Email webhook payload validation

**File:** `backend/api/routes/email.py`, inside `email_webhook_receive()`, add after `data = await request.json()`:

```python
    # Basic payload validation: require either Gmail Pub/Sub format or known fields
    if not ("message" in data and "data" in data["message"]) and not any(k in data for k in ["from_email", "from", "subject"]):
        logger.warning(f"Email webhook received unrecognized payload format")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown email payload format"
        )
```

---

## M10 — Frontend proxy rate limiting

**File:** `frontend/src/lib/api-utils.ts`

Add rate limiter utility and export it:

```typescript
const requestCounts = new Map<string, number[]>();
const RATE_LIMIT_MAX = 30;
const RATE_LIMIT_WINDOW_MS = 60_000;

export function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const timestamps = requestCounts.get(ip) || [];
  const recent = timestamps.filter(t => now - t < RATE_LIMIT_WINDOW_MS);
  if (recent.length >= RATE_LIMIT_MAX) return false;
  recent.push(now);
  requestCounts.set(ip, recent);
  return true;
}
```

Then in each proxy route file, add at the top of the handler (before any logic):

```typescript
const ip = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim()
  || request.headers.get('x-real-ip')
  || 'unknown';
if (!checkRateLimit(ip)) {
  return NextResponse.json({ detail: 'Too many requests' }, { status: 429 });
}
```

---

## L1 — Remove .env.example copy from Dockerfiles

**File:** `backend/Dockerfile:40`
```diff
- COPY --chown=appuser:appuser .env.example .env
+ # Note: Runtime env vars injected via docker-compose or container runtime
```

**File:** `backend/Dockerfile.worker:39`
```diff
- COPY --chown=appuser:appuser .env.example .env
+ # Note: Runtime env vars injected via docker-compose or container runtime
```

---

## L2 — Pin base images to SHA digests

Get digests via `docker pull` then pin, e.g.:

**Root + backend Dockerfiles:** `FROM python:3.11-slim@sha256:...`
**Frontend Dockerfile:** `FROM node:20-alpine@sha256:...`

Run to resolve:
```bash
docker pull python:3.11-slim && docker inspect python:3.11-slim --format '{{index .RepoDigests 0}}'
docker pull node:20-alpine && docker inspect node:20-alpine --format '{{index .RepoDigests 0}}'
```

---

## L5 — Split Docker network

**File:** `docker-compose.yml`

Replace single `networks: ai-support-network` with two networks:

```yaml
networks:
  frontend_net:
    driver: bridge
  backend_net:
    driver: bridge
```

Assign services:
- `frontend` → `frontend_net` only
- `backend` → both `frontend_net` + `backend_net`
- `worker` → `backend_net` only
- `redpanda` → `backend_net` only

---

## L7 — Remove bootstrap_servers from health endpoint

**File:** `backend/api/routes/health.py:47`

```diff
     return {
         "status": "healthy" if is_connected else "unhealthy",
-        "bootstrap_servers": settings.kafka_bootstrap_servers,
         "details": "Queue connection successful"
     }
```
