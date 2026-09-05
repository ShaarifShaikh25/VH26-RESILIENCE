"""Online ML scoring model used by the adaptive eviction policy."""
from time import time

try:
    from river.ensemble import AdaptiveRandomForestRegressor
except ImportError:
    from river.forest import ARFRegressor as AdaptiveRandomForestRegressor

from backend.cache.cache_object import CacheObject


class ScoringEngine:
    """Learn reuse likelihood continuously from cache request outcomes."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.model = AdaptiveRandomForestRegressor(
            n_models=10, grace_period=10, leaf_prediction="adaptive", seed=42
        )
        self.training_samples = 0
        self.request_number = 0
        self.reuse_window = 50
        self.pending_reuse: dict[str, tuple[dict[str, float], int, float, int, float]] = {}
        self.prediction_scores: list[float] = []
        self.labeled_predictions = 0
        self.correct_predictions = 0
        self.reuse_probability_error = 0.0
        self.max_frequency_seen = 1.0
        self.max_cost = 10.0
        self.max_size = 1024.0
        self.max_time_window = 3600.0

    def adjust_for_workload(self, workload: str) -> None:
        """Retain the workload hook without changing learned model parameters."""

    def features(self, item: CacheObject) -> dict[str, float]:
        now = time()
        age = max(now - item.last_accessed, 0.0)
        self.max_frequency_seen = max(self.max_frequency_seen, float(item.frequency))
        recent_cutoff = now - 60.0
        recent_accesses = sum(access >= recent_cutoff for access in item.access_times)
        request_rate = min(recent_accesses / 60.0, 1.0)
        velocity_window = 10.0
        velocity_count = sum(access >= now - velocity_window for access in item.access_times)
        rolling_frequency = min(len(item.access_times[-10:]) / 10.0, 1.0)
        burst_indicator = 1.0 if velocity_count >= 3 else 0.0
        reuse_gap = (item.last_accessed - item.previous_accessed
                     if item.previous_accessed is not None else self.max_time_window)
        return {
            "frequency_norm": min(float(item.frequency) / self.max_frequency_seen, 1.0),
            "recency_norm": min(age / self.max_time_window, 1.0),
            "cost_norm": min(float(item.cost) / self.max_cost, 1.0),
            "size_norm": min(float(item.size) / self.max_size, 1.0),
            "request_rate": request_rate,
            "time_since_last_access": min(age / self.max_time_window, 1.0),
            "access_velocity": min(velocity_count / velocity_window, 1.0),
            "burst_indicator": burst_indicator,
            "rolling_frequency": rolling_frequency,
            "reuse_gap": min(reuse_gap / self.max_time_window, 1.0),
            "event_type": float({"view": 0, "cart": 1, "purchase": 2}.get(
                str(item.value.get("event", "view")) if isinstance(item.value, dict) else "view", 0
            )),
        }

    def score(self, item: CacheObject) -> float:
        features = self.features(item)
        self.model.predict_one(features)
        raw_prediction = float(self.model.predict_one(features) or 0.0)
        # The regression target is already normalized to [0, 1]; only add a
        # small floor/ceiling so cold-start scores remain continuous.
        score = 0.02 + 0.96 * min(max(raw_prediction, 0.0), 1.0)
        self.prediction_scores.append(score)
        self.prediction_scores = self.prediction_scores[-500:]
        return score

    def begin_request(self) -> None:
        """Advance the online reuse window and train observations that expired."""
        self.request_number += 1
        expired = [
            key for key, (_, expires_at, _, _, _) in self.pending_reuse.items()
            if self.request_number > expires_at
        ]
        for key in expired:
            features, _, prediction, future_hits, cost = self.pending_reuse.pop(key)
            self._learn(features, future_hits, cost, prediction)

    def track_new_item(self, item: CacheObject) -> None:
        """Start a deferred reuse observation for a newly fetched item."""
        self.pending_reuse[item.key] = (
            self.features(item), self.request_number + self.reuse_window,
            self.score(item), 0, float(item.cost),
        )

    def track_reuse(self, key: str, item: CacheObject | None = None) -> None:
        """Label a pending item positive when it is reused within the window."""
        observation = self.pending_reuse.get(key)
        if observation:
            features, expires_at, prediction, future_hits, cost = observation
            self.pending_reuse[key] = (
                self.features(item) if item is not None else features,
                expires_at, prediction, future_hits + 1, cost,
            )

    def _learn(self, features: dict[str, float], future_hits: int, cost: float,
               prediction: float) -> None:
        reuse_value = min(future_hits * cost / (self.reuse_window * self.max_cost), 1.0)
        self.model.learn_one(features, reuse_value)
        self.training_samples += 1
        self.labeled_predictions += 1
        self.correct_predictions += int(abs(prediction - reuse_value) <= 0.25)
        self.reuse_probability_error += abs(prediction - reuse_value)

    @property
    def average_prediction_score(self) -> float:
        return (sum(self.prediction_scores) / len(self.prediction_scores)
                if self.prediction_scores else 0.0)

    def learning_metrics(self) -> dict[str, float | int]:
        return {
            "training_samples": self.training_samples,
            "pending_labels": len(self.pending_reuse),
            "average_prediction_score": self.average_prediction_score,
            "ml_prediction_accuracy": (
                self.correct_predictions / self.labeled_predictions
                if self.labeled_predictions else 0.0
            ),
            "reuse_prediction_quality": (
                1.0 - self.reuse_probability_error / self.labeled_predictions
                if self.labeled_predictions else 0.0
            ),
            "model_confidence": min(self.training_samples / 100.0, 1.0),
        }
