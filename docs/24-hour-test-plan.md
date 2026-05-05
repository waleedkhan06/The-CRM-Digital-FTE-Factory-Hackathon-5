# Customer Success FTE — 24-Hour Continuous Operation Test Plan

**Version:** 1.0  
**Duration:** 24 continuous hours  
**Goal:** Validate the system meets production-readiness criteria before go-live

---

## Overview

This test plan verifies that the Customer Success FTE can handle real-world multi-channel traffic for 24 continuous hours without data loss, unacceptable latency, or pod failures that cause downtime.

### Pass/Fail Criteria Summary

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Uptime | ≥ 99.9% (< 1.44 min downtime) | `/health` endpoint monitoring |
| Web form submissions | ≥ 100 successful | Locust load test results |
| Email messages simulated | ≥ 50 processed | Gmail API test messages |
| WhatsApp messages | ≥ 50 processed | Twilio sandbox messages |
| Cross-channel customers | ≥ 10 (contacted via 2+ channels) | DB query `customer_identifiers` table |
| P95 latency | < 3 000 ms | MetricsCollector + Kafka `fte.metrics` |
| Escalation rate | < 25% of total tickets | `tickets` table query |
| Cross-channel ID accuracy | > 95% | Customer deduplication query |
| Message loss | 0 messages | Kafka offset tracking vs. DB ticket count |
| Chaos tolerance | Survives 12 random pod kills | Kill schedule below |

---

## Prerequisites

Before starting the 24-hour test, verify:

- [ ] `docker-compose up` or Kubernetes cluster is healthy
- [ ] All pods are `Running`: `kubectl get pods -n fte`
- [ ] `GET /health/ready` returns `"status": "ready"`
- [ ] PostgreSQL is accessible and schema is applied
- [ ] Kafka is running with all 9 topics created
- [ ] Gmail Pub/Sub subscription is active (or mock mode confirmed)
- [ ] Twilio sandbox is configured (or mock mode confirmed)
- [ ] Web form is accessible at `http://localhost:3000`
- [ ] `tests/load_test.py` runs without import errors: `locust --version`
- [ ] MetricsCollector worker is running

---

## Phase 1: Baseline Validation (Hours 0–1)

**Goal:** Confirm the system handles basic traffic before extended testing.

### 1.1 Health Checks
```powershell
# Run every 5 minutes — log all responses
while ($true) {
    $resp = Invoke-RestMethod http://localhost:8000/health
    Write-Host "$(Get-Date -Format 'HH:mm:ss') — status=$($resp.status)"
    Start-Sleep 300
}
```

### 1.2 Smoke Test — All Three Channels

**Web Form (manual)**
```powershell
$body = @{
    name    = "Test User"
    email   = "test@example.com"
    subject = "Smoke test - web form"
    category = "general"
    message  = "This is a 24-hour test smoke test submission."
    priority = "medium"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/support/submit `
    -Method POST -ContentType "application/json" -Body $body
