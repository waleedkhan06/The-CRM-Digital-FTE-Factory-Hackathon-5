# 📖 Operations Runbook — Customer Success FTE

> **Purpose:** Guide for operating, monitoring, and troubleshooting the Digital FTE system.
> **Audience:** Support engineers, DevOps, on-call staff

---

## 🔍 System Overview

| Component | Port/Location | Health Check |
|-----------|--------------|-------------|
| **FastAPI** | `:8000` | `GET /health` |
| **Next.js Frontend** | `:3000` | `GET /` |
| **PostgreSQL** | `:5432` | `pg_isready` |
| **Kafka** | `:9092` | Kafka broker connection |
| **Zookeeper** | `:2181` | Zookeeper four-letter commands |

---

## 🚨 Incident Response

### P0 — System Down

**Symptoms:** Health check returns 500 or times out, all users affected

**Immediate Actions:**
```bash
# 1. Check system status
curl http://localhost:8000/health/ready

# 2. Check all services
docker compose ps
# or
kubectl get pods -n customer-success-fte

# 3. Check logs
docker compose logs --tail=100 fte-api
# or
kubectl logs -n customer-success-fte -l app=customer-success-fte --tail=100

# 4. Restart affected services
docker compose restart fte-api fte-worker
# or
kubectl rollout restart deployment/fte-api -n customer-success-fte
```

**Escalation:** Notify engineering lead immediately

---

### P1 — High Error Rate (>5%)

**Symptoms:** Multiple 500 errors in logs, customers reporting failures

**Diagnosis:**
```bash
# Check error logs
docker compose logs fte-api 2>&1 | grep -i error | tail -50

# Check database connectivity
curl http://localhost:8000/health/ready | python3 -m json.tool

# Check Kafka connectivity
docker compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

**Common Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Database connection pool exhausted | `docker compose restart postgres` |
| Kafka broker unavailable | `docker compose restart kafka` |
| OpenAI API rate limit | Implement exponential backoff, check quota |
| Out of memory | Scale up pod resources in K8s |

---

### P2 — Channel Failure

#### Gmail Not Working
```bash
# Check Gmail handler status
curl http://localhost:8000/health | python3 -c "import sys,json; print(json.load(sys.stdin)['channels'])"

# Check credentials
ls -la credentials/gmail-credentials.json

# Test Gmail API
python3 -c "
from production.channels.gmail_handler import GmailHandler
h = GmailHandler()
print('Gmail initialized:', h._initialized)
"
```

**Fix:** Re-download service account JSON if expired

#### WhatsApp Not Working
```bash
# Check Twilio credentials
echo $TWILIO_ACCOUNT_SID
echo $TWILIO_AUTH_TOKEN

# Test Twilio connection
python3 -c "
from twilio.rest import Client
client = Client('AC...', 'auth_token')
print(client.api.accounts('AC...').fetch().status)
"
```

**Fix:** Regenerate Auth Token in Twilio Console if compromised

#### Web Form Not Working
```bash
# Check Next.js
curl http://localhost:3000

# Check API endpoint
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","subject":"Test","category":"general","message":"Test message"}'
```

---

### P3 — Slow Response Times

**Symptoms:** P95 latency > 3 seconds

**Diagnosis:**
```bash
# Check metrics
curl http://localhost:8000/metrics/channels | python3 -m json.tool

# Check database query performance
docker compose exec postgres psql -U fte_user -d fte_db -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;
"

# Check Kafka queue depth
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group fte-message-processor
```

**Fix:** Scale up workers
```bash
# K8s
kubectl scale deployment fte-message-processor --replicas=10 -n customer-success-fte

# Docker
docker compose up -d --scale fte-worker=5
```

---

## 📊 Monitoring

### Key Metrics to Watch

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| P95 Latency | < 1s | 1-3s | > 3s |
| Error Rate | < 1% | 1-5% | > 5% |
| Queue Depth | < 10 | 10-50 | > 100 |
| Escalation Rate | < 15% | 15-25% | > 25% |
| DB Connections | < 10 | 10-18 | > 18 |
| Memory Usage | < 70% | 70-85% | > 85% |

### Sentiment Alerts

```bash
# Check for negative sentiment conversations
docker compose exec postgres psql -U fte_user -d fte_db -c "
SELECT c.id, c.sentiment_score, c.initial_channel, c.started_at
FROM conversations c
WHERE c.sentiment_score < 0.3
  AND c.started_at > NOW() - INTERVAL '1 hour'
