"""One public cache API that selects a standard or adaptive policy."""
from backend.algorithms.gds import GDSCache
from backend.algorithms.lfu import LFUCache
from backend.algorithms.lru import LRUCache
from backend.cache.redis_client import RedisClient
from backend.config import settings
from backend.core.decision_engine import DecisionEngine
from backend.core.scoring_engine import ScoringEngine
from backend.metrics.logger import log_decision


class AdaptiveCacheManager:
    """Coordinates metadata, eviction policy, and optional Redis persistence."""

    def __init__(self, algorithm: str = settings.algorithm, capacity: int = settings.cache_capacity) -> None:
        self.algorithm = algorithm.lower()
        policies = {"lru": LRUCache, "lfu": LFUCache, "gds": GDSCache, "adaptive": LRUCache}
        if self.algorithm not in policies:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        self.policy = policies[self.algorithm](capacity)
        self.redis = RedisClient(settings.redis_url)
        self.scorer = ScoringEngine(settings.weights)
        self.decider = DecisionEngine(self.scorer, settings.decision_threshold)

    def set_workload(self, workload: str) -> None:
        if self.algorithm == "adaptive":
            self.scorer.adjust_for_workload(workload)

    def get(self, key: str):
        item = self.policy.get(key)
        if not item:
            log_decision(key, "miss", self.algorithm)
            return None
        value = self.redis.get(key)
        score = self.scorer.score(item) if self.algorithm == "adaptive" else None
        log_decision(key, "hit", self.algorithm, score)
        return item.value if value is None else value

    def put(self, key: str, value, cost: float = 1.0) -> None:
        if self.algorithm == "adaptive" and len(self.policy.items) >= self.policy.capacity and key not in self.policy.items:
            victim = min(self.policy.items.values(), key=self.scorer.score)
            del self.policy.items[victim.key]
            self.redis.delete(victim.key)
            log_decision(victim.key, "evict", self.algorithm, self.scorer.score(victim))
        evicted = self.policy.put(key, value, cost)
        if evicted:
            self.redis.delete(evicted)
            log_decision(evicted, "evict", self.algorithm)
        self.redis.set(key, value)
        decision = self.decide(key) if self.algorithm == "adaptive" else "keep"
        # Expose the dashboard-friendly wording while retaining the decision engine API.
        decision = "keep" if decision == "retain" else decision
        item = self.policy.items.get(key)
        score = self.scorer.score(item) if self.algorithm == "adaptive" and item else None
        log_decision(key, decision, self.algorithm, score)

    def decide(self, key: str) -> str | None:
        item = self.policy.items.get(key)
        return self.decider.decide(item) if item else None

    def cache_state(self) -> list[dict]:
        """Return metadata for every in-memory cache entry."""
        state = []
        for item in self.policy.items.values():
            score = self.scorer.score(item) if self.algorithm == "adaptive" else None
            decision = self.decide(item.key) if self.algorithm == "adaptive" else "keep"
            decision = "keep" if decision == "retain" else decision
            state.append({
                "key": item.key, "frequency": item.frequency,
                "last_access": item.last_accessed, "cost": item.cost,
                "size": item.size, "score": score,
                "decision": decision,
            })
        return state
