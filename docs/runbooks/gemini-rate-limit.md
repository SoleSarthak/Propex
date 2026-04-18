# Runbook: Gemini API Rate Limit Exhaustion

**Severity**: Low (fallback templates are automatic)  
**Service Impact**: Patch drafts are template-based instead of LLM-generated until midnight UTC  
**RTO**: Self-healing at midnight UTC (daily quota resets)

---

## Symptoms
- `patch-drafter` logs: `Gemini daily rate limit reached (1500/1500). Using fallback template.`
- GitHub issues still being created, but content is template-based (not LLM)
- Redis key `gemini:daily:<date>` equals `1500`

## Diagnosis

### Step 1: Check current daily usage
```bash
docker exec propex-redis redis-cli GET "gemini:daily:$(date +%Y-%m-%d)"
# Returns current count. 1500 = limit reached.
```

### Step 2: Check Gemini usage log in PostgreSQL
```bash
docker exec propex-postgres psql -U propex -d propex_db \
  -c "SELECT DATE(called_at), COUNT(*), SUM(prompt_tokens+output_tokens) as total_tokens FROM gemini_usage_log GROUP BY DATE(called_at) ORDER BY 1 DESC LIMIT 7;"
```

## Recovery Options

### Option A: Wait for quota reset (recommended)
- Gemini free tier resets at midnight Pacific time (5:30 AM IST)
- Fallback templates are high quality and cover all 3 ecosystems × 4 severity tiers
- No manual intervention needed

### Option B: Use a second Gemini API key
```bash
# In .env file, swap the key temporarily
# GEMINI_API_KEY=<secondary_key>
docker compose restart patch-drafter
```

### Option C: Manually reset the daily counter (use with caution)
```bash
docker exec propex-redis redis-cli DEL "gemini:daily:$(date +%Y-%m-%d)"
# Warning: This bypasses the rate limit — may result in API charges if you upgrade
```

## Prevention
- Alert triggers at 1,200 requests/day (80% of limit) — check Grafana `gemini_usage` panel
- Batch non-critical (Medium/Low) patches after 6 PM IST to ensure headroom for Critical/High
- The `draft_patch()` function already prioritizes cache hits, so repeat CVE+repo pairs cost 0 tokens

## Notes
- 1M tokens/month free tier is rarely exhausted — 1,500 req/day limit is the binding constraint
- Each request averages ~500 prompt tokens + ~400 output tokens ≈ 900 tokens/req
- Monthly token budget: 1,500 × 30 × 900 = 40.5M tokens (well under 1M limit — fine)
