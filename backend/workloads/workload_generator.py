import random


class WorkloadGenerator:
    """
    Generates different traffic patterns
    """

    def steady(self, n=100):
        # uniform random traffic
        return [random.randint(1, 50) for _ in range(n)]

    def spike(self, n=100):
        # sudden hotspot traffic
        workload = []
        for i in range(n):
            if 40 < i < 60:
                workload.append(random.randint(1, 10))  # hot keys
            else:
                workload.append(random.randint(1, 50))
        return workload

    def gradual(self, n=100):
        # slowly changing pattern
        workload = []
        for i in range(n):
            max_key = int(10 + (i / n) * 40)
            workload.append(random.randint(1, max_key))
        return workload


# ✅ TEST BLOCK
if __name__ == "__main__":
    wg = WorkloadGenerator()

    print("STEADY :", wg.steady(10))
    print("SPIKE  :", wg.spike(20))
    print("GRADUAL:", wg.gradual(20))