"""A reproducible stand-in for a paid, slow upstream API."""
import random
import re
import time


def fetch_data(key: str, delay_ms: float = 8.0) -> tuple[dict, float]:
    """Simulate latency and return a structured API response plus its cost."""
    time.sleep(delay_ms / 1000)
    rng = random.Random(key)
    cost = rng.uniform(1.0, 10.0)
    match = re.search(r"(?:user|product):(?P<id>\d+)$|/users/(?P<api_id>\d+)$", key)
    record_id = int(match.group("id") or match.group("api_id")) if match else rng.randint(1000, 9999)
    if key.startswith("product:"):
        resource_type = "product"
        name = f"Product {record_id}"
        email = f"catalog-{record_id}@example.com"
    elif key.startswith("api:/users/"):
        resource_type = "user-api"
        name = f"User {record_id}"
        email = f"user{record_id}@example.com"
    else:
        resource_type = "user"
        name = f"User {record_id}"
        email = f"user{record_id}@example.com"
    return {
        "id": record_id,
        "type": resource_type,
        "data": {
            "name": name,
            "email": email,
            "score": rng.randint(1, 100),
        },
        "timestamp": time.time(),
    }, cost
