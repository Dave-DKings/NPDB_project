"""Common plotting helpers used by the advanced notebook."""

from __future__ import annotations

import pandas as pd


def plot_count_pct_bar(summary: pd.DataFrame, category_col: str, count_col: str = "count", pct_col: str = "pct", ax=None):
    """Plot a bar chart with count labels and percent annotations."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    axis = ax or plt.gca()
    sns.barplot(data=summary, x=category_col, y=count_col, ax=axis, color="steelblue")
    axis.set_ylabel("Count")
    axis.set_xlabel(category_col.replace("_", " "))
    for patch, (_, row) in zip(axis.patches, summary.iterrows()):
        axis.annotate(
            f"{int(row[count_col]):,}\n{row[pct_col]:.1f}%",
            (patch.get_x() + patch.get_width() / 2, patch.get_height()),
            ha="center",
            va="bottom",
            fontsize=9,
        )
    return axis


def plot_state_period_heatmap(summary: pd.DataFrame, value_col: str = "mean_payment_adj", ax=None):
    """Render a state-period heatmap from a grouped table."""
    import matplotlib.pyplot as plt
    import numpy as np
    import seaborn as sns

    axis = ax or plt.gca()
    pivot = summary.pivot(index="STATE", columns="PERIOD_10Y", values=value_col)
    pivot = pivot.apply(pd.to_numeric, errors="coerce")
    heatmap_values = np.asarray(pivot, dtype=float)
    sns.heatmap(
        heatmap_values,
        cmap="YlGnBu",
        annot=True,
        fmt=",.0f",
        ax=axis,
        xticklabels=pivot.columns.astype(str),
        yticklabels=pivot.index.astype(str),
        linewidths=0.5,
        cbar_kws={"label": value_col.replace("_", " ").title()},
    )
    axis.set_title(value_col.replace("_", " ").title(), fontsize=13, fontweight="bold")
    return axis


def plot_wisconsin_peers(summary: pd.DataFrame, value_col: str = "mean_payment_adj", ax=None):
    """Plot Wisconsin and peer-state trends over time."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    axis = ax or plt.gca()
    sns.lineplot(data=summary, x="PERIOD_10Y", y=value_col, hue="STATE", marker="o", ax=axis)
    axis.tick_params(axis="x", rotation=45)
    axis.set_title(f"Wisconsin and Peers: {value_col.replace('_', ' ').title()}")
    return axis
