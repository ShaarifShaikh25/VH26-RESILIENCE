from backend.workloads.backend_simulator import BackendSimulator
from backend.workloads.workload_generator import WorkloadGenerator
from backend.metrics.metrics import Metrics

from backend.algorithms.lru import LRUCache
from backend.algorithms.lfu import LFUCache
from backend.algorithms.gds import GDSCache
from backend.algorithms.adaptive import AdaptiveCache


class Benchmark:
    def __init__(self, cache, workload):
        self.cache = cache
        self.workload = workload
        self.backend = BackendSimulator()
        self.metrics = Metrics()

    def run(self):
        for key in self.workload:
            value = self.cache.get(key)

            if value is not None:
                self.metrics.record_hit()
                latency = 0.001  # cache hit
                cost = 0
            else:
                value, latency, cost = self.backend.fetch(key)
                self.cache.put(key, value, cost)

            self.metrics.record_request(latency, cost)

        return self.metrics.results()


def run_comparison(workload_type="spike", requests=100, capacity=20):
    """Return metrics for every policy on one selected workload."""
    generator = WorkloadGenerator()
    workloads = {
        "steady": generator.steady,
        "spike": generator.spike,
        "gradual": generator.gradual,
    }
    if workload_type not in workloads:
        raise ValueError("workload_type must be steady, spike, or gradual")

    workload = workloads[workload_type](requests)
    algorithms = {
        "LRU": LRUCache(capacity),
        "LFU": LFUCache(capacity),
        "GDS": GDSCache(capacity),
        "Adaptive": AdaptiveCache(capacity),
    }
    return [{"algorithm": name, **Benchmark(cache, workload).run()}
            for name, cache in algorithms.items()]


def run_all():
    wg = WorkloadGenerator()

    # 🔁 Change workload here
    workload = wg.spike()

    algorithms = {
        "LRU": LRUCache(20),
        "LFU": LFUCache(20),
        "GDS": GDSCache(20),
        "Adaptive": AdaptiveCache(20),
    }

    print("\n=== Benchmark Results ===")
    print(f"{'Algorithm':<10} | {'Hit Rate':<10} | {'Latency':<10} | {'Cost':<10}")
    print("-" * 50)

    for name, cache in algorithms.items():
        bench = Benchmark(cache, workload)
        result = bench.run()

        print(
            f"{name:<10} | "
            f"{result['hit_rate']:.2f}     | "
            f"{result['avg_latency']:.4f}   | "
            f"{result['cost']}"
        )


if __name__ == "__main__":
    run_all()
