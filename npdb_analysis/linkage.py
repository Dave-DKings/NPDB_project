"""Defensible linkage helpers for pre-2004 total-payment reconstruction."""

from __future__ import annotations

import pandas as pd

TIER_COLUMNS = {
    "strict": ["PRACTNUM", "STATE", "MALYEAR1", "MALYEAR2", "ALGNNATR", "PAYTYPE_STR"],
    "moderate": ["PRACTNUM", "STATE", "MALYEAR1", "ALGNNATR", "ORIGYEAR_WINDOW"],
    "exploratory": ["PRACTNUM", "STATE", "MALYEAR1"],
}

MAX_ALLOWED_YEAR_SPAN = {
    "strict": 3,
    "moderate": 5,
    "exploratory": 7,
}


def _prepare_linkage_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame["PRACTNUM"] = pd.to_numeric(frame["PRACTNUM"], errors="coerce").astype("Int64")
    frame["MALYEAR1"] = pd.to_numeric(frame["MALYEAR1"], errors="coerce").astype("Int64")
    frame["MALYEAR2"] = pd.to_numeric(frame["MALYEAR2"], errors="coerce").astype("Int64")
    frame["ALGNNATR"] = pd.to_numeric(frame["ALGNNATR"], errors="coerce").astype("Int64")
    frame["ORIGYEAR"] = pd.to_numeric(frame["ORIGYEAR"], errors="coerce").astype("Int64")
    frame["ORIGYEAR_WINDOW"] = ((frame["ORIGYEAR"] // 3) * 3).astype("Int64")
    frame["PAYTYPE_STR"] = frame["PAYTYPE_STR"].astype("string")
    frame["STATE"] = frame["STATE"].astype("string")
    return frame


def build_episode_keys(df: pd.DataFrame, tier: str = "strict") -> pd.DataFrame:
    """Assign a deterministic episode key for the selected linkage tier."""
    if tier not in TIER_COLUMNS:
        raise ValueError(f"Unsupported linkage tier: {tier}")
    frame = _prepare_linkage_frame(df)
    key_columns = TIER_COLUMNS[tier]
    components = []
    for column in key_columns:
        components.append(frame[column].astype("string").fillna("NA"))
    frame["EPISODE_KEY"] = pd.Series(["|".join(values) for values in zip(*components)], index=frame.index)
    frame["LINKAGE_TIER"] = tier
    return frame


def derive_payment_episodes(df: pd.DataFrame, tier: str = "strict") -> pd.DataFrame:
    """Aggregate records into derived payment episodes and flag ambiguity."""
    frame = build_episode_keys(df, tier=tier)
    episodes = (
        frame.groupby("EPISODE_KEY", dropna=False)
        .agg(
            linkage_tier=("LINKAGE_TIER", "first"),
            record_count=("SEQNO", "size"),
            practitioner_count=("PRACTNUM", "nunique"),
            state_count=("STATE", "nunique"),
            allegation_count=("ALGNNATR", "nunique"),
            paytype_count=("PAYTYPE_STR", "nunique"),
            reptype_count=("REPTYPE", "nunique"),
            min_origyear=("ORIGYEAR", "min"),
            max_origyear=("ORIGYEAR", "max"),
            payment_sum_adj=("PAYMENT_ADJ", "sum"),
            totalpmt_max_adj=("TOTALPMT_ADJ", "max"),
            totalpmt_non_null=("TOTALPMT_ADJ", lambda series: int(series.notna().sum())),
        )
        .reset_index()
    )
    episodes["origyear_span"] = episodes["max_origyear"] - episodes["min_origyear"]
    episodes["ambiguous_episode"] = (
        (episodes["practitioner_count"] > 1)
        | (episodes["state_count"] > 1)
        | (episodes["allegation_count"] > 1)
        | (episodes["paytype_count"] > 1)
        | (episodes["origyear_span"] > MAX_ALLOWED_YEAR_SPAN[tier])
    )
    episodes["reconstruction_eligible"] = (~episodes["ambiguous_episode"]) & (episodes["record_count"] >= 1)
    return episodes


def validate_linkage(df: pd.DataFrame, tier: str = "strict") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate the linkage rule on records with observed TOTALPMT."""
    frame = build_episode_keys(df, tier=tier)
    episodes = derive_payment_episodes(frame, tier=tier)
    validation = episodes[
        episodes["totalpmt_non_null"] > 0
    ].copy()
    if validation.empty:
        return episodes, validation
    validation["absolute_error"] = (validation["payment_sum_adj"] - validation["totalpmt_max_adj"]).abs()
    validation["absolute_pct_error"] = validation["absolute_error"] / validation["totalpmt_max_adj"].replace(0, pd.NA)
    validation["within_10pct"] = validation["absolute_pct_error"] <= 0.10
    validation["within_25pct"] = validation["absolute_pct_error"] <= 0.25
    return episodes, validation


def validation_metrics(validation: pd.DataFrame) -> pd.DataFrame:
    """Summarize linkage validation quality."""
    if validation.empty:
        return pd.DataFrame()
    metrics = pd.DataFrame(
        {
            "episodes_validated": [len(validation)],
            "median_abs_pct_error": [validation["absolute_pct_error"].median()],
            "mean_abs_pct_error": [validation["absolute_pct_error"].mean()],
            "share_within_10pct": [validation["within_10pct"].mean()],
            "share_within_25pct": [validation["within_25pct"].mean()],
            "ambiguous_share": [validation["ambiguous_episode"].mean()],
        }
    )
    return metrics


def merge_total_payment_best(df: pd.DataFrame, episodes: pd.DataFrame) -> pd.DataFrame:
    """Attach derived episode totals and build TOTALPMT_BEST with provenance tags."""
    frame = build_episode_keys(df, tier=episodes["linkage_tier"].iat[0] if not episodes.empty else "strict")
    episode_subset = episodes[["EPISODE_KEY", "payment_sum_adj", "reconstruction_eligible"]].rename(
        columns={"payment_sum_adj": "EPISODE_PAYMENT_SUM_ADJ"}
    )
    merged = frame.merge(episode_subset, on="EPISODE_KEY", how="left")
    merged["TOTALPMT_BEST"] = merged["TOTALPMT_ADJ"]
    merged["TOTALPMT_SOURCE"] = "observed"
    needs_reconstruction = merged["TOTALPMT_BEST"].isna() & merged["reconstruction_eligible"].fillna(False)
    merged.loc[needs_reconstruction, "TOTALPMT_BEST"] = merged.loc[needs_reconstruction, "EPISODE_PAYMENT_SUM_ADJ"]
    merged.loc[needs_reconstruction, "TOTALPMT_SOURCE"] = "reconstructed"
    unresolved = merged["TOTALPMT_BEST"].isna()
    merged.loc[unresolved, "TOTALPMT_SOURCE"] = "unresolved"
    return merged

