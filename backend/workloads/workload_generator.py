"""Deterministic traffic patterns for repeatable comparisons."""
import random
import math


def generate_workload(kind: str, length: int = 200, seed: int = 42) -> list[str]:
    """Return keys for steady, spike, or gradually shifting traffic."""
    rng = random.Random(seed)
    if kind == "steady":
        pattern = [
            "user:1001", "product:2001", "api:/users/1001", "product:2002",
            "product:2002", "user:1002", "user:1001", "user:1001",
            "api:/users/1002", "product:2001", "product:2001", "user:1001",
            "product:2002", "product:2002", "product:2001",
        ]
        return [pattern[index % len(pattern)] for index in range(length)]
    if kind == "spike":
        workload = []
        block_size = 15
        for block in range((length + block_size - 1) // block_size):
            hot_keys = [
                f"api:/users/{1000 + (block % 5) * 10 + index}"
                for index in range(4)
            ]
            cold_keys = [
                f"product:{3000 + block * 10 + index}" for index in range(3)
            ]
            block_keys = hot_keys + cold_keys
            block_weights = [8, 6, 4, 3, 1, 1, 1]
            workload.extend(rng.choices(block_keys, weights=block_weights, k=block_size))
        return workload[:length]
    if kind == "realistic":
        stable = [f"product:{2000 + index}" for index in range(12)]
        volatile = [f"product:{5000 + index}" for index in range(80)]
        workload = []
        for index in range(length):
            phase = index // 40
            if phase % 3 == 1 and index % 5 == 0:
                workload.append(volatile[(index * 7) % len(volatile)])
            else:
                rank = 1 + int((rng.random() ** 2) * len(stable))
                workload.append(stable[min(rank - 1, len(stable) - 1)])
            if index % 17 == 0:
                workload.extend(stable[:3])
        return workload[:length]
    if kind == "gradual":
        stages = [
            ["user:1101", "product:2101", "user:1101", "api:/users/1102"],
            ["user:1101", "product:2101", "product:2102", "user:1101", "product:2103"],
            ["user:1101", "product:2201", "api:/users/1201", "user:1101", "product:2202", "api:/users/1202"],
        ]
        pattern = stages[0] + stages[1] + stages[2]
        return [pattern[index % len(pattern)] for index in range(length)]
    raise ValueError("kind must be steady, spike, or gradual")
