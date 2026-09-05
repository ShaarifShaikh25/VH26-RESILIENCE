import time

from backend.cache.cache_manager import AdaptiveCacheManager
from backend.workloads.backend_simulator import fetch_data


ALGORITHMS = ["lru", "lfu", "gds", "adaptive"]

ACCESS_PATTERNS = {
    "steady": [
        "user:1001", "product:2001", "api:/users/1001", "product:2002", "product:2003",
        "user:1001", "product:2001", "api:/users/1002",
        "user:1001", "product:2001", "product:2004",
        "user:1001", "product:2001", "api:/users/1003", "product:2005",
        "user:1001", "product:2001", "product:2006",
        "user:1001", "product:2001", "api:/users/1004", "product:2007",
        "user:1001", "product:2001", "api:/users/1001", "product:2002", "product:2003",
    ],

    "spike": [
        "user:1001", "product:2001", "api:/users/1001", "product:2002", "product:2003",
        "product:2001", "product:2001", "product:2001", "product:2001",
        "api:/users/1001", "api:/users/1001", "api:/users/1001",
        "product:2001", "product:2001", "product:2001",
        "product:2010", "api:/users/1010", "product:2011",
        "product:2001", "product:2001", "product:2001", "api:/users/1001", "api:/users/1001",
        "product:2001", "product:2001", "product:2001",
    ],

    "gradual": [
        "user:1001", "product:2001", "api:/users/1001",
        "user:1001", "product:2001", "api:/users/1001", "product:2002",
        "user:1001", "product:2001", "api:/users/1001", "product:2002", "product:2003",
        "user:1001", "product:2001", "api:/users/1001", "product:2002", "product:2003", "product:2004",
        "user:1001", "product:2001", "api:/users/1001", "product:2002", "product:2003", "product:2004", "api:/users/1002",
        "user:1001", "product:2001", "api:/users/1001", "product:2002", "product:2003", "product:2004", "api:/users/1002", "product:2005",
    ],
}


def run_benchmark(algorithm, workload):
    cache = AdaptiveCacheManager(algorithm, 5)

    if algorithm == "adaptive":
        cache.set_workload(workload)

    # Initial population
    initial_keys = ["user:1001", "product:2001", "api:/users/1001", "product:2002", "product:2003"]
    for key in initial_keys:
        value, cost = fetch_data(key)
        cache.put(key, value, cost)

    hits = 0
    misses = 0
    cache.evictions = 0
    cache.refreshes = 0

    start = time.perf_counter()

    for key in ACCESS_PATTERNS[workload]:
        if cache.get(key) is None:
            misses += 1
            value, cost = fetch_data(key)
            cache.put(key, value, cost)
        else:
            hits += 1

    elapsed_ms = (time.perf_counter() - start) * 1000

    total = hits + misses
    hit_rate = (hits / total) * 100 if total else 0

    return hits, misses, hit_rate, cache.evictions, cache.refreshes, elapsed_ms


print()
print("FINAL CACHE BENCHMARK")
print("=" * 88)

for workload in ACCESS_PATTERNS:

    print()
    print(f"WORKLOAD: {workload.upper()}")
    print("-" * 88)

    print(
        f"{'Algorithm':<10} | "
        f"{'Hits':>6} | "
        f"{'Misses':>6} | "
        f"{'Hit Rate':>10} | "
        f"{'Evictions':>9} | "
        f"{'Refreshes':>9} | "
        f"{'Time(ms)':>10}"
    )

    print("-" * 88)

    for algorithm in ALGORITHMS:

        try:
            hits, misses, hit_rate, evictions, refreshes, elapsed = run_benchmark(
                algorithm,
                workload,
            )

            print(
                f"{algorithm.upper():<10} | "
                f"{hits:>6} | "
                f"{misses:>6} | "
                f"{hit_rate:>9.2f}% | "
                f"{evictions:>9} | "
                f"{refreshes:>9} | "
                f"{elapsed:>10.2f}"
            )

        except Exception as e:
            print(
                f"{algorithm.upper():<10} | "
                f"ERROR: {type(e).__name__}: {e}"
            )

print()
print("=" * 88)
print("BENCHMARK COMPLETE")