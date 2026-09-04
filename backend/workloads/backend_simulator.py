"""A predictable stand-in for a paid, slow upstream API."""
import time


def fetch_data(key: str, delay_ms: float = 8.0) -> tuple[dict, float]:
    """Simulate latency and return a payload plus its backend cost."""
    time.sleep(delay_ms / 1000)
    cost = 1.0 + (len(key) % 5) * 0.5
    return {"key": key, "source": "simulated-backend", "payload": f"value-for-{key}"}, cost
