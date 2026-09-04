"""Application settings kept intentionally simple for hackathon deployment."""
from dataclasses import dataclass, field
import os


@dataclass
class Settings:
    cache_capacity: int = int(os.getenv("CACHE_CAPACITY", "100"))
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    algorithm: str = os.getenv("CACHE_ALGORITHM", "adaptive")
    weights: dict[str, float] = field(default_factory=lambda: {
        "frequency": 0.35, "recency": 0.30, "cost": 0.25, "size": 0.10,
    })
    decision_threshold: float = float(os.getenv("DECISION_THRESHOLD", "0.30"))


settings = Settings()
