"""Deterministic traffic patterns for repeatable comparisons."""
import random


def generate_workload(kind: str, length: int = 200, seed: int = 42) -> list[str]:
    """Return keys for steady, spike, or gradually shifting traffic."""
    rng = random.Random(seed)
    if kind == "steady":
        pattern = ["B", "A", "E", "D", "D", "C", "B", "B", "G", "A",
                   "A", "B", "D", "D", "A"]
        return [pattern[index % len(pattern)] for index in range(length)]
    if kind == "spike":
        workload = []
        block_size = 15
        for block in range((length + block_size - 1) // block_size):
            hot_keys = [f"hot-{block % 5}-{index}" for index in range(4)]
            cold_keys = [f"cold-{block}-{index}" for index in range(3)]
            block_keys = hot_keys + cold_keys
            block_weights = [8, 6, 4, 3, 1, 1, 1]
            workload.extend(rng.choices(block_keys, weights=block_weights, k=block_size))
        return workload[:length]
    if kind == "gradual":
        stages = [
            ["A", "B", "A", "C"],
            ["A", "B", "D", "A", "E"],
            ["A", "F", "G", "A", "B", "H"],
        ]
        pattern = stages[0] + stages[1] + stages[2]
        return [pattern[index % len(pattern)] for index in range(length)]
    raise ValueError("kind must be steady, spike, or gradual")
