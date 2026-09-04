"""CLI benchmark comparing cache policies against identical traffic."""
import argparse
from time import perf_counter
from backend.cache.cache_manager import AdaptiveCacheManager
from backend.metrics.metrics import Metrics
from backend.workloads.backend_simulator import fetch_data
from backend.workloads.workload_generator import generate_workload


def run(algorithm: str, workload: list[str], workload_type: str, capacity: int) -> dict:
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workload", choices=["steady", "spike", "gradual"], default="spike")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--capacity", type=int, default=25)
    args = parser.parse_args()
    workload = generate_workload(args.workload, args.requests)
    print(f"Benchmark: {args.workload} ({args.requests} requests)")
    for algorithm in ("lru", "lfu", "gds", "adaptive"):
        result = run(algorithm, workload, args.workload, args.capacity)
        print(f"{algorithm:8} hit_rate={result['hit_rate']:.1%}  "
              f"avg_latency={result['average_latency_ms']:.2f}ms  cost={result['cost']:.2f}")


if __name__ == "__main__":
    main()
