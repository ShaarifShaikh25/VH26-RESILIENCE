import time

from backend.cache.cache_manager import AdaptiveCacheManager


def prepare_cache(workload):
    cache = AdaptiveCacheManager("adaptive", 3)
    cache.set_workload(workload)

    cache.put("a", {"value": 1})
    cache.put("b", {"value": 2})
    cache.put("c", {"value": 3})

    # Create different access profiles for each workload
    if workload == "steady":
        # a = very frequently used
        # b = moderately used
        # c = rarely used
        for _ in range(8):
            cache.get("a")

        for _ in range(4):
            cache.get("b")

        cache.get("c")

        cache.policy.items["c"].last_accessed = time.time() - 1000

    elif workload == "spike":
        # b = currently hot/recent
        # c = moderately recent
        # a = old
        for _ in range(6):
            cache.get("b")

        for _ in range(2):
            cache.get("c")

        cache.policy.items["a"].last_accessed = time.time() - 1000
        cache.policy.items["c"].last_accessed = time.time() - 10
        cache.policy.items["b"].last_accessed = time.time()

    elif workload == "gradual":
        # Balanced workload
        for _ in range(5):
            cache.get("a")

        for _ in range(3):
            cache.get("b")

        for _ in range(2):
            cache.get("c")

        cache.policy.items["a"].last_accessed = time.time() - 5
        cache.policy.items["b"].last_accessed = time.time() - 50
        cache.policy.items["c"].last_accessed = time.time() - 500

    return cache


def run_workload(workload):
    print()
    print(f"WORKLOAD: {workload.upper()}")
    print("-" * 75)

    cache = prepare_cache(workload)

    scores_before = {
        key: round(cache.scorer.score(item), 4)
        for key, item in cache.policy.items.items()
    }

    print("Weights:")
    print(cache.scorer.weights)

    print("Scores before eviction:")
    print(scores_before)

    # Force one eviction
    cache.put("new", {"value": 99})

    print("Remaining:")
    print(list(cache.policy.items.keys()))

    print("-" * 75)


print()
print("ADAPTIVE EVICTION VALIDATION")
print("=" * 75)

for workload in ["steady", "spike", "gradual"]:
    try:
        run_workload(workload)
    except Exception as e:
        print(
            f"ERROR in {workload.upper()}: "
            f"{type(e).__name__}: {e}"
        )

print("=" * 75)