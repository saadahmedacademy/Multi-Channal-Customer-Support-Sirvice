# Load Testing Execution Guide

**Task**: Run load tests and document performance results  
**Status**: Ready to execute  
**Prerequisites**: API and Worker must be running

---

## Quick Start

### Step 1: Start Services

```bash
# Terminal 1: Start API
cd /home/saadahmed/hk-5
source .venv/bin/activate
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start Worker
cd /home/saadahmed/hk-5
source .venv/bin/activate
python backend/worker/message_processor.py

# Terminal 3: Verify services
curl http://localhost:8000/health
```

### Step 2: Run Load Tests

```bash
# Terminal 4: Run load tests
cd /home/saadahmed/hk-5
source .venv/bin/activate

# Test 1: Normal Load (50 users, 5 min)
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 300s \
  --html reports/load_test_normal_$(date +%Y%m%d_%H%M%S).html

# Test 2: Peak Load (100 users, 5 min)
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 300s \
  --html reports/load_test_peak_$(date +%Y%m%d_%H%M%S).html

# Test 3: Stress Test (200 users, 3 min)
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 200 \
  --spawn-rate 20 \
  --run-time 180s \
  --html reports/load_test_stress_$(date +%Y%m%d_%H%M%S).html
```

---

## Performance Targets

| Metric | Target | Critical | Status |
|--------|--------|----------|--------|
| Response Time (p95) | < 2s | < 5s | ⏳ To measure |
| Response Time (p99) | < 5s | < 10s | ⏳ To measure |
| Error Rate | < 1% | < 5% | ⏳ To measure |
| Throughput | > 50 req/s | > 20 req/s | ⏳ To measure |
| Concurrent Users | 100+ | 50+ | ⏳ To measure |

---

## Results Template

Copy this template to `reports/LOAD_TEST_RESULTS.md` after running tests:

```markdown
# Load Test Results

**Date**: [DATE]  
**Environment**: Local Development  
**API Version**: 1.0.0

---

## Test 1: Normal Load (50 users)

**Configuration:**
- Users: 50
- Spawn Rate: 5/sec
- Duration: 5 minutes
- User Class: SupportFormUser

**Results:**
- Total Requests: [NUMBER]
- Failed Requests: [NUMBER]
- Failure Rate: [PERCENTAGE]%
- Average Response Time: [NUMBER]ms
- Median Response Time: [NUMBER]ms
- 95th Percentile: [NUMBER]ms
- 99th Percentile: [NUMBER]ms
- Requests/sec: [NUMBER]
- Max Response Time: [NUMBER]ms

**Status**: ✅ PASS / ❌ FAIL

**Notes:**
- [Any observations]
- [Bottlenecks identified]
- [Errors encountered]

---

## Test 2: Peak Load (100 users)

**Configuration:**
- Users: 100
- Spawn Rate: 10/sec
- Duration: 5 minutes
- User Class: SupportFormUser

**Results:**
- Total Requests: [NUMBER]
- Failed Requests: [NUMBER]
- Failure Rate: [PERCENTAGE]%
- Average Response Time: [NUMBER]ms
- Median Response Time: [NUMBER]ms
- 95th Percentile: [NUMBER]ms
- 99th Percentile: [NUMBER]ms
- Requests/sec: [NUMBER]
- Max Response Time: [NUMBER]ms

**Status**: ✅ PASS / ❌ FAIL

**Notes:**
- [Any observations]
- [Bottlenecks identified]
- [Errors encountered]

---

## Test 3: Stress Test (200 users)

**Configuration:**
- Users: 200
- Spawn Rate: 20/sec
- Duration: 3 minutes
- User Class: SupportFormUser

**Results:**
- Total Requests: [NUMBER]
- Failed Requests: [NUMBER]
- Failure Rate: [PERCENTAGE]%
- Average Response Time: [NUMBER]ms
- Median Response Time: [NUMBER]ms
- 95th Percentile: [NUMBER]ms
- 99th Percentile: [NUMBER]ms
- Requests/sec: [NUMBER]
- Max Response Time: [NUMBER]ms

**Status**: ✅ PASS / ❌ FAIL

**Notes:**
- [Any observations]
- [Bottlenecks identified]
- [Maximum capacity identified]

---

## Summary

### Performance Assessment

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| p95 Response Time | < 2s | [ACTUAL] | [✅/❌] |
| p99 Response Time | < 5s | [ACTUAL] | [✅/❌] |
| Error Rate | < 1% | [ACTUAL] | [✅/❌] |
| Throughput | > 50 req/s | [ACTUAL] | [✅/❌] |
| Max Users | 100+ | [ACTUAL] | [✅/❌] |

### Bottlenecks Identified

1. [Bottleneck 1]
   - Impact: [Description]
   - Recommendation: [Fix]

2. [Bottleneck 2]
   - Impact: [Description]
   - Recommendation: [Fix]

### Recommendations

**Immediate:**
- [ ] [Action 1]
- [ ] [Action 2]

**Short Term:**
- [ ] [Action 1]
- [ ] [Action 2]

**Long Term:**
- [ ] [Action 1]
- [ ] [Action 2]

---

## System Resources During Tests

**CPU Usage:**
- Average: [PERCENTAGE]%
- Peak: [PERCENTAGE]%

**Memory Usage:**
- Average: [MB/GB]
- Peak: [MB/GB]

**Database Connections:**
- Average: [NUMBER]
- Peak: [NUMBER]

**Queue Depth:**
- Average: [NUMBER]
- Peak: [NUMBER]

---

## Conclusion

[Overall assessment of system performance]

**Production Ready**: ✅ YES / ❌ NO / ⚠️ WITH CAVEATS

**Caveats:**
- [Caveat 1]
- [Caveat 2]

---

**Tested By**: [NAME]  
**Date**: [DATE]  
**Next Review**: [DATE]
```

