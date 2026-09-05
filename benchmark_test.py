import time

from backend.cache.cache_manager import AdaptiveCacheManager


def prepare_cache(workload):
    cache = AdaptiveCacheManager("adaptive", 3)
    cache.set_workload(workload)

    cache.put("user:1001", {"id": 1001, "type": "user", "data": {"name": "User 1001", "email": "user1001@example.com", "score": 91}, "timestamp": time.time()})
    cache.put("product:2001", {"id": 2001, "type": "product", "data": {"name": "Product 2001", "email": "catalog-2001@example.com", "score": 78}, "timestamp": time.time()})
    cache.put("api:/users/1002", {"id": 1002, "type": "user-api", "data": {"name": "User 1002", "email": "user1002@example.com", "score": 84}, "timestamp": time.time()})

    # Create different access profiles for each workload
    if workload == "steady":
        # a = very frequently used
        # b = moderately used
        # c = rarely used
        for _ in range(8):
            cache.get("user:1001")

        for _ in range(4):
            cache.get("product:2001")

        cache.get("api:/users/1002")

        cache.policy.items["api:/users/1002"].last_accessed = time.time() - 1000

    elif workload == "spike":
        # b = currently hot/recent
        # c = moderately recent
        # a = old
        for _ in range(6):
            cache.get("product:2001")

        for _ in range(2):
            cache.get("api:/users/1002")

        cache.policy.items["user:1001"].last_accessed = time.time() - 1000
        cache.policy.items["api:/users/1002"].last_accessed = time.time() - 10
        cache.policy.items["product:2001"].last_accessed = time.time()

    elif workload == "gradual":
        # Balanced workload
        for _ in range(5):
            cache.get("user:1001")

        for _ in range(3):
            cache.get("product:2001")

        for _ in range(2):
            cache.get("api:/users/1002")

        cache.policy.items["user:1001"].last_accessed = time.time() - 5
        cache.policy.items["product:2001"].last_accessed = time.time() - 50
        cache.policy.items["api:/users/1002"].last_accessed = time.time() - 500

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
    print(f"Online model training samples: {cache.scorer.training_samples}")

    print("Scores before eviction:")
    print(scores_before)

    # Force one eviction
    cache.put("product:2999", {"id": 2999, "type": "product", "data": {"name": "Product 2999", "email": "catalog-2999@example.com", "score": 66}, "timestamp": time.time()})

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