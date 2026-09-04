"""Central logging helper for cache decisions."""
import logging
from collections import deque
from time import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("adaptive_cache")
_recent_decisions: deque[dict] = deque(maxlen=200)


def log_decision(key: str, decision: str, algorithm: str, score: float | None = None) -> None:
    """Log and retain a compact cache event for API and dashboard consumers."""
    event = {
        "timestamp": time(), "key": key, "decision": decision.upper(),
        "algorithm": algorithm.upper(), "score": score,
    }
    _recent_decisions.append(event)
    logger.info("key=%s decision=%s algorithm=%s score=%s", key, decision, algorithm, score)


def recent_decisions(limit: int = 50) -> list[dict]:
    """Return recent cache events in newest-first order."""
    return list(reversed(_recent_decisions))[:limit]
