"""CLI and reusable benchmark for identical cache-policy workloads."""
import argparse
from time import perf_counter

from backend.cache.cache_manager import AdaptiveCacheManager
from backend.metrics.metrics import Metrics
from backend.workloads.backend_simulator import fetch_data
from backend.workloads.workload_generator import generate_workload


def run(algorithm: str, workload: list[str], workload_type: str, capacity: int) -> dict:
    """Measure one cache algorithm against a pre-generated workload."""
    cache, metrics = AdaptiveCacheManager(algorithm, capacity), Metrics()
    cache.set_workload(workload_type)
    for key in workload:
        started = perf_counter()
        value = cache.get(key)
        hit, cost = value is not None, 0.0
        if not hit:
            value, cost = fetch_data(key)
            cache.put(key, value, cost)
        metrics.record(hit, (perf_counter() - started) * 1000, cost)
    return metrics.snapshot()


def run_comparison(workload_type: str = "spike", requests: int = 200,
                   capacity: int = 25) -> list[dict]:
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
    parser.add_argument("--capacity", type=int, default=25)
    args = parser.parse_args()

    print(f"Benchmark: {args.workload} ({args.requests} requests)")
    for result in run_comparison(args.workload, args.requests, args.capacity):
        print(f"{result['algorithm']:8} hit_rate={result['hit_rate']:.1%}  "
              f"avg_latency={result['average_latency_ms']:.2f}ms  "
              f"cost={result['cost']:.2f}")


if __name__ == "__main__":
    main()
