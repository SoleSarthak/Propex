import redis
import json
from typing import Any, Optional


class RedisClient:
    def __init__(self, host: str, port: int, db: int = 0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def get_json(self, key: str) -> Optional[Any]:
        val = self.client.get(key)
        if val:
            return json.loads(val)
        return None

    def set_json(self, key: str, value: Any, ttl_seconds: int = 86400):
        self.client.setex(key, ttl_seconds, json.dumps(value))

    def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, window_seconds)
        if current > limit:
            return False  # rate limited
        return True
