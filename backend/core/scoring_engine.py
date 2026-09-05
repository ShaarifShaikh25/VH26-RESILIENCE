"""Online ML scoring model used by the adaptive eviction policy."""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from time import time

try:
    from river.forest import ARFRegressor as AdaptiveRandomForestRegressor
except ImportError:
    try:
        from river.ensemble import AdaptiveRandomForestRegressor
    except ImportError:
        AdaptiveRandomForestRegressor = None

from backend.cache.cache_object import CacheObject


@dataclass
class PendingObservation:
    obs_id: int
    key: str
    features: dict[str, float]
    expires_at: int
    prediction: float
    future_hits: int = 0
    cost: float = 1.0


class ScoringEngine:
    """Learn reuse likelihood continuously from cache request outcomes."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        if AdaptiveRandomForestRegressor is not None:
            self.model = AdaptiveRandomForestRegressor(
                n_models=10, grace_period=10, leaf_prediction="adaptive", seed=42
            )
        else:
            self.model = None

        self.training_samples = 0
        self.request_number = 0
        self.reuse_window = 30  # evaluate reuse within next 30 requests
        self.obs_counter = 0
        self.pending_observations: deque[PendingObservation] = deque()
        self.pending_by_key: dict[str, list[PendingObservation]] = {}
        self.prediction_scores: list[float] = []
        self.labeled_predictions = 0
        self.correct_predictions = 0
        self.reuse_probability_error = 0.0
        self.max_frequency_seen = 1.0
        self.max_cost = 10.0
        self.max_size = 1024.0
        self.max_time_window = 3600.0

        default_weights = {
            "frequency": 0.35,
            "recency": 0.30,
            "velocity": 0.15,
            "cost": 0.10,
            "size": 0.05,
            "gap": 0.05,
        }
        self.weights = weights.copy() if weights else default_weights
        self.workload = "default"

    @property
    def pending_reuse(self) -> dict:
        """Compatibility property for code reading pending_reuse dictionary length."""
        return {
            obs.key: (obs.features, obs.expires_at, obs.prediction, obs.future_hits, obs.cost)
            for obs in self.pending_observations
        }

    def adjust_for_workload(self, workload: str) -> None:
        """Favor frequency in steady traffic, recency/velocity during spikes, balanced in gradual."""
        self.workload = workload.lower()
        presets = {
            "steady": {"frequency": 0.55, "recency": 0.25, "velocity": 0.10, "cost": 0.05, "size": 0.03, "gap": 0.02},
            "spike": {"frequency": 0.10, "recency": 0.60, "velocity": 0.20, "cost": 0.05, "size": 0.03, "gap": 0.02},
            "gradual": {"frequency": 0.50, "recency": 0.30, "velocity": 0.10, "cost": 0.05, "size": 0.03, "gap": 0.02},
            "realistic": {"frequency": 0.50, "recency": 0.30, "velocity": 0.10, "cost": 0.05, "size": 0.03, "gap": 0.02},
        }
        if self.workload in presets:
            self.weights = presets[self.workload].copy()

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
        reuse_gap = (
            item.last_accessed - item.previous_accessed
            if item.previous_accessed is not None else self.max_time_window
        )

        seq_age = max(self.request_number - getattr(item, "last_sequence", 0), 0)
        rec_scale = 4.0 if self.workload == "spike" else 15.0
        seq_recency = 1.0 / (1.0 + seq_age / rec_scale)

        return {
            "frequency_norm": min(math.log1p(float(item.frequency)) / math.log1p(max(self.max_frequency_seen, 10.0)), 1.0),
            "recency_norm": seq_recency,
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

    def heuristic_score(self, item: CacheObject) -> float:
        """Strong multi-factor heuristic with dynamic frequency aging and recency protection."""
        now = time()
        age = max(now - item.last_accessed, 0.0)
        seq_age = max(self.request_number - getattr(item, "last_sequence", 0), 0)

        # In spike workloads, decay stale keys quickly so new bursts enter and stay
        if self.workload == "spike":
            rec_scale = 3.0
            age_scale = 2.0
        else:
            rec_scale = 15.0
            age_scale = 25.0

        # 1. Recency component: blends sequence recency (fast in-memory) and wall-clock decay
        recency_seq = 1.0 / (1.0 + seq_age / rec_scale)
        recency_time = 1.0 / (1.0 + age / 5.0)
        recency_factor = 0.80 * recency_seq + 0.20 * recency_time

        # 2. Dynamic Frequency Aging: stale popularity decays so dead hot keys are evicted
        aging_factor = 1.0 / (1.0 + seq_age / age_scale)
        effective_freq = 1.0 + (float(item.frequency) - 1.0) * aging_factor
        freq_factor = min(math.log1p(effective_freq) / math.log1p(max(self.max_frequency_seen, 8.0)), 1.0)
        if effective_freq >= 1.5:
            freq_factor = 0.35 + 0.65 * freq_factor

        # 3. Access velocity & burst
        recent_count = sum(t >= now - 10.0 for t in item.access_times)
        velocity_factor = min(recent_count / 5.0, 1.0)
        if self.workload == "spike" and seq_age <= 1:
            velocity_factor = max(velocity_factor, 0.7)
        elif seq_age <= 2 and len(item.access_times) >= 2:
            velocity_factor = max(velocity_factor, 0.6)

        # 4. Retrieval Cost factor (normalized [0, 1])
        cost_factor = min(max(float(item.cost), 0.0) / self.max_cost, 1.0)

        # 5. Size factor: smaller objects get slight preference
        size_factor = 512.0 / (512.0 + max(float(item.size), 1.0))

        # 6. Reuse gap factor
        if item.previous_accessed is not None:
            gap = max(item.last_accessed - item.previous_accessed, 0.0)
            gap_factor = 1.0 / (1.0 + gap / 10.0)
        else:
            gap_factor = 0.5

        # Weighted combination
        h_score = (
            self.weights.get("frequency", 0.35) * freq_factor +
            self.weights.get("recency", 0.30) * recency_factor +
            self.weights.get("velocity", 0.15) * velocity_factor +
            self.weights.get("cost", 0.10) * cost_factor +
            self.weights.get("size", 0.05) * size_factor +
            self.weights.get("gap", 0.05) * gap_factor
        )
        return min(max(h_score, 0.05), 0.98)


    def ml_score(self, item: CacheObject) -> float:
        """Predict reuse probability from the online River regression model."""
        if self.model is None:
            return 0.5
        features = self.features(item)
        try:
            raw_prediction = float(self.model.predict_one(features) or 0.0)
        except Exception:
            raw_prediction = 0.5
        return min(max(raw_prediction, 0.0), 1.0)

    def score(self, item: CacheObject) -> float:
        """Hybrid adaptive score combining ML prediction with heuristic fallback based on confidence."""
        h_score = self.heuristic_score(item)
        ml_pred = self.ml_score(item)

        # Confidence ramps smoothly with training samples and prediction accuracy
        accuracy_multiplier = max(self.ml_prediction_accuracy, 0.5)
        sample_progress = min(self.training_samples / 50.0, 1.0)
        confidence = min(0.70, sample_progress * 0.70 * accuracy_multiplier)

        # Dual-phase blend: cold-start is 100% heuristic; trained phase smoothly blends ML
        blended = (1.0 - confidence) * h_score + confidence * ml_pred
        final_score = min(max(blended, 0.02), 0.98)

        self.prediction_scores.append(final_score)
        if len(self.prediction_scores) > 500:
            self.prediction_scores = self.prediction_scores[-500:]
        return final_score

    def begin_request(self) -> None:
        """Advance the online reuse window and train observations that expired."""
        self.request_number += 1

        # Train expired observations
        while self.pending_observations and self.pending_observations[0].expires_at <= self.request_number:
            obs = self.pending_observations.popleft()
            # Clean up pending_by_key index
            key_list = self.pending_by_key.get(obs.key)
            if key_list and obs in key_list:
                key_list.remove(obs)
                if not key_list:
                    self.pending_by_key.pop(obs.key, None)

            self._learn(obs.features, obs.future_hits, obs.cost, obs.prediction)

    def track_new_item(self, item: CacheObject) -> None:
        """Start a deferred reuse observation for a newly fetched/inserted item."""
        self.obs_counter += 1
        prediction = self.score(item)
        snapshot_features = self.features(item)
        expires_at = self.request_number + self.reuse_window

        obs = PendingObservation(
            obs_id=self.obs_counter,
            key=item.key,
            features=snapshot_features,
            expires_at=expires_at,
            prediction=prediction,
            future_hits=0,
            cost=float(item.cost),
        )
        self.pending_observations.append(obs)
        self.pending_by_key.setdefault(item.key, []).append(obs)

        # Bound pending queue size
        if len(self.pending_observations) > 200:
            oldest = self.pending_observations.popleft()
            k_list = self.pending_by_key.get(oldest.key)
            if k_list and oldest in k_list:
                k_list.remove(oldest)
            self._learn(oldest.features, oldest.future_hits, oldest.cost, oldest.prediction)

    def track_reuse(self, key: str, item: CacheObject | None = None) -> None:
        """Record hits during the observation window for all pending observations of this key."""
        matching_obs = self.pending_by_key.get(key)
        if matching_obs:
            for obs in matching_obs:
                obs.future_hits += 1

    def _learn(self, features: dict[str, float], future_hits: int, cost: float,
               prediction: float) -> None:
        """Calibrated streaming update for the online ML model."""
        if self.model is None:
            return

        # Target represents future reuse value:
        # Reused items receive a clear positive signal [0.65, 1.0], non-reused receive 0.05
        if future_hits >= 1:
            hit_bonus = min(future_hits * 0.15, 0.30)
            cost_bonus = min((cost / self.max_cost) * 0.15, 0.15)
            reuse_value = min(0.60 + hit_bonus + cost_bonus, 1.0)
        else:
            reuse_value = 0.05

        try:
            self.model.learn_one(features, reuse_value)
            self.training_samples += 1
            self.labeled_predictions += 1
            is_accurate = int(abs(prediction - reuse_value) <= 0.30)
            self.correct_predictions += is_accurate
            self.reuse_probability_error += abs(prediction - reuse_value)
        except Exception:
            pass

    @property
    def ml_prediction_accuracy(self) -> float:
        return (
            self.correct_predictions / self.labeled_predictions
            if self.labeled_predictions else 0.70
        )

    @property
    def average_prediction_score(self) -> float:
        return (sum(self.prediction_scores) / len(self.prediction_scores)
                if self.prediction_scores else 0.5)

    def learning_metrics(self) -> dict[str, float | int]:
        confidence = min(0.70, (self.training_samples / 50.0) * max(self.ml_prediction_accuracy, 0.5))
        return {
            "training_samples": self.training_samples,
            "pending_labels": len(self.pending_observations),
            "average_prediction_score": self.average_prediction_score,
            "ml_prediction_accuracy": self.ml_prediction_accuracy,
            "reuse_prediction_quality": (
                1.0 - (self.reuse_probability_error / self.labeled_predictions)
                if self.labeled_predictions else 0.70
            ),
            "model_confidence": confidence,
        }

