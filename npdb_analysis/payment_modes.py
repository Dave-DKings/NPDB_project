"""Single-vs-multiple payment analysis helpers."""

from __future__ import annotations

import pandas as pd

from .config import PAYMENT_MODE_MAP


def add_payment_mode_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Map PAYNUMBR into labeled payment-mode categories."""
    enriched = df.copy()
    paynumbr = enriched["PAYNUMBR"].astype("string").str.strip().str.upper()
    enriched["PAYNUMBR_STR"] = paynumbr
    enriched["PAYMENT_MODE"] = paynumbr.map(PAYMENT_MODE_MAP)
    enriched.loc[enriched["RECTYPE"].astype("string") == "M", "PAYMENT_MODE"] = "Unavailable Pre-2004"
    enriched["PAYMENT_MODE"] = enriched["PAYMENT_MODE"].fillna("Unknown Payment Mode")
    return enriched


def payment_mode_distribution(df: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    """Count records and percentages by payment mode."""
    frame = add_payment_mode_labels(df)
    grouping = (group_cols or []) + ["PAYMENT_MODE"]
    summary = frame.groupby(grouping, dropna=False).size().reset_index(name="count")
    if group_cols:
        summary["pct"] = (
            summary["count"]
            / summary.groupby(group_cols)["count"].transform("sum")
            * 100
        ).round(2)
    else:
        summary["pct"] = (summary["count"] / summary["count"].sum() * 100).round(2)
    return summary.sort_values(grouping).reset_index(drop=True)


def single_multiple_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Compare payment size across single and multiple payment records."""
    frame = add_payment_mode_labels(df)
    frame = frame[frame["PAYMENT_MODE"].isin(["Single Payment", "Multiple Payments"])].copy()
    summary = (
        frame.groupby("PAYMENT_MODE")
        .agg(
            count=("PAYMENT_ADJ", "size"),
            mean_payment_adj=("PAYMENT_ADJ", "mean"),
            median_payment_adj=("PAYMENT_ADJ", "median"),
            std_payment_adj=("PAYMENT_ADJ", "std"),
            max_payment_adj=("PAYMENT_ADJ", "max"),
            total_payment_adj=("PAYMENT_ADJ", "sum"),
        )
        .reset_index()
        .sort_values("count", ascending=False)
    )
    summary["pct"] = (summary["count"] / summary["count"].sum() * 100).round(2)
    summary["pct_of_total_dollars"] = (summary["total_payment_adj"] / summary["total_payment_adj"].sum() * 100).round(2)
    summary["mean_to_median_ratio"] = (summary["mean_payment_adj"] / summary["median_payment_adj"]).round(2)
    return summary


def practitioner_multi_payment_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize multiple-payment records by practitioner."""
    frame = add_payment_mode_labels(df)
    frame = frame[frame["PAYMENT_MODE"] == "Multiple Payments"].copy()
    if frame.empty:
        return pd.DataFrame()
    summary = (
        frame.groupby("PRACTNUM")
        .agg(
            report_count=("SEQNO", "size"),
            total_payment_adj=("PAYMENT_ADJ", "sum"),
            mean_payment_adj=("PAYMENT_ADJ", "mean"),
            min_year=("ORIGYEAR", "min"),
            max_year=("ORIGYEAR", "max"),
            state_count=("STATE", "nunique"),
        )
        .reset_index()
        .sort_values(["report_count", "total_payment_adj"], ascending=[False, False])
    )
    summary["years_spanned"] = summary["max_year"] - summary["min_year"]
    summary["pct_of_total_dollars"] = (summary["total_payment_adj"] / summary["total_payment_adj"].sum() * 100).round(2)
    return summary


def classify_multi_payment_practitioners(profile: pd.DataFrame) -> pd.DataFrame:
    """Classify multi-payment practitioners into behavioral profiles.

    Profiles:
        Chronic Repeater  - 3+ reports spread over 3+ years
        Catastrophic Event - mean payment >= $1M with <= 3 reports
        Batch Reporter    - 3+ reports clustered within 1 year
        Moderate Repeater - everyone else with 2+ reports
    """
    df = profile.copy()

    conditions = [
        (df["report_count"] >= 3) & (df["years_spanned"] >= 3),
        (df["mean_payment_adj"] >= 1_000_000) & (df["report_count"] <= 3),
        (df["report_count"] >= 3) & (df["years_spanned"] <= 1),
    ]
    labels = ["Chronic Repeater", "Catastrophic Event", "Batch Reporter"]

    df["practitioner_profile"] = "Moderate Repeater"
    # Apply in reverse priority so higher-priority rules overwrite
    for condition, label in zip(conditions, labels):
        df.loc[condition, "practitioner_profile"] = label

    return df

