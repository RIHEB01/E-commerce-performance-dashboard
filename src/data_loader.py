from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


def list_available_csvs(base_dir: Path = RAW_DIR) -> list[Path]:
    if not base_dir.exists():
        return []
    return sorted(base_dir.glob("*.csv"))


def load_csv_table(filename: str, base_dir: Path = RAW_DIR) -> pd.DataFrame:
    path = base_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Required dataset file not found: {path}")
    return pd.read_csv(path)


def ensure_processed_dir() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_processed_table(filename: str) -> pd.DataFrame:
    path = PROCESSED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Processed file not found: {path}")
    return pd.read_csv(path)


def detect_missing_tables(required: Iterable[str]) -> list[str]:
    return [name for name in required if not (RAW_DIR / name).exists()]
