"""A cost-aware cache policy combining frequency and recency."""
from time import time


class AdaptiveCache:
    """Keep high-frequency, recently used, and expensive values in cache."""

    SPIKE_FREQUENCY_THRESHOLD = 2.0

    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.meta = {}

    def get(self, key):
        if key in self.cache:
            self.meta[key]["frequency"] += 1
            self.meta[key]["last_access"] = time()
            return self.cache[key]
        return None

    def score(self, key):
        """Return the retention value using workload-aware component weights."""
        metadata = self.meta[key]
        average_frequency = self.average_frequency()
        if average_frequency >= self.SPIKE_FREQUENCY_THRESHOLD:
            frequency_weight, cost_weight, recency_weight = 0.6, 0.3, 0.1
        else:
            frequency_weight, cost_weight, recency_weight = 0.4, 0.4, 0.2

        freq_score = metadata["frequency"]
        recency_score = 1 / (1 + time() - metadata["last_access"])
        cost_score = metadata["cost"]
        return (frequency_weight * freq_score
                + cost_weight * cost_score
                + recency_weight * recency_score)

    def average_frequency(self):
        """Return cache-wide access frequency used to detect a traffic spike."""
        if not self.meta:
            return 0.0
        return sum(item["frequency"] for item in self.meta.values()) / len(self.meta)

    def put(self, key, value, cost=None):
        if key in self.cache:
            self.meta[key]["frequency"] += 1
            self.meta[key]["last_access"] = time()
            return

        if len(self.cache) >= self.capacity:
            # evict lowest score
            worst_key = min(self.cache.keys(), key=lambda k: self.score(k))
            del self.cache[worst_key]
            del self.meta[worst_key]

        self.cache[key] = value
        self.meta[key] = {
            "frequency": 1,
            "last_access": time(),
            "cost": 0.0 if cost is None else float(cost),
        }
