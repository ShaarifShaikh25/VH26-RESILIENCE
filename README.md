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

The requirements install this project in editable mode, which lets Streamlit import the `backend` package when it runs `dashboard/app.py`.

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
python -m backend.benchmark.compare
streamlit run dashboard/app.py
```

The dashboard runs a selected `steady`, `spike`, or `gradual` workload through the real cache manager. It shows live hit-rate and latency history, algorithm comparisons, cache-entry metadata, and recent cache decisions.

The FastAPI service exposes the same observability data at `/metrics`, `/metrics/history`, `/cache/state`, and `/decisions`; use `POST /simulate/{workload}` to generate traffic through the API session.

## Kaggle workload

Install the Kaggle client and place the downloaded API token at `~/.kaggle/kaggle.json`:

```bash
pip install kaggle
```

The endpoint downloads the e-commerce behavior dataset on first use, extracts the relevant event columns, sorts events chronologically, and replays product requests through the active cache:

```text
GET /simulate/kaggle?requests=500
```

For local testing or an already-downloaded file, pass `csv_path`. The loader maps views, carts, and purchases to costs `1`, `5`, and `10`, respectively, and keeps the generated response size in cache metadata.

## Frontend (3D Cybernetic Interface)

The interactive 3D WebGL landing page is located in `frontend/` and built with React 18, Vite 5, React Three Fiber (Three.js), and Framer Motion.

```bash
# Run frontend dev server
npm run dev

# Or build for production
npm run build
```

## Vercel Deployment

This repository is configured to deploy both the 3D frontend and the FastAPI serverless API in a unified Vercel deployment:

1. Go to [vercel.com/new](https://vercel.com/new).
2. Import repository: `ShaarifShaikh25/VH26-RESILIENCE`.
3. Vercel automatically reads `vercel.json` and builds:
   - **Frontend static bundle** from `frontend/` -> served at `/`
   - **FastAPI serverless function** from `api/index.py` -> served at `/docs`, `/metrics`, `/api/*`, `/data/*`, etc.
4. Click **Deploy**.

## Layout

- `api/index.py`: Serverless ASGI entry point for Vercel deployment.
- `frontend/`: React + Vite + Three.js 3D Cybernetic interface and team telemetry.
- `backend/cache`: Redis adapter, cache metadata, and unified cache manager.
- `backend/algorithms`: LRU, LFU, and GDS eviction implementations.
- `backend/core`: workload-aware scoring and retain/evict/refresh decisions.
- `backend/workloads`, `metrics`, and `benchmark`: simulation, reporting, and comparison tools.
- `dashboard`: Streamlit observability control room.
