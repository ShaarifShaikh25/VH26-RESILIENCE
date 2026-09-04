"""Deterministic traffic patterns for repeatable comparisons."""
import random


def generate_workload(kind: str, length: int = 200, seed: int = 7) -> list[str]:
    """Return keys for steady, spike, or gradually shifting traffic."""
    rng = random.Random(seed)
    if kind == "steady":
        return [f"item-{rng.randrange(20)}" for _ in range(length)]
    if kind == "spike":
        first = [f"item-{rng.randrange(80)}" for _ in range(length // 2)]
        return first + [f"hot-{rng.randrange(5)}" for _ in range(length - len(first))]
    if kind == "gradual":
        return [f"item-{rng.randrange(5 + (i * 40 // length))}" for i in range(length)]
    raise ValueError("kind must be steady, spike, or gradual")
