import time


class BackendSimulator:
    """
    Simulates backend APIs with different latency & cost
    """

    def fetch(self, key):
        if key % 5 == 0:
            latency = 0.05   # slow (50ms)
            cost = 5
        else:
            latency = 0.005  # fast (5ms)
            cost = 1

        time.sleep(latency)

        return f"value_{key}", latency, cost


# ✅ TEST BLOCK (important)
if __name__ == "__main__":
    backend = BackendSimulator()

    print("FAST:", backend.fetch(3))
    print("SLOW:", backend.fetch(10))