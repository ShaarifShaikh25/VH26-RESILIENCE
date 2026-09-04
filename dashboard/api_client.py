"""HTTP client for the FastAPI-backed Streamlit dashboard."""
import os

import requests


class DashboardAPI:
    """Call the running FastAPI service used by the dashboard."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = (base_url or os.getenv("CACHE_API_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs):
        try:
            response = requests.request(
                method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"FastAPI backend unavailable at {self.base_url}: {exc}"
            ) from exc

    def overview(self) -> dict:
        return self._request("GET", "/metrics")

    def history(self) -> list[dict]:
        return self._request("GET", "/metrics/history")

    def cache_state(self) -> list[dict]:
        return self._request("GET", "/cache/state")

    def decisions(self, limit: int = 50) -> list[dict]:
        return self._request("GET", "/decisions", params={"limit": limit})

    def select_algorithm(self, algorithm: str) -> dict:
        return self._request("POST", f"/algorithm/{algorithm}")

    def simulate(self, workload: str, requests_count: int) -> dict:
        return self._request(
            "POST", f"/simulate/{workload}", params={"requests": requests_count}
        )

    def benchmark(self, workload: str, requests_count: int, capacity: int = 5) -> list[dict]:
        return self._request(
            "POST",
            f"/benchmark/{workload}",
            params={"requests": requests_count, "capacity": capacity},
        )