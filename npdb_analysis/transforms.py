"""Raw-data cleaning and missingness classification."""

from __future__ import annotations

import pandas as pd

from .config import CATEGORY_COLUMNS, CURRENCY_COLUMNS, NULLABLE_NUMERIC_COLUMNS


def _clean_string_codes(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.strip().str.upper()
    return cleaned.replace({"": pd.NA, "NAN": pd.NA, "NONE": pd.NA})


def clean_currency_columns(df: pd.DataFrame, columns: tuple[str, ...] = CURRENCY_COLUMNS) -> pd.DataFrame:
    """Convert dollar-string columns into numeric values."""
    cleaned = df.copy()
    for column in columns:
        if column not in cleaned.columns:
            continue
        cleaned[column] = (
            cleaned[column]
            .astype("string")
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .replace({"nan": pd.NA, "NAN": pd.NA, "": pd.NA})
        )
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    return cleaned


def cast_nullable_numeric(df: pd.DataFrame, columns: tuple[str, ...] = NULLABLE_NUMERIC_COLUMNS) -> pd.DataFrame:
    """Cast numeric-coded columns into pandas nullable numeric types."""
    cleaned = df.copy()
    for column in columns:
        if column not in cleaned.columns:
            continue
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
        if column == "AALENGTH":
            continue
        if pd.api.types.is_float_dtype(cleaned[column]) or pd.api.types.is_integer_dtype(cleaned[column]):
            try:
                cleaned[column] = cleaned[column].round().astype("Int64")
            except TypeError:
                cleaned[column] = cleaned[column].astype("Float64")
    if "AALENGTH" in cleaned.columns:
        cleaned["AALENGTH"] = pd.to_numeric(cleaned["AALENGTH"], errors="coerce")
    return cleaned


def cast_category_columns(df: pd.DataFrame, columns: tuple[str, ...] = CATEGORY_COLUMNS) -> pd.DataFrame:
    """Normalize string code columns and cast to category."""
    cleaned = df.copy()
    for column in columns:
        if column not in cleaned.columns:
            continue
        cleaned[column] = _clean_string_codes(cleaned[column]).astype("category")
    return cleaned


def clean_npdb(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the standard cleaning sequence used by the advanced notebook."""
    cleaned = clean_currency_columns(df)
    cleaned = cast_nullable_numeric(cleaned)
    cleaned = cast_category_columns(cleaned)
    return cleaned


def structural_missingness_summary(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Summarize missingness by RECTYPE for selected columns."""
    subset = [column for column in columns if column in df.columns]
    if not subset:
        return pd.DataFrame()
    rows = []
    for rectype, rectype_df in df.groupby("RECTYPE", dropna=False):
        for column in subset:
            rows.append(
                {
                    "RECTYPE": rectype,
                    "column": column,
                    "missing_count": int(rectype_df[column].isna().sum()),
                    "missing_pct": round(float(rectype_df[column].isna().mean() * 100), 2),
                }
            )
    return pd.DataFrame(rows).sort_values(["column", "RECTYPE"]).reset_index(drop=True)


def dtype_audit(df: pd.DataFrame) -> pd.DataFrame:
    """Return a compact dtype audit table."""
    return pd.DataFrame({"column": df.columns, "dtype": [str(dtype) for dtype in df.dtypes]})

