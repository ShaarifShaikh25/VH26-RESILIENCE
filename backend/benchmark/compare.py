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
    warmup_started = perf_counter()
    warmup = (workload * ((warmup_requests + len(workload) - 1) // len(workload)))[:warmup_requests]
    for key in warmup:
        _send_request(cache, key, workload_type, Metrics())
    warmup_seconds = perf_counter() - warmup_started
    metrics = Metrics()
    evaluation_started = perf_counter()
    for key in workload:
        _send_request(cache, key, workload_type, metrics)
    evaluation_seconds = perf_counter() - evaluation_started
    learning = cache.learning_metrics()
    total_seconds = perf_counter() - total_started
    return {
        **metrics.snapshot(),
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
    parser.add_argument("--workload", choices=["steady", "spike", "gradual"], default="spike")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--capacity", type=int, default=5)
    args = parser.parse_args()

    print(f"Benchmark: {args.workload} ({args.requests} requests)")
    for result in run_comparison(args.workload, args.requests, args.capacity):
        print(f"{result['algorithm']} hits={result['hits']} misses={result['misses']} "
              f"hit_rate={result['hit_rate']:.1%}")
        print(f"{result['algorithm']:8} hit_rate={result['hit_rate']:.1%}  "
              f"avg_latency={result['average_latency_ms']:.2f}ms  "
              f"cost={result['cost']:.2f}")


if __name__ == "__main__":
    main()
