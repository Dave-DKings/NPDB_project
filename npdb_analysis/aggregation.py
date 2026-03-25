"""Reusable grouped summaries for the advanced NPDB workflow."""

from __future__ import annotations

from itertools import combinations

import pandas as pd

from .config import NPDB_PEER_STATES


def summarize_by_period(df: pd.DataFrame, period_col: str, amount_col: str = "PAYMENT_ADJ") -> pd.DataFrame:
    """Compute counts, shares, and payment statistics by a period column."""
    summary = (
        df.groupby(period_col, dropna=False)
        .agg(
            count=("SEQNO", "size"),
            mean_payment_adj=(amount_col, "mean"),
            median_payment_adj=(amount_col, "median"),
            total_payment_adj=(amount_col, "sum"),
            catastrophic_share=("CATASTROPHIC", "mean"),
            judgment_share=("IS_JUDGMENT", "mean"),
        )
        .reset_index()
        .sort_values(period_col)
    )
    summary["pct"] = (summary["count"] / summary["count"].sum() * 100).round(2)
    summary["pct_of_total_dollars"] = (summary["total_payment_adj"] / summary["total_payment_adj"].sum() * 100).round(2)
    summary["mean_to_median_ratio"] = (summary["mean_payment_adj"] / summary["median_payment_adj"]).round(2)
    summary["catastrophic_share"] = (summary["catastrophic_share"] * 100).round(2)
    summary["judgment_share"] = (summary["judgment_share"] * 100).round(2)
    return summary


def hierarchical_state_period_mode(
    df: pd.DataFrame,
    state_col: str = "STATE",
    period_col: str = "PERIOD_10Y",
    mode_col: str = "PAYMENT_MODE",
    amount_col: str = "PAYMENT_ADJ",
) -> pd.DataFrame:
    """Build the core state-period-payment-mode summary table."""
    summary = (
        df.groupby([state_col, period_col, mode_col], dropna=False)
        .agg(
            count=("SEQNO", "size"),
            mean_payment_adj=(amount_col, "mean"),
            median_payment_adj=(amount_col, "median"),
            total_payment_adj=(amount_col, "sum"),
            catastrophic_share=("CATASTROPHIC", "mean"),
            judgment_share=("IS_JUDGMENT", "mean"),
        )
        .reset_index()
    )
    summary["pct_within_state_period"] = (
        summary["count"] / summary.groupby([state_col, period_col])["count"].transform("sum") * 100
    ).round(2)
    summary["pct_of_total_dollars"] = (summary["total_payment_adj"] / summary["total_payment_adj"].sum() * 100).round(2)
    summary["mean_to_median_ratio"] = (summary["mean_payment_adj"] / summary["median_payment_adj"]).round(2)
    summary["catastrophic_share"] = (summary["catastrophic_share"] * 100).round(2)
    summary["judgment_share"] = (summary["judgment_share"] * 100).round(2)
    return summary.sort_values([state_col, period_col, mode_col]).reset_index(drop=True)


def state_level_summary(df: pd.DataFrame, amount_col: str = "PAYMENT_ADJ") -> pd.DataFrame:
    """Summarize malpractice payments by state."""
    summary = (
        df.groupby("STATE", dropna=False)
        .agg(
            count=("SEQNO", "size"),
            mean_payment_adj=(amount_col, "mean"),
            median_payment_adj=(amount_col, "median"),
            total_payment_adj=(amount_col, "sum"),
            catastrophic_share=("CATASTROPHIC", "mean"),
            judgment_share=("IS_JUDGMENT", "mean"),
        )
        .reset_index()
        .sort_values("count", ascending=False)
    )
    summary["pct"] = (summary["count"] / summary["count"].sum() * 100).round(2)
    summary["pct_of_total_dollars"] = (summary["total_payment_adj"] / summary["total_payment_adj"].sum() * 100).round(2)
    summary["mean_to_median_ratio"] = (summary["mean_payment_adj"] / summary["median_payment_adj"]).round(2)
    summary["catastrophic_share"] = (summary["catastrophic_share"] * 100).round(2)
    summary["judgment_share"] = (summary["judgment_share"] * 100).round(2)
    return summary


def wisconsin_peer_comparison(
    df: pd.DataFrame,
    states: tuple[str, ...] = NPDB_PEER_STATES,
    period_col: str = "PERIOD_10Y",
    amount_col: str = "PAYMENT_ADJ",
) -> pd.DataFrame:
    """Filter a grouped comparison set for Wisconsin and peer states."""
    frame = df[df["STATE"].isin(states)].copy()
    summary = (
        frame.groupby(["STATE", period_col], dropna=False)
        .agg(
            count=("SEQNO", "size"),
            mean_payment_adj=(amount_col, "mean"),
            median_payment_adj=(amount_col, "median"),
            total_payment_adj=(amount_col, "sum"),
            catastrophic_share=("CATASTROPHIC", "mean"),
            judgment_share=("IS_JUDGMENT", "mean"),
        )
        .reset_index()
        .sort_values(["STATE", period_col])
    )
    summary["pct_of_total_dollars"] = (summary["total_payment_adj"] / summary["total_payment_adj"].sum() * 100).round(2)
    summary["mean_to_median_ratio"] = (summary["mean_payment_adj"] / summary["median_payment_adj"]).round(2)
    return summary


def practitioner_state_mobility(df: pd.DataFrame) -> pd.DataFrame:
    """Count unique states per practitioner and compare payment exposure."""
    summary = (
        df.groupby("PRACTNUM")
        .agg(
            unique_states=("STATE", "nunique"),
            record_count=("SEQNO", "size"),
            total_payment_adj=("PAYMENT_ADJ", "sum"),
            mean_payment_adj=("PAYMENT_ADJ", "mean"),
            min_year=("ORIGYEAR", "min"),
            max_year=("ORIGYEAR", "max"),
        )
        .reset_index()
    )
    summary["multi_state_practitioner"] = summary["unique_states"] >= 2
    summary["years_spanned"] = summary["max_year"] - summary["min_year"]
    return summary


def multi_state_pairs(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Return the most common state pairs shared by the same practitioner."""
    pair_counts: dict[tuple[str, str], int] = {}
    practitioner_states = (
        df.dropna(subset=["PRACTNUM", "STATE"])
        .groupby("PRACTNUM")["STATE"]
        .apply(lambda series: sorted(set(series.dropna().astype(str))))
    )
    for states in practitioner_states:
        if len(states) < 2:
            continue
        for pair in combinations(states, 2):
            pair_counts[pair] = pair_counts.get(pair, 0) + 1
    pair_frame = pd.DataFrame(
        [{"state_1": pair[0], "state_2": pair[1], "shared_practitioners": count} for pair, count in pair_counts.items()]
    )
    if pair_frame.empty:
        return pair_frame
    return pair_frame.sort_values("shared_practitioners", ascending=False).head(top_n).reset_index(drop=True)

