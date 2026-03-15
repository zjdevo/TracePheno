from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_table(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=None, engine="python")
    if frame.empty:
        raise ValueError(f"Input table is empty: {path}")
    index_name = frame.columns[0]
    frame = frame.set_index(index_name)
    frame.index = frame.index.astype(str)
    return frame


def read_numeric_matrix(path: str | Path) -> pd.DataFrame:
    frame = read_table(path)
    return coerce_numeric_frame(frame, source=path)


def coerce_numeric_frame(frame: pd.DataFrame, source: str | Path | None = None) -> pd.DataFrame:
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    numeric = numeric.loc[:, numeric.notna().any(axis=0)]
    if numeric.empty or numeric.isna().all().all():
        label = source if source is not None else "input frame"
        raise ValueError(f"No numeric values were detected in {label}")
    numeric = numeric.fillna(0.0)
    return numeric


def write_table(frame: pd.DataFrame, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, sep="\t")


def ensure_output_dir(path: str | Path) -> Path:
    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    column_sums = frame.sum(axis=0)
    safe_sums = column_sums.where(column_sums > 0, 1.0)
    return frame.divide(safe_sums, axis=1)