ORDER BY c.sentiment_score ASC;
"
```

---

## 🔄 Common Operations

### Deploy New Version

```bash
# 1. Build new image
docker compose build

# 2. Rolling update (K8s)
kubectl set image deployment/fte-api \
  fte-api=your-registry/customer-success-fte:v2.0.0 \
  -n customer-success-fte

# 3. Monitor rollout
kubectl rollout status deployment/fte-api -n customer-success-fte

# 4. Rollback if needed
kubectl rollout undo deployment/fte-api -n customer-success-fte
```

### Database Migration

```bash
# Apply schema changes
docker compose exec postgres psql -U fte_user -d fte_db -f /docker-entrypoint-initdb.d/02-migration.sql

# Or via psql directly
psql -h localhost -U fte_user -d fte_db -f production/database/migrations/001_add_column.sql
```

### Scale Services

```bash
# K8s (HPA auto-scales, but manual override)
kubectl scale deployment fte-api --replicas=5 -n customer-success-fte
kubectl scale deployment fte-message-processor --replicas=10 -n customer-success-fte

# Docker
docker compose up -d --scale fte-api=3 --scale fte-worker=5
```

### Backup Database

```bash
# Full backup
docker compose exec postgres pg_dump -U fte_user fte_db > backup-$(date +%Y%m%d).sql

# Restore
docker compose exec -T postgres psql -U fte_user -d fte_db < backup-20260407.sql
```

---

## 🐛 Troubleshooting FAQ

### "OpenAI API key is required" Warning
- **Cause:** `OPENAI_API_KEY` not set in `.env`
- **Fix:** Add your key to `.env` and restart
- **Impact:** Agent falls back to keyword-based prototype (still works)

### "aiokafka not installed" Warning
- **Cause:** Kafka Python client not installed
- **Fix:** `pip install aiokafka`
- **Impact:** Messages processed synchronously instead of via queue

### "Gmail credentials not found" Warning
- **Cause:** `credentials/gmail-credentials.json` missing
- **Fix:** Download service account JSON from Google Cloud Console
- **Impact:** Gmail channel disabled (other channels still work)

### Form Submission Returns Error
- **Cause:** Validation failure or API misconfiguration
- **Fix:** Check browser console for errors, verify API URL in frontend
- **Debug:** `curl -v POST http://localhost:8000/support/submit -H "Content-Type: application/json" -d '{...}'`

### Ticket Status Shows "Processing" Forever
- **Cause:** Kafka consumer not running or agent not processing
- **Fix:** Restart worker: `docker compose restart fte-worker`
- **Check:** `docker compose logs fte-worker | tail -50`

---

## 📞 Escalation Contacts

| Role | Contact | When to Contact |
|------|---------|----------------|
| **On-Call Engineer** | Internal channel | P0/P1 incidents |
| **Engineering Lead** | marcus.j@techcorp.io | P0 > 30 min, architectural decisions |
| **Support Manager** | sarah.chen@techcorp.io | Escalation rate spikes, customer complaints |
| **Product Manager** | priya.p@techcorp.io | Feature requests, product decisions |

---

## 📋 Daily Checklist

- [ ] Health check passing (`GET /health`)
- [ ] Error rate < 1% (check logs)
- [ ] P95 latency < 3 seconds
- [ ] Queue depth < 10 messages
- [ ] No negative sentiment alerts unresolved
- [ ] All 3 channels operational
- [ ] Database backups completed
- [ ] SSL certificate valid (if production)

---

## 📋 Weekly Checklist

- [ ] Review escalation rate trend (< 20%)
- [ ] Check customer satisfaction metrics
- [ ] Review top topics for knowledge gaps
- [ ] Update knowledge base with new solutions
- [ ] Test disaster recovery (backup restore)
- [ ] Review and rotate logs if needed
- [ ] Check for security updates

---

*Last updated: April 7, 2026*
