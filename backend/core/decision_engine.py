"""Turns adaptive scores into simple retain/evict/refresh decisions."""
from backend.cache.cache_object import CacheObject
from backend.core.scoring_engine import ScoringEngine


class DecisionEngine:
    def __init__(self, scorer: ScoringEngine, threshold: float) -> None:
        self.scorer, self.threshold = scorer, threshold

    def decide(self, item: CacheObject) -> str:
        score = self.scorer.score(item)
        if score < self.threshold:
            return "evict"
        if item.frequency > 8 and item.cost > 50:
            return "refresh"
        return "retain"
