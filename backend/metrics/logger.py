"""Central logging helper for cache decisions."""
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("adaptive_cache")


def log_decision(key: str, decision: str, algorithm: str) -> None:
    logger.info("key=%s decision=%s algorithm=%s", key, decision, algorithm)