```

**Agent Direct (internal)**
```powershell
$body = @{
    content        = "How do I export my data?"
    channel        = "web_form"
    customer_email = "smoketest@example.com"
    customer_name  = "Smoke Test"
    subject        = "Data export question"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/agent/process `
    -Method POST -ContentType "application/json" -Body $body
```

**Pass criteria:** Both return HTTP 200/202 and agent produces a non-empty response.

---

## Phase 2: Traffic Generation (Hours 1–22)

### 2.1 Locust Load Test — Web Form Channel

Start with low traffic, ramp up to realistic peak load.

```powershell
# Stage 1: Warm-up (hours 1–3) — 2 concurrent users
locust -f tests/load_test.py --headless `
    --users 2 --spawn-rate 1 --run-time 2h `
    --host http://localhost:8000 `
    --csv results/load_warmup

# Stage 2: Normal load (hours 3–18) — 10 concurrent users
locust -f tests/load_test.py --headless `
    --users 10 --spawn-rate 2 --run-time 15h `
    --host http://localhost:8000 `
    --csv results/load_normal

# Stage 3: Peak load (hours 18–22) — 25 concurrent users
locust -f tests/load_test.py --headless `
    --users 25 --spawn-rate 5 --run-time 4h `
    --host http://localhost:8000 `
    --csv results/load_peak
```

**Expected traffic:**
- Warm-up: ~70 requests/hour
- Normal: ~360 requests/hour
- Peak: ~900 requests/hour

### 2.2 Gmail Simulation (Hours 1–22)

Send 3–4 test emails per hour using the Gmail API test account.

```python
# scripts/simulate_gmail.py — run manually or schedule
import time
import requests

TEST_EMAILS = [
    {"subject": "API integration question", "body": "How do I authenticate to your API?"},
    {"subject": "Export data", "body": "How can I export all my project data?"},
    {"subject": "Billing question", "body": "Can I upgrade my plan mid-month?"},
    {"subject": "Bug report", "body": "The dashboard is not loading on Firefox 120."},
]

# For each email, trigger agent directly (simulates Gmail webhook)
for i in range(50):
    email_data = TEST_EMAILS[i % len(TEST_EMAILS)]
    requests.post("http://localhost:8000/agent/process", json={
        "content": email_data["body"],
        "channel": "email",
        "customer_email": f"simuser{i}@example.com",
        "customer_name": f"Simulated User {i}",
        "subject": email_data["subject"],
    })
    time.sleep(1200)  # 1 email per 20 minutes = 3/hour
```

### 2.3 WhatsApp Simulation (Hours 1–22)

Use Twilio sandbox to send 3+ messages per hour.

```python
# scripts/simulate_whatsapp.py
from twilio.rest import Client
import os, time

client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
SANDBOX_NUMBER = "whatsapp:+14155238886"
TEST_PHONES = [f"whatsapp:+1555000{i:04d}" for i in range(50)]

WA_MESSAGES = [
    "hi need help",
    "my account is locked",
    "how reset password?",
    "i want to cancel",
    "great product thanks!",
]

for i in range(50):
    client.messages.create(
        from_=SANDBOX_NUMBER,
        to=TEST_PHONES[i % len(TEST_PHONES)],
        body=WA_MESSAGES[i % len(WA_MESSAGES)],
    )
    time.sleep(1584)  # ~50 messages over 22 hours
```

### 2.4 Cross-Channel Customer Test (Hours 3, 8, 14, 20)

At each checkpoint, simulate 2–3 customers contacting via multiple channels.

```powershell
# Customer contacts via web form first, then WhatsApp
# Web form
$body = @{
    name = "CrossChannel User"; email = "cross1@example.com"
    subject = "Integration issue"; category = "technical"
    message = "I cannot connect to the API from Python."
} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/support/submit -Method POST `
    -ContentType "application/json" -Body $body

Start-Sleep 3600  # Wait 1 hour

# Same customer from WhatsApp
Invoke-RestMethod -Uri http://localhost:8000/agent/process -Method POST `
    -ContentType "application/json" -Body (@{
        content = "still having api issues from before"
        channel = "whatsapp"
        customer_email = "cross1@example.com"
        customer_name = "CrossChannel User"
        subject = "API issue follow-up"
    } | ConvertTo-Json)

# Verify cross-channel history preserved
Invoke-RestMethod "http://localhost:8000/customers/lookup?email=cross1@example.com"
```

---

## Phase 3: Chaos Testing (Hours 6, 10, 14, 18, 22)

**Schedule:** Kill a random pod every 4 hours (12 kills total during the test).

### 3.1 Pod Kill Procedure (Kubernetes)
```powershell
# Kill a random API pod
$pods = kubectl get pods -n fte -l app=fte-api -o name
$target = ($pods | Get-Random)
kubectl delete $target -n fte
Write-Host "Killed pod: $target at $(Get-Date)"

# Verify recovery within 2 minutes
Start-Sleep 30
kubectl get pods -n fte
Invoke-RestMethod http://localhost:8000/health
```

### 3.2 Pod Kill Procedure (Docker Compose)
```powershell
# Kill the API container
docker compose restart fte-api
Write-Host "Restarted fte-api at $(Get-Date)"
Start-Sleep 15
Invoke-RestMethod http://localhost:8000/health

# Kill the worker container
docker compose restart fte-worker
Write-Host "Restarted fte-worker at $(Get-Date)"
```

### 3.3 Database Interruption Test (Hour 12)
```powershell
# Pause the PostgreSQL container for 30 seconds
docker compose pause postgres
Start-Sleep 30
docker compose unpause postgres

# Verify system recovers gracefully
Start-Sleep 10
Invoke-RestMethod http://localhost:8000/health/ready
# Expected: database=true after recovery
```

### 3.4 Kafka Interruption Test (Hour 16)
```powershell
# Restart Kafka broker
docker compose restart kafka
Start-Sleep 30

# Verify messages resume processing (no loss)
Invoke-RestMethod http://localhost:8000/metrics/channels
```

### Pass Criteria After Each Chaos Event
- [ ] `/health` returns `"status": "healthy"` within 2 minutes
- [ ] No submitted tickets are lost (check DB count vs. Kafka offsets)
- [ ] Locust shows < 5% error rate within 5 minutes of recovery

---

## Phase 4: Metrics Validation (Hours 8, 16, 24)

At each checkpoint, collect and record these metrics:

### 4.1 Database Metrics Query
```sql
-- Run in PostgreSQL
SELECT
    source_channel,
    COUNT(*) AS total_tickets,
    COUNT(*) FILTER (WHERE status = 'escalated') AS escalated,
    COUNT(*) FILTER (WHERE status = 'resolved') AS resolved,
    ROUND(COUNT(*) FILTER (WHERE status = 'escalated')::decimal
          / NULLIF(COUNT(*), 0) * 100, 1) AS escalation_rate_pct
FROM tickets
WHERE created_at > NOW() - INTERVAL '8 hours'
GROUP BY source_channel
ORDER BY source_channel;
```

### 4.2 API Metrics Collection
```powershell
$metrics = Invoke-RestMethod http://localhost:8000/metrics/channels
$metrics | ConvertTo-Json -Depth 5 | Out-File "results/metrics_$(Get-Date -Format 'HH00').json"
```

### 4.3 Cross-Channel Identity Accuracy Check
```sql
-- Customers with multiple channel identifiers (cross-channel success)
SELECT
    c.email,
    COUNT(DISTINCT ci.identifier_type) AS channel_count,
    STRING_AGG(ci.identifier_type, ', ') AS channels
FROM customers c
JOIN customer_identifiers ci ON ci.customer_id = c.id
GROUP BY c.id, c.email
HAVING COUNT(DISTINCT ci.identifier_type) > 1
ORDER BY channel_count DESC;
```

### 4.4 Kafka Offset Verification (No Message Loss)
```powershell
# Check consumer group lag
docker exec kafka kafka-consumer-groups.sh `
    --bootstrap-server localhost:9092 `
    --group fte-message-processor --describe
# All LAG values should be 0 or near 0 under normal load
```

---

## Phase 5: Final Validation (Hour 24)

### 5.1 Run Full Test Suite
```powershell
cd "e:\The CRM Digital FTE Factory Hackathon 5"
python -m pytest tests/ -v --tb=short 2>&1 | Tee-Object results/final_test_run.txt
```

### 5.2 Final Metrics Report
```powershell
# Collect all metrics for the full 24-hour window
$finalMetrics = Invoke-RestMethod http://localhost:8000/metrics/channels
```

```sql
-- Final 24-hour summary
SELECT
    source_channel,
    COUNT(*) AS total_tickets,
    AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))) AS avg_resolution_seconds,
    COUNT(*) FILTER (WHERE status = 'escalated')::decimal / COUNT(*) * 100 AS escalation_pct
