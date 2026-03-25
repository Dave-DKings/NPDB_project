"""File loading and schema profiling helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DATA_PATH


def load_npdb_csv(path: Path | str = DATA_PATH, low_memory: bool = False) -> pd.DataFrame:
    """Load the NPDB CSV from disk."""
    return pd.read_csv(path, low_memory=low_memory)


def build_column_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize dtype, missingness, and distinct counts for each column."""
    profile = pd.DataFrame(
        {
            "column": df.columns,
            "dtype": [str(dtype) for dtype in df.dtypes],
            "non_null": df.notna().sum().values,
            "null_count": df.isna().sum().values,
            "null_pct": (df.isna().mean() * 100).round(2).values,
            "nunique": df.nunique(dropna=True).values,
        }
    )
    return profile.sort_values(["null_pct", "column"], ascending=[False, True]).reset_index(drop=True)


def profile_key_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return a compact profile for a selected column set."""
    subset = [column for column in columns if column in df.columns]
    return build_column_profile(df[subset])


def rectype_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Count records by RECTYPE."""
    counts = (
        df["RECTYPE"]
        .value_counts(dropna=False)
        .rename_axis("RECTYPE")
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )
    counts["pct"] = (counts["count"] / counts["count"].sum() * 100).round(2)
    return counts

