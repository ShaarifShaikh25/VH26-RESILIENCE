# Adaptive Cache Management System

A small, runnable FastAPI project that compares LRU, LFU, GreedyDual-Size (GDS), and an adaptive cache policy. It uses Redis when `REDIS_URL` is reachable and automatically falls back to local memory, so it is ready for a hackathon demo without infrastructure.

## Setup

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Optional Redis:

```bash
docker run --rm -p 6379:6379 redis:7-alpine
```

Set `REDIS_URL`, `CACHE_CAPACITY`, and `CACHE_ALGORITHM` (`lru`, `lfu`, `gds`, or `adaptive`) to customize the service. Defaults are `redis://localhost:6379/0`, `100`, and `adaptive`.

## Run

```bash
# macOS/Linux
./run.sh
# Any platform
python -m uvicorn backend.main:app --reload
```

Then try `http://127.0.0.1:8000/data/product-42` twice: the second request is a cache hit. Swagger UI is available at `http://127.0.0.1:8000/docs`.

Useful API calls:

```bash
curl "http://127.0.0.1:8000/data/product-42?workload=spike"
curl http://127.0.0.1:8000/metrics
curl -X POST http://127.0.0.1:8000/algorithm/gds
```

## Benchmark and dashboard

```bash
python -m backend.benchmark.compare --workload spike --requests 200 --capacity 25
streamlit run dashboard/app.py
```

The benchmark replays one deterministic workload through each policy and prints hit rate, average request latency, and simulated backend cost. GDS uses `score = (cost / size) + L`; the adaptive policy changes its frequency, recency, cost, and size weights for steady, spike, and gradual traffic.

## Layout

- `backend/cache`: Redis adapter, cache metadata, and unified cache manager.
- `backend/algorithms`: LRU, LFU, and GDS eviction implementations.
- `backend/core`: workload-aware scoring and retain/evict/refresh decisions.
- `backend/workloads`, `metrics`, and `benchmark`: simulation, reporting, and comparison tools.