FROM tickets
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY source_channel;
```

### 5.3 Uptime Calculation
```powershell
# Count health check failures from logs
$failures = (Get-Content results/health_checks.log | Where-Object { $_ -notmatch '"status":"healthy"' }).Count
$total    = (Get-Content results/health_checks.log).Count
$uptime   = (($total - $failures) / $total) * 100
Write-Host "Uptime: $uptime%"
# Must be >= 99.9%
```

---

## Go / No-Go Checklist

Complete this checklist at Hour 24 before declaring the system production-ready.

### Traffic Volume
- [ ] Web form: ≥ 100 submissions processed
- [ ] Email: ≥ 50 messages processed
- [ ] WhatsApp: ≥ 50 messages processed
- [ ] Cross-channel: ≥ 10 customers used 2+ channels

### Performance
- [ ] P95 latency < 3 000 ms (from Kafka `fte.metrics` records)
- [ ] P99 latency < 10 000 ms
- [ ] No message loss (Kafka LAG = 0, ticket count matches)

### Reliability
- [ ] Uptime ≥ 99.9%
- [ ] System recovered within 2 min after each of 12 pod kills
- [ ] System recovered after DB interruption (Hour 12)
- [ ] System recovered after Kafka restart (Hour 16)

### Quality
- [ ] Escalation rate < 25%
- [ ] Average sentiment > 0.4 (customers not uniformly unhappy)
- [ ] Cross-channel ID accuracy > 95%
- [ ] Zero unhandled exceptions in application logs

### Tests
- [ ] All `pytest tests/` tests pass
- [ ] Load test shows < 5% error rate at peak (25 users)

---

## Results Recording Template

Fill in at the end of the 24-hour window:

| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|
| Uptime % | ≥ 99.9% | ___ | ___ |
| Web form tickets | ≥ 100 | ___ | ___ |
| Email tickets | ≥ 50 | ___ | ___ |
| WhatsApp tickets | ≥ 50 | ___ | ___ |
| Cross-channel customers | ≥ 10 | ___ | ___ |
| P95 latency (ms) | < 3 000 | ___ | ___ |
| Escalation rate % | < 25% | ___ | ___ |
| Cross-channel ID accuracy % | > 95% | ___ | ___ |
| Message loss count | 0 | ___ | ___ |
| Pod kill recovery time (avg s) | < 120 | ___ | ___ |
| Pytest pass rate % | 100% | ___ | ___ |
| **OVERALL VERDICT** | | | **PASS / FAIL** |
