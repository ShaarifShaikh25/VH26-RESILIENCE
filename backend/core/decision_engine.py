"""Turns adaptive scores into simple retain/evict/refresh decisions."""
from backend.cache.cache_object import CacheObject
from backend.core.scoring_engine import ScoringEngine


class DecisionEngine:
    def __init__(self, scorer: ScoringEngine, threshold: float = 0.30) -> None:
        self.scorer = scorer
        self.threshold = threshold

    def decide(self, item: CacheObject) -> str:
        decision, _ = self.decide_with_score(item)
        return decision

    def decide_with_score(self, item: CacheObject) -> tuple[str, float]:
        score = self.scorer.score(item)
        if score < self.threshold:
            return "evict", score
        # Items with significant reuse frequency and high cost or top score get refreshed
        if item.frequency >= 3 and (item.cost >= 4.0 or item.frequency >= 5 or score >= 0.75):
            return "refresh", score
        return "retain", score
