class Metrics:
    """
    Tracks cache performance metrics
    """

    def __init__(self):
        self.hits = 0
        self.total_requests = 0
        self.total_latency = 0
        self.total_cost = 0

    def record_hit(self):
        self.hits += 1

    def record_request(self, latency, cost):
        self.total_requests += 1
        self.total_latency += latency
        self.total_cost += cost

    def results(self):
        hit_rate = self.hits / self.total_requests if self.total_requests else 0
        avg_latency = self.total_latency / self.total_requests if self.total_requests else 0

        return {
            "hit_rate": hit_rate,
            "avg_latency": avg_latency,
            "cost": self.total_cost
        }


# ✅ TEST BLOCK
if __name__ == "__main__":
    m = Metrics()

    # simulate 5 requests
    m.record_request(0.01, 1)
    m.record_request(0.02, 2)
    m.record_hit()
    m.record_request(0.01, 0)
    m.record_hit()
    m.record_request(0.03, 3)

    print(m.results())