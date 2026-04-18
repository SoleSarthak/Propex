# Runbook: PostgreSQL Container Restart

**Severity**: Medium  
**Service Impact**: API Gateway + Impact Analyzer (write path only, Redis cache serves reads)  
**Recovery Time Objective (RTO)**: < 5 minutes

---

## Symptoms
- `api-gateway` logs: `sqlalchemy.exc.OperationalError: could not connect to server`
- `impact-analyzer` logs: `asyncpg.exceptions.ConnectionFailureError`
- API returns `500 Internal Server Error` on write endpoints

## Immediate Response

### Step 1: Verify the container is down
```bash
docker ps | grep propex-postgres
# If missing from output, container has crashed
```

### Step 2: Check logs for root cause
```bash
docker logs propex-postgres --tail 50
# Common causes: OOM (out of memory), disk full, ungraceful shutdown
```

### Step 3: Restart the container
```bash
docker compose restart postgres
# Wait 15-20 seconds for health check to pass
docker ps | grep propex-postgres  # Should show "healthy"
```

### Step 4: Verify data integrity
```bash
docker exec propex-postgres psql -U propex -d propex_db -c "\dt"
# Verify all tables are present: affected_repositories, issued_notifications, etc.
docker exec propex-postgres psql -U propex -d propex_db -c "SELECT COUNT(*) FROM affected_repositories;"
```

### Step 5: Restart dependent services
```bash
docker compose restart api-gateway impact-analyzer
```

### Step 6: Verify API health
```bash
curl http://localhost:8006/health
# Expected: {"status":"healthy"}
```

## If Data is Corrupt
```bash
# 1. Stop all services
docker compose down

# 2. Restore from latest backup (daily pg_dump to MinIO)
docker exec propex-minio mc cp minio/propex-backups/latest.sql /tmp/restore.sql
docker exec propex-postgres psql -U propex -d propex_db < /tmp/restore.sql

# 3. Restart
docker compose up -d
```

## Prevention
- PostgreSQL is configured with `max_connections=100` (see `docker-compose.yml`)
- Daily `pg_dump` to MinIO runs at 3 AM UTC via APScheduler in the coordinator service
- Monitor disk space: `df -h` — alert if `/var/lib/docker` > 80%

## Escalation
If recovery takes > 10 minutes, page the on-call engineer via UptimeRobot alert.
