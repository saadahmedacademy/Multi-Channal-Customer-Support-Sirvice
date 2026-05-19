# Load Testing Guide

This directory contains load testing scenarios using [Locust](https://locust.io/).

## Prerequisites

```bash
pip install locust
```

## Quick Start

### 1. Start the Backend API

```bash
# Terminal 1: Start API
uvicorn backend.api.main:app --reload --port 8000

# Terminal 2: Start Worker
python backend/worker/message_processor.py
```

### 2. Run Load Tests

**Web UI Mode (Recommended for first run):**
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```
Then open http://localhost:8089 in your browser.

**Headless Mode (Automated):**
```bash
# 100 users, spawn 10/sec, run for 60 seconds
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 60s
```

## Test Scenarios

### SupportFormUser (Default)
Simulates normal user behavior:
- Submit support forms (weight: 10)
- Check ticket status (weight: 5)
- Health checks (weight: 1)
- Wait time: 1-3 seconds between actions

**Usage:**
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 -u 50 -r 5
```

### HighVolumeUser
Simulates high-volume rapid submissions:
- Minimal wait time (0.1-0.5 seconds)
- Rapid form submissions
- Tests system under stress

**Usage:**
```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --class-picker \
  -u 100 -r 20
```

### MixedWorkloadUser
Realistic mixed workload:
- Form submissions
- Health checks
- API endpoint calls
- Wait time: 2-5 seconds

## Performance Targets

Based on success criteria from spec:

| Metric | Target | Critical |
|--------|--------|----------|
| Response Time (p95) | < 2000ms | < 5000ms |
| Response Time (p99) | < 5000ms | < 10000ms |
| Error Rate | < 1% | < 5% |
| Throughput | > 50 req/s | > 20 req/s |
| Concurrent Users | 100+ | 50+ |

## Test Scenarios

### Scenario 1: Normal Load
**Goal:** Validate performance under normal conditions

```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 300s \
  --html reports/normal_load.html
```

**Expected Results:**
- p95 response time < 2 seconds
- Error rate < 1%
- All endpoints responding

### Scenario 2: Peak Load
**Goal:** Test system at peak capacity

```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 300s \
  --html reports/peak_load.html
```

**Expected Results:**
- p95 response time < 5 seconds
- Error rate < 5%
- System remains stable

### Scenario 3: Stress Test
**Goal:** Find breaking point

```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 200 \
  --spawn-rate 20 \
  --run-time 180s \
  --html reports/stress_test.html
```

**Expected Results:**
- Identify maximum capacity
- Observe degradation patterns
- No crashes or data loss

### Scenario 4: Spike Test
**Goal:** Test rapid traffic increase

```bash
# Start with 10 users
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 10 \
  --spawn-rate 10 \
  --run-time 60s

# Then spike to 100 users
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 100 \
  --spawn-rate 50 \
  --run-time 120s \
  --html reports/spike_test.html
```

## Monitoring During Tests

### 1. API Logs
```bash
tail -f logs/api.log
```

### 2. Worker Logs
```bash
tail -f logs/worker.log
```

### 3. System Resources
```bash
# CPU and Memory
htop

# Database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Queue lag
# Check Redpanda metrics
```

## Analyzing Results

### Key Metrics to Review

1. **Response Times**
   - Average, median, p95, p99
   - Look for outliers
   - Check if within targets

2. **Error Rates**
   - Total failures
   - Failure types (4xx vs 5xx)
   - Error patterns

3. **Throughput**
   - Requests per second
   - Sustained vs peak
   - Degradation over time

4. **Resource Usage**
   - CPU utilization
   - Memory consumption
   - Database connections
   - Queue depth

### Common Issues

**High Response Times:**
- Database query optimization needed
- Add caching layer (Redis)
- Increase worker count
- Optimize AI API calls

**High Error Rates:**
- Rate limiting too aggressive
- Database connection pool exhausted
- Queue backlog building up
- External API timeouts

**Memory Leaks:**
- Check for unclosed connections
- Review async task cleanup
- Monitor worker memory over time

## Best Practices

1. **Start Small:** Begin with 10-20 users, gradually increase
2. **Monitor Everything:** Watch logs, metrics, and system resources
3. **Test Incrementally:** Don't jump straight to 1000 users
4. **Document Results:** Save HTML reports for comparison
5. **Test Realistic Scenarios:** Mix of operations, not just one endpoint
6. **Run Multiple Times:** Ensure consistent results
7. **Test in Staging:** Never load test production without approval

## Troubleshooting

### Locust Won't Start
```bash
# Check if port 8089 is in use
lsof -i :8089

# Use different port
locust -f tests/load/locustfile.py --web-port 8090
```

### Connection Refused
```bash
# Verify API is running
curl http://localhost:8000/health

# Check firewall
sudo ufw status
```

### High Failure Rate
```bash
# Check API logs for errors
tail -f logs/api.log

# Verify database is accessible
psql $DATABASE_URL -c "SELECT 1;"

# Check queue is running
docker ps | grep redpanda
```

## Continuous Load Testing

### CI/CD Integration

Add to `.github/workflows/load-test.yml`:

```yaml
name: Load Test

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install locust
      - name: Run load test
        run: |
          locust -f tests/load/locustfile.py \
            --host=${{ secrets.STAGING_URL }} \
            --headless \
            --users 50 \
            --spawn-rate 5 \
            --run-time 300s \
            --html load-test-report.html
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: load-test-report
          path: load-test-report.html
```

## Resources

- [Locust Documentation](https://docs.locust.io/)
- [Load Testing Best Practices](https://docs.locust.io/en/stable/writing-a-locustfile.html)
- [Performance Testing Guide](https://martinfowler.com/articles/practical-test-pyramid.html)

---

**Last Updated:** 2026-05-19
