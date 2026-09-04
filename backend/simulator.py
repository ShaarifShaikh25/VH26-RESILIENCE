import time
import random

def fetch_from_backend(key: str):
    """
    Simulates fetching data from a slow backend.
    Now updated to also return random application_type, retrieval_cost, and size.
    """
    # Simulate network or DB delay (100ms to 500ms)
    time.sleep(random.uniform(0.1, 0.5))
    
    app_types = ["API", "IMAGE", "DB_QUERY"]
    
    return {
        "data": f"Data for {key} from backend",
        "application_type": random.choice(app_types),
        "retrieval_cost": random.uniform(10.0, 100.0),  # Example cost (e.g., ms latency from origin)
        "size": random.uniform(1.0, 500.0)              # Example size in KB
    }
