"""A reproducible stand-in for a paid, slow upstream API."""
import random
import time


def fetch_data(key: str, delay_ms: float = 8.0) -> tuple[dict, float]:
    """Simulate latency and return a payload plus its backend cost."""
    time.sleep(delay_ms / 1000)
    rng = random.Random(key)
    cost = rng.uniform(1.0, 10.0)
    size = rng.randint(1, 100)
    return {
        "key": key,
        "source": "simulated-backend",
        "payload": f"value-for-{key}",
        "size": size,
    }, cost
