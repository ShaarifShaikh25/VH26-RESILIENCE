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
        self.scorer = ScoringEngine()
        self.last_prediction_score: float | None = None
        self.decider = DecisionEngine(self.scorer, settings.decision_threshold)
        self.evictions: int = 0
        self.refreshes: int = 0
        self.decision_counts: dict[str, int] = {"retain": 0, "evict": 0, "refresh": 0}
        self.verbose_logging: bool = True
        if self.algorithm == "adaptive":
            self.policy.set_scorer(self.scorer)

    def set_workload(self, workload: str) -> None:
        if self.algorithm == "adaptive":
            self.scorer.adjust_for_workload(workload)

    def _score_for(self, item) -> float | None:
        if self.algorithm == "adaptive":
            self.last_prediction_score = self.scorer.score(item)
            return self.last_prediction_score
        if self.algorithm == "gds":
            return self.policy.scores[item.key]
        return None

    def get(self, key: str):
        if self.algorithm == "adaptive":
            self.last_prediction_score = None
            self.scorer.begin_request()
        item = self.policy.get(key)
        if not item:
            log_decision(key, "miss", self.algorithm_name)
            return None
        value = self.redis.get(key)
        score = self._score_for(item)

        if self.algorithm == "adaptive":
            self.scorer.track_reuse(key, item)
            decision, dec_score = self.decider.decide_with_score(item)
            if decision == "refresh":
                self.refreshes += 1
                self.decision_counts["refresh"] += 1
                item.touch(getattr(self.scorer, "request_number", 0))
            elif decision == "evict":
                self.decision_counts["evict"] += 1
            else:
                self.decision_counts["retain"] += 1

            if self.verbose_logging:
                print(f"[ADAPTIVE DECISION] object={key} score={dec_score:.4f} decision={decision}")
            log_decision(key, "hit", self.algorithm_name, dec_score, {"decision": decision})
        else:
            log_decision(key, "hit", self.algorithm_name, score)

        return item.value if value is None else value

    def put(self, key: str, value, cost: float = 1.0) -> None:
        was_present = key in self.policy.items
        evicted = self.policy.put(key, value, cost)
        if evicted:
            self.evictions += 1
            evicted_score = getattr(self.policy, "last_evicted_score", None)
            if self.algorithm == "adaptive":
                self.decision_counts["evict"] += 1
                if self.verbose_logging:
                    ev_val = evicted_score if evicted_score is not None else 0.0
                    print(f"[ADAPTIVE DECISION] object={evicted} score={ev_val:.4f} decision=evict")
            metadata = {
                "decision_mode": getattr(self.policy, "last_eviction_mode", None),
                "retention_score": getattr(self.policy, "last_evicted_retention_score", None),
                "decision_target": "evicted_item",
                **getattr(self.policy, "last_eviction_metadata", {}),
            }
            self.redis.delete(evicted)
            log_decision(evicted, "evict", self.algorithm_name, evicted_score, metadata)
        self.redis.set(key, value)
        item = self.policy.items.get(key)
        score = self._score_for(item) if item else None
        decision = "keep"

        if self.algorithm == "adaptive" and item:
            item_dec, item_score = self.decider.decide_with_score(item)
            score = item_score
            decision = item_dec
            if decision == "refresh":
                self.refreshes += 1
                self.decision_counts["refresh"] += 1
            elif decision == "evict":
                self.decision_counts["evict"] += 1
            else:
                self.decision_counts["retain"] += 1

            if self.verbose_logging:
                print(f"[ADAPTIVE DECISION] object={key} score={item_score:.4f} decision={decision}")

        # Expose the dashboard-friendly wording while retaining the decision engine API.
        log_decision_str = "evicted" if decision is None else decision
        log_decision_str = "keep" if log_decision_str == "retain" else log_decision_str
        retention_score = None
        if self.algorithm == "adaptive" and item and score is not None:
            retention_score = getattr(self.policy, "_retention_score", lambda it: score)(item)
        log_decision(key, log_decision_str, self.algorithm_name, score, {
            "decision_mode": "RETAIN" if log_decision_str == "keep" else log_decision_str.upper(),
            "decision_target": "cache_item",
            "retention_score": retention_score,
            "frequency": item.frequency if item else None,
            "last_access": item.last_accessed if item else None,
            "cost": item.cost if item else None,
            "size": item.size if item else None,
        })
        if self.algorithm == "adaptive" and not was_present:
            tracking_item = item or self.policy._cache_object(key, value, cost)
            self.scorer.track_new_item(tracking_item)

    def learning_metrics(self) -> dict:
        if self.algorithm != "adaptive":
            return {
                "training_samples": 0, "pending_labels": 0,
                "average_prediction_score": 0.0,
                "ml_prediction_accuracy": 0.0,
                "reuse_prediction_quality": 0.0,
                "exploration_count": 0,
                "exploitation_count": 0,
                "warmup_phase": False,
                "model_confidence": 0.0,
                "exploration_ratio": 0.0,
            }
        return {
            **self.scorer.learning_metrics(),
            "exploration_count": self.policy.exploration_count,
            "exploitation_count": self.policy.exploitation_count,
            "warmup_phase": self.policy.warmup_phase,
            "exploration_ratio": (
                self.policy.exploration_count / (
                    self.policy.exploration_count + self.policy.exploitation_count
                ) if self.policy.exploration_count + self.policy.exploitation_count else 0.0
            ),
        }

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
                "value": item.value,
            })
        return state