---

## Monitoring During Tests

### Watch API Logs
```bash
# In separate terminal
tail -f logs/api.log | grep -E "(ERROR|WARNING|response_time)"
```

### Watch Worker Logs
```bash
# In separate terminal
tail -f logs/worker.log | grep -E "(ERROR|WARNING|Processing)"
```

### Monitor System Resources
```bash
# CPU and Memory
htop

# Or use top
top -p $(pgrep -f "uvicorn|python.*message_processor")
```

### Check Database
```bash
# Connection count
psql $DATABASE_URL -c "SELECT count(*) as connections FROM pg_stat_activity;"

# Active queries
psql $DATABASE_URL -c "SELECT pid, state, query FROM pg_stat_activity WHERE state != 'idle';"
```

---

## Troubleshooting

### High Response Times
- Check database query performance
- Check AI API response times
- Check queue depth
- Consider adding Redis caching

### High Error Rates
- Check API logs for errors
- Check database connection pool
- Check rate limiting settings
- Verify external API availability

### Low Throughput
- Check worker count
- Check database connection pool size
- Check queue consumer lag
- Consider horizontal scaling

---

## After Testing

1. **Review HTML Reports**
   ```bash
   cd reports
   python -m http.server 8080
   # Open http://localhost:8080 in browser
   ```

2. **Document Results**
   - Fill in the results template
   - Save to `reports/LOAD_TEST_RESULTS.md`
   - Commit to git

3. **Create Action Items**
   - File issues for bottlenecks
   - Prioritize optimizations
   - Update deployment plan

4. **Update Documentation**
   - Update performance benchmarks
   - Update capacity planning
   - Update SLA/SLO definitions

---

## Success Criteria

✅ **PASS** if:
- p95 response time < 2 seconds
- Error rate < 1%
- System handles 100+ concurrent users
- No crashes or data loss
- Resource usage acceptable

⚠️ **CONDITIONAL PASS** if:
- p95 response time < 5 seconds
- Error rate < 5%
- System handles 50+ concurrent users
- Minor issues identified with fixes planned

❌ **FAIL** if:
- p95 response time > 5 seconds
- Error rate > 5%
- System crashes under load
- Data loss occurs
- Critical bottlenecks with no clear fix

---

**Ready to Execute**: ✅ YES  
**Estimated Time**: 30-45 minutes  
**Next Task**: Deploy to staging
