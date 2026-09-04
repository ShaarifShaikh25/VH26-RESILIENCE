"""One public cache API that selects a standard or adaptive policy."""
from backend.algorithms.gds import GDSCache
from backend.algorithms.lfu import LFUCache
from backend.algorithms.lru import LRUCache
from backend.algorithms.adaptive import AdaptiveCache
from backend.cache.redis_client import RedisClient
from backend.config import settings
from backend.core.decision_engine import DecisionEngine
from backend.core.scoring_engine import ScoringEngine
from backend.metrics.logger import log_decision


class AdaptiveCacheManager:
    """Coordinates metadata, eviction policy, and optional Redis persistence."""

    def __init__(self, algorithm: str = "lru", capacity: int = settings.cache_capacity) -> None:
        requested_algorithm = algorithm.upper()
        policies = {"LRU": LRUCache, "LFU": LFUCache, "GDS": GDSCache, "ADAPTIVE": AdaptiveCache}
        if requested_algorithm not in policies:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        self.policy = policies[requested_algorithm](capacity)
        self.algorithm_name = self.policy.algorithm_name
        self.algorithm = self.algorithm_name.lower()
        self.redis = RedisClient(settings.redis_url)
        self.scorer = ScoringEngine(settings.weights)
        self.decider = DecisionEngine(self.scorer, settings.decision_threshold)
        if self.algorithm == "adaptive":
            self.policy.set_scorer(self.scorer)

    def set_workload(self, workload: str) -> None:
        if self.algorithm == "adaptive":
            self.scorer.adjust_for_workload(workload)

    def _score_for(self, item) -> float | None:
        if self.algorithm == "adaptive":
            return self.scorer.score(item)
        if self.algorithm == "gds":
            return self.policy.scores[item.key]
        return None

    def get(self, key: str):
        item = self.policy.get(key)
        if not item:
            log_decision(key, "miss", self.algorithm_name)
            return None
        value = self.redis.get(key)
        score = self._score_for(item)
        log_decision(key, "hit", self.algorithm_name, score)
        return item.value if value is None else value

    def put(self, key: str, value, cost: float = 1.0) -> None:
        evicted = self.policy.put(key, value, cost)
        if evicted:
            evicted_score = getattr(self.policy, "last_evicted_score", None)
            print(f"Evicting: {evicted} Algo: {self.algorithm}")
            if evicted_score is not None:
                print(f"Score: {evicted_score:.6f}")
            self.redis.delete(evicted)
            log_decision(evicted, "evict", self.algorithm_name, evicted_score)
        self.redis.set(key, value)
        decision = self.decide(key) if self.algorithm == "adaptive" else "keep"
        # Expose the dashboard-friendly wording while retaining the decision engine API.
        decision = "evicted" if decision is None else decision
        decision = "keep" if decision == "retain" else decision
        item = self.policy.items.get(key)
        score = self._score_for(item) if item else None
        log_decision(key, decision, self.algorithm_name, score)

    def decide(self, key: str) -> str | None:
        item = self.policy.items.get(key)
        return self.decider.decide(item) if item else None

    def cache_state(self) -> list[dict]:
        """Return metadata for every in-memory cache entry."""
        state = []
        for item in self.policy.items.values():
            score = self._score_for(item)
            decision = self.decide(item.key) if self.algorithm == "adaptive" else "keep"
            decision = "keep" if decision == "retain" else decision
            state.append({
                "key": item.key, "frequency": item.frequency,
                "last_access": item.last_accessed, "cost": item.cost,
                "size": item.size, "score": score,
                "decision": decision,
            })
        return state
