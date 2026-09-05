"""Small Redis adapter with a graceful in-memory fallback."""
import json
from typing import Any

try:
    import redis
except ImportError:  # Allows importing the project before dependencies are installed.
    redis = None


class RedisClient:
    """Use Redis when available; retain a local fallback for demos and tests."""

    def __init__(self, url: str) -> None:
        self._fallback: dict[str, Any] = {}
        self.client = None
        if redis:
            try:
                candidate = redis.Redis.from_url(
                    url,
                    decode_responses=True,
                    socket_connect_timeout=0.25,
                    socket_timeout=0.25,
                )
                candidate.ping()
                self.client = candidate
            except redis.RedisError:
                pass

    def get(self, key: str) -> Any | None:
        raw = self.client.get(key) if self.client else self._fallback.get(key)
        return json.loads(raw) if raw is not None else None

    def set(self, key: str, value: Any) -> None:
        raw = json.dumps(value)
        if self.client:
            self.client.set(key, raw)
        else:
            self._fallback[key] = raw

    def delete(self, key: str) -> None:
        if self.client:
            self.client.delete(key)
        else:
            self._fallback.pop(key, None)
