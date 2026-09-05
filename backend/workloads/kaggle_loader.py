"""Kaggle e-commerce data loader and chronological cache request adapter."""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Iterator

import pandas as pd

DATASET = "mkechinov/ecommerce-behavior-data-from-multi-category-store"
REQUIRED_COLUMNS = ("event_time", "event_type", "product_id")
OPTIONAL_COLUMNS = ("user_id", "category_id", "category_code")
EVENT_COSTS = {"view": 1.0, "cart": 5.0, "purchase": 10.0}
logger = logging.getLogger("adaptive_cache.kaggle")


def _find_csv(directory: Path) -> Path:
    files = sorted(directory.rglob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {directory}")
    return files[0]


def download_dataset(data_dir: str | Path = "data/kaggle") -> Path:
    """Download and extract the Kaggle dataset using the user's kaggle.json."""
    target = Path(data_dir)
    target.mkdir(parents=True, exist_ok=True)
    existing = list(target.rglob("*.csv"))
    if existing:
        csv_path = sorted(existing)[0]
        logger.info("Kaggle CSV found: %s", csv_path)
        return csv_path

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as exc:
        raise RuntimeError("Install kaggle and configure ~/.kaggle/kaggle.json") from exc

    if not os.getenv("KAGGLE_CONFIG_DIR") and not (
        Path.home() / ".kaggle" / "kaggle.json"
    ).exists():
        logger.warning("Kaggle credentials not found")
        raise RuntimeError(
            "Kaggle credentials not found. Place kaggle.json in ~/.kaggle "
            "or set KAGGLE_CONFIG_DIR."
        )

    logger.info("Kaggle credentials found; downloading dataset %s", DATASET)
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(DATASET, path=str(target), unzip=True)
    csv_path = _find_csv(target)
    logger.info("Kaggle CSV found after download: %s", csv_path)
    return csv_path


def load_events(
    csv_path: str | Path | None = None,
    data_dir: str | Path = "data/kaggle",
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Load only cache-relevant columns and return chronological events."""
    path = Path(csv_path) if csv_path else download_dataset(data_dir)
    logger.info("Loading Kaggle events from %s", path)
    header = pd.read_csv(path, nrows=0).columns.tolist()
    columns = [column for column in REQUIRED_COLUMNS + OPTIONAL_COLUMNS if column in header]
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    frame = pd.read_csv(path, usecols=columns, nrows=max_rows)
    frame["event_time"] = pd.to_datetime(frame["event_time"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["event_time", "product_id", "event_type"])
    frame = frame[frame["event_type"].isin(EVENT_COSTS)]
    frame = frame.sort_values("event_time", kind="stable").reset_index(drop=True)
    logger.info("Loaded %d Kaggle events", len(frame))
    return frame


def _size_for(product_id: object, category_id: object | None) -> int:
    """Generate stable, bounded memory usage for a product response."""
    source = f"{product_id}:{category_id or ''}".encode()
    return 128 + int.from_bytes(hashlib.blake2b(source, digest_size=2).digest(), "big") % 896


def generate_requests(frame: pd.DataFrame) -> Iterator[tuple[str, dict, float, int]]:
    """Yield chronological cache requests from Kaggle event rows."""
    for row in frame.itertuples(index=False):
        product_id = int(row.product_id) if str(row.product_id).isdigit() else str(row.product_id)
        event_type = str(row.event_type)
        value = {
            "product_id": product_id,
            "event": event_type,
            "timestamp": row.event_time.isoformat(),
        }
        if hasattr(row, "user_id") and pd.notna(row.user_id):
            value["user_id"] = int(row.user_id) if str(row.user_id).isdigit() else str(row.user_id)
        category_id = getattr(row, "category_id", None)
        if category_id is not None and pd.notna(category_id):
            value["category_id"] = int(category_id) if str(category_id).isdigit() else str(category_id)
        size = _size_for(product_id, category_id)
        value["size"] = size
        yield f"product:{product_id}", value, EVENT_COSTS[event_type], size
