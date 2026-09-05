"""CLI and reusable benchmark for identical cache-policy workloads."""
import argparse
from time import perf_counter

from backend.cache.cache_manager import AdaptiveCacheManager
from backend.metrics.metrics import Metrics
from backend.workloads.backend_simulator import fetch_data
from backend.workloads.workload_generator import generate_workload

HIT_LATENCY_MS = 1.0
MISS_LATENCY_MS = 10.0


def _send_request(cache, key: str, workload_type: str, metrics: Metrics) -> None:
    counters = getattr(cache, "_benchmark_counters", None)
    if counters is not None:
        counters["get_operations"] += 1
    value = cache.get(key)
    hit, cost = value is not None, 0.0
    if not hit:
        # Benchmark latency is represented by HIT_LATENCY_MS/MISS_LATENCY_MS;
        # avoid sleeping in the simulator while measuring policy behavior.
        value, cost = fetch_data(key, delay_ms=0.0)
        if counters is not None:
            counters["put_operations"] += 1
        cache.put(key, value, cost)
    metrics.record(hit, HIT_LATENCY_MS if hit else MISS_LATENCY_MS, cost)


def run(algorithm: str, workload: list[str], workload_type: str, capacity: int,
        warmup_requests: int = 1000) -> dict:
    """Warm each policy before measuring the requested workload."""
    total_started = perf_counter()
    init_started = perf_counter()
    cache, metrics = AdaptiveCacheManager(algorithm, capacity), Metrics()
    initialization_seconds = perf_counter() - init_started
    cache._benchmark_counters = {
        "get_operations": 0,
        "put_operations": 0,
    }
    cache.set_workload(workload_type)
    cache.verbose_logging = False
    warmup_started = perf_counter()
    warmup = (workload * ((warmup_requests + len(workload) - 1) // len(workload)))[:warmup_requests]
    for key in warmup:
        _send_request(cache, key, workload_type, Metrics())
    warmup_seconds = perf_counter() - warmup_started

    metrics = Metrics()
    cache.evictions = 0
    cache.refreshes = 0
    cache.decision_counts = {"retain": 0, "evict": 0, "refresh": 0}
    cache.verbose_logging = True

    evaluation_started = perf_counter()
    for key in workload:
        _send_request(cache, key, workload_type, metrics)
    evaluation_seconds = perf_counter() - evaluation_started
    learning = cache.learning_metrics()
    total_seconds = perf_counter() - total_started
    return {
        **metrics.snapshot(),
        "evictions": cache.evictions,
        "refreshes": cache.refreshes,
        "decision_counts": dict(cache.decision_counts),
        "warmup_phase": learning.get("warmup_phase", False),
        "training_samples": learning.get("training_samples", 0),
        "initialization_seconds": initialization_seconds,
        "warmup_seconds": warmup_seconds,
        "evaluation_seconds": evaluation_seconds,
        "total_seconds": total_seconds,
        "requests_processed": len(warmup) + len(workload),
        "get_operations": cache._benchmark_counters["get_operations"],
        "put_operations": cache._benchmark_counters["put_operations"],
        "ml_training_operations": learning.get("training_samples", 0),
    }


def run_comparison(workload_type: str = "spike", requests: int = 200,
                   capacity: int = 5) -> list[dict]:
    """Return LRU, LFU, GDS, and Adaptive results for one workload type."""
    workload = generate_workload(workload_type, requests)
    return [
        {"algorithm": algorithm.upper(),
         **run(algorithm, workload, workload_type, capacity)}
        for algorithm in ("lru", "lfu", "gds", "adaptive")
    ]


def main() -> None:
    """Run the comparison from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--workload", choices=["steady", "spike", "gradual", "realistic"], default="spike")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--capacity", type=int, default=5)
    args = parser.parse_args()

    print(f"\nBenchmark: {args.workload.upper()} ({args.requests} requests, capacity={args.capacity})")
    results = run_comparison(args.workload, args.requests, args.capacity)
    print("\n" + "=" * 90)
    print(f"{'Algorithm':<10} | {'Hits':>6} | {'Misses':>6} | {'Hit Rate':>10} | {'Evictions':>9} | {'Refreshes':>9} | {'Latency':>10} | {'Cost':>8}")
    print("-" * 90)
    for r in results:
        print(f"{r['algorithm']:<10} | {r['hits']:>6} | {r['misses']:>6} | {r['hit_rate']:>9.1%} | {r['evictions']:>9} | {r['refreshes']:>9} | {r['average_latency_ms']:>8.2f}ms | {r['cost']:>8.2f}")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    main()
