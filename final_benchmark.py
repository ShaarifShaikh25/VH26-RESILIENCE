import time

from backend.cache.cache_manager import AdaptiveCacheManager


ALGORITHMS = ["lru", "lfu", "gds", "adaptive"]

ACCESS_PATTERNS = {
    "steady": [
        0, 1, 2, 3, 4,
        0, 1, 2, 5,
        0, 1, 6,
        0, 1, 2, 7,
        0, 1, 8,
        0, 1, 2, 9,
        0, 1, 2, 3, 4, 5,
    ],

    "spike": [
        0, 1, 2, 3, 4,
        1, 1, 1, 1,
        2, 2, 2,
        1, 1, 1,
        5, 6, 7,
        1, 1, 1, 2, 2,
        1, 1, 1,
    ],

    "gradual": [
        0, 1, 2,
        0, 1, 2, 3,
        0, 1, 2, 3, 4,
        0, 1, 2, 3, 4, 5,
        0, 1, 2, 3, 4, 5, 6,
        0, 1, 2, 3, 4, 5, 6, 7,
    ],
}


def run_benchmark(algorithm, workload):
    cache = AdaptiveCacheManager(algorithm, 5)

    if algorithm == "adaptive":
        cache.set_workload(workload)

    # Initial population
    for i in range(5):
        cache.put(f"key{i}", {"value": i})

    hits = 0
    misses = 0

    start = time.perf_counter()

    for key_id in ACCESS_PATTERNS[workload]:
        key = f"key{key_id}"

        if cache.get(key) is None:
            misses += 1
            cache.put(key, {"value": key_id})
        else:
            hits += 1

    elapsed_ms = (time.perf_counter() - start) * 1000

    total = hits + misses
    hit_rate = (hits / total) * 100 if total else 0

    return hits, misses, hit_rate, elapsed_ms


print()
print("FINAL CACHE BENCHMARK")
print("=" * 85)

for workload in ACCESS_PATTERNS:

    print()
    print(f"WORKLOAD: {workload.upper()}")
    print("-" * 85)

    print(
        f"{'Algorithm':<12}"
        f"{'Hits':>10}"
        f"{'Misses':>10}"
        f"{'Hit Rate':>14}"
        f"{'Time(ms)':>14}"
    )

    print("-" * 85)

    for algorithm in ALGORITHMS:

        try:
            hits, misses, hit_rate, elapsed = run_benchmark(
                algorithm,
                workload,
            )

            print(
                f"{algorithm.upper():<12}"
                f"{hits:>10}"
                f"{misses:>10}"
                f"{hit_rate:>13.2f}%"
                f"{elapsed:>14.2f}"
            )

        except Exception as e:
            print(
                f"{algorithm.upper():<12}"
                f"ERROR: {type(e).__name__}: {e}"
            )

print()
print("=" * 85)
print("BENCHMARK COMPLETE")