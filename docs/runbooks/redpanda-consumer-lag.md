# Runbook: Redpanda (Kafka) Consumer Lag / Queue Buildup

**Severity**: High  
**Service Impact**: Scoring pipeline delayed; new CVE impacts not processed  
**RTO**: < 15 minutes

---

## Symptoms
- `impact-analyzer` is running but not consuming new messages
- Redpanda lag metric shows growing offset gap
- Grafana `redpanda_kafka_consumer_group_lag` alert fires

## Diagnosis

### Step 1: Check consumer group lag
```bash
docker exec propex-redpanda rpk group describe impact-analyzer-group
# Look for large "LAG" values on the dependency.resolved topic
```

### Step 2: Check if the consumer process is alive
```bash
docker logs propex-impact-analyzer --tail 30
# Look for: "Starting Kafka consumer" and absence of error loops
```

### Step 3: Check Redpanda broker health
```bash
docker exec propex-redpanda rpk cluster info
# All brokers should show "UP"
```

## Recovery

### Option A: Restart the consumer service
```bash
docker compose restart impact-analyzer
# Wait 30 seconds, then re-check lag
docker exec propex-redpanda rpk group describe impact-analyzer-group
```

### Option B: Reset consumer group offset (use ONLY if messages are stale/corrupt)
```bash
# ⚠️  This will skip unprocessed messages — data loss risk
docker exec propex-redpanda rpk group seek impact-analyzer-group --to end --topics dependency.resolved
```

### Option C: Scale up consumers (if lag is due to volume spike)
```bash
# Run a second instance of impact-analyzer temporarily
docker compose up -d --scale impact-analyzer=2
```

## Prevention
- APScheduler batch job prevents real-time overload by buffering Medium/Low severity impacts
- Monitor: `docker exec propex-redpanda rpk topic describe dependency.resolved`
- Alert threshold: consumer lag > 1,000 messages → page on-call

## Escalation
If lag continues to grow after restart, check if Neo4j or Redis are the bottleneck:
```bash
docker stats propex-neo4j propex-redis
```
