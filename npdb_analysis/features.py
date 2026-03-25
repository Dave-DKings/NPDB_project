"""Feature engineering for malpractice analyses."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import CPI_FACTORS_2025, MALPRACTICE_RECORD_TYPES, PAYTYPE_BINARY_MAP


def filter_malpractice(df: pd.DataFrame) -> pd.DataFrame:
    """Keep malpractice payment records only."""
    return df[df["RECTYPE"].isin(MALPRACTICE_RECORD_TYPES)].copy()


def add_state_composite(df: pd.DataFrame) -> pd.DataFrame:
    """Create a fallback state variable using NPDB guidance."""
    enriched = df.copy()
    enriched["STATE"] = (
        enriched["WORKSTAT"].astype("object")
        .fillna(enriched["LICNSTAT"].astype("object"))
        .fillna(enriched["HOMESTAT"].astype("object"))
    )
    enriched["STATE"] = (
        enriched["STATE"]
        .astype("string")
        .str.strip()
        .str.upper()
        .replace({"": pd.NA, "NAN": pd.NA})
        .astype("category")
    )
    return enriched


def _period_label(series: pd.Series, width: int) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    start = (numeric // width) * width
    start = start.astype("Int64")
    end = start + width - 1
    labels = start.astype("string") + "-" + end.astype("Int64").astype("string")
    return labels.where(numeric.notna(), pd.NA).astype("string")


def add_period_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add 5-year and 10-year period buckets for report year and incident year."""
    enriched = df.copy()
    enriched["ORIGYEAR"] = pd.to_numeric(enriched["ORIGYEAR"], errors="coerce").astype("Int64")
    if "MALYEAR1" in enriched.columns:
        enriched["MALYEAR1"] = pd.to_numeric(enriched["MALYEAR1"], errors="coerce").astype("Int64")
    enriched["PERIOD_5Y"] = _period_label(enriched["ORIGYEAR"], 5)
    enriched["PERIOD_10Y"] = _period_label(enriched["ORIGYEAR"], 10)
    enriched["MAL_PERIOD_5Y"] = _period_label(enriched["MALYEAR1"], 5)
    enriched["MAL_PERIOD_10Y"] = _period_label(enriched["MALYEAR1"], 10)
    return enriched


def add_resolution_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Create detailed and binary resolution fields from PAYTYPE."""
    enriched = df.copy()
    paytype = enriched["PAYTYPE"].astype("string").str.strip().str.upper()
    enriched["PAYTYPE_STR"] = paytype
    enriched["RESOLUTION_BINARY"] = paytype.map(PAYTYPE_BINARY_MAP).fillna("Other")
    enriched["IS_JUDGMENT"] = enriched["PAYTYPE_STR"].eq("J")
    return enriched


def add_cpi_adjustments(
    df: pd.DataFrame,
    cpi_factors: dict[int, float] = CPI_FACTORS_2025,
    year_col: str = "ORIGYEAR",
) -> pd.DataFrame:
    """Adjust payment columns to the shared 2025-dollar baseline."""
    enriched = df.copy()
    enriched["CPI_FACTOR"] = pd.to_numeric(enriched[year_col], errors="coerce").map(cpi_factors)
    if "PAYMENT" in enriched.columns:
        enriched["PAYMENT_ADJ"] = enriched["PAYMENT"] * enriched["CPI_FACTOR"]
        positive_payment_mask = enriched["PAYMENT_ADJ"].notna() & (enriched["PAYMENT_ADJ"] > 0)
        enriched["LOG_PAYMENT_ADJ"] = np.nan
        enriched.loc[positive_payment_mask, "LOG_PAYMENT_ADJ"] = np.log(
            enriched.loc[positive_payment_mask, "PAYMENT_ADJ"]
        )
    if "TOTALPMT" in enriched.columns:
        enriched["TOTALPMT_ADJ"] = enriched["TOTALPMT"] * enriched["CPI_FACTOR"]
    return enriched


def add_lag_and_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Add lag and quality-flag columns."""
    enriched = df.copy()
    enriched["LAG_YEARS"] = pd.to_numeric(enriched["ORIGYEAR"], errors="coerce") - pd.to_numeric(
        enriched["MALYEAR1"], errors="coerce"
    )
    enriched["VALID_LAG"] = enriched["LAG_YEARS"].between(0, 50, inclusive="both")
    enriched["CATASTROPHIC"] = enriched["PAYMENT_ADJ"].ge(1_000_000).fillna(False)
    enriched["MISSING_STATE"] = enriched["STATE"].isna()
    enriched["MISSING_ALLEGATION"] = enriched["ALGNNATR"].isna()
    enriched["MISSING_OUTCOME"] = enriched["OUTCOME"].isna()
    return enriched


def add_common_features(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full feature engineering pipeline for malpractice analyses."""
    enriched = filter_malpractice(df)
    enriched = add_state_composite(enriched)
    enriched = add_period_columns(enriched)
    enriched = add_resolution_fields(enriched)
    enriched = add_cpi_adjustments(enriched)
    enriched = add_lag_and_flags(enriched)
    return enriched
