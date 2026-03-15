from __future__ import annotations

from pathlib import Path

import pandas as pd

from tracepheno.io_utils import coerce_numeric_frame

KO_PATTERN = r"(?i)\b(?:ko:)?k\d{5}\b"
CONTRIB_VALUE_PRIORITY = [
    "taxon_function_abun",
    "taxon_rel_function_abun",
    "norm_taxon_function_contrib",
]


def _normalize_function_id(value: object) -> str:
    text = str(value).strip()
    if text.lower().startswith("ko:"):
        text = text.split(":", 1)[1]
    return text


def _find_column(columns: list[str], candidates: set[str]) -> str | None:
    lookup = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def _read_table_raw(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=None, engine="python")


def _validate_ko_like_index(index: pd.Index, source: str | Path) -> None:
    ko_like = index.astype(str).str.contains(KO_PATTERN, regex=True, na=False)
    if not ko_like.any():
        raise ValueError(
            f"No KEGG KO-like feature identifiers were detected in {source}. "
            "Use PICRUSt2 KO metagenome output such as pred_metagenome_unstrat.tsv.gz."
        )


def _pivot_contribution_table(frame: pd.DataFrame, source: str | Path) -> pd.DataFrame:
    columns = frame.columns.tolist()
    function_column = _find_column(columns, {"function"})
    sample_column = _find_column(columns, {"sample"})
    if function_column is None or sample_column is None:
        raise ValueError(
            "PICRUSt2 contribution table parsing requires 'function' and 'sample' columns."
        )

    value_column = _find_column(columns, set(CONTRIB_VALUE_PRIORITY))
    if value_column is None:
        numeric_candidates = [
            column
            for column in columns
            if column not in {function_column, sample_column}
            and pd.to_numeric(frame[column], errors="coerce").notna().any()
        ]
        if not numeric_candidates:
            raise ValueError(
                f"No numeric contribution column was detected in {source}."
            )
        value_column = numeric_candidates[0]

    working = frame[[function_column, sample_column, value_column]].copy()
    working[function_column] = working[function_column].map(_normalize_function_id)
    working[value_column] = pd.to_numeric(working[value_column], errors="coerce").fillna(0.0)
    wide = working.pivot_table(
        index=function_column,
        columns=sample_column,
        values=value_column,
        aggfunc="sum",
        fill_value=0.0,
    )
    wide.index.name = "function"
    wide.columns.name = None
    _validate_ko_like_index(wide.index, source)
    return wide


def read_picrust2_ko_table(path: str | Path) -> pd.DataFrame:
    frame = _read_table_raw(path)
    if frame.empty:
        raise ValueError(f"PICRUSt2 input table is empty: {path}")

    lower_columns = {column.lower() for column in frame.columns}
    if {"function", "sample"}.issubset(lower_columns):
        return _pivot_contribution_table(frame, path)

    index_column = frame.columns[0]
    frame = frame.set_index(index_column)
    frame.index = frame.index.map(_normalize_function_id)
    numeric = coerce_numeric_frame(frame, source=path)
    numeric.index.name = "function"
    numeric.columns.name = None
    numeric = numeric.groupby(level=0).sum()
    _validate_ko_like_index(numeric.index, path)
    return numeric
