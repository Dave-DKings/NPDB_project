"""Insert visualization cells into advanced_NPDB.ipynb for key tables."""
import json
import sys
import uuid

sys.stdout.reconfigure(encoding="utf-8")

NOTEBOOK = "advanced_NPDB.ipynb"

with open(NOTEBOOK, "r", encoding="utf-8") as f:
    nb = json.load(f)


def make_code_cell(source_text):
    return {
        "cell_type": "code",
        "metadata": {},
        "source": source_text.split("\n__LINESEP__\n") if "__LINESEP__" in source_text else [source_text],
        "outputs": [],
        "execution_count": None,
        "id": str(uuid.uuid4())[:8],
    }


# Each entry: (after_cell_index, code_string)
# Process bottom-to-top so indices stay valid.

viz_cells = [
    # ═══════════════════════════════════════════════════════════════
    # SECTION 12: Lag Analysis — after cell 77 (lag_by_resolution table)
    # ═══════════════════════════════════════════════════════════════
    (
        77,
        '''# --- Lag by Resolution: Side-by-side bar + period trend ---
fig, axes = plt.subplots(1, 2, figsize=(18, 6))

# Panel 1: Mean vs Median lag by resolution type
res_labels = lag_by_resolution["RESOLUTION_BINARY"].tolist()
x = np.arange(len(res_labels))
w = 0.35
bars1 = axes[0].bar(x - w/2, lag_by_resolution["mean_lag_years"], w, label="Mean", color="#4C72B0")
bars2 = axes[0].bar(x + w/2, lag_by_resolution["median_lag_years"], w, label="Median", color="#DD8452")
axes[0].set_xticks(x)
axes[0].set_xticklabels(res_labels, fontsize=11)
axes[0].set_ylabel("Years", fontsize=12)
axes[0].set_title("Time to Payment by Resolution Type", fontsize=13, fontweight="bold")
axes[0].legend(fontsize=11)
for bar in bars1:
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 f"{bar.get_height():.1f}y", ha="center", fontsize=10, fontweight="bold")
for bar in bars2:
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 f"{bar.get_height():.1f}y", ha="center", fontsize=10, fontweight="bold")

# Panel 2: Lag trend by decade
lag_by_period = (
    lag_df.groupby("PERIOD_10Y")
    .agg(mean_lag=("LAG_YEARS", "mean"), median_lag=("LAG_YEARS", "median"), count=("SEQNO", "size"))
    .reset_index()
)
axes[1].plot(lag_by_period["PERIOD_10Y"].astype(str), lag_by_period["mean_lag"], "o-", color="#4C72B0", linewidth=2, markersize=8, label="Mean")
axes[1].plot(lag_by_period["PERIOD_10Y"].astype(str), lag_by_period["median_lag"], "s--", color="#DD8452", linewidth=2, markersize=8, label="Median")
axes[1].set_ylabel("Lag (Years)", fontsize=12)
axes[1].set_title("Resolution Speed Over Time", fontsize=13, fontweight="bold")
axes[1].legend(fontsize=11)
for _, row in lag_by_period.iterrows():
    axes[1].annotate(f"n={row['count']:,.0f}", (str(row['PERIOD_10Y']), row['mean_lag']),
                     textcoords="offset points", xytext=(0, 12), ha="center", fontsize=9, color="gray")

plt.tight_layout()
plt.show()
''',
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECTION 11: Distribution fitting — after cell 69 (exceedance table)
    # ═══════════════════════════════════════════════════════════════
    (
        69,
        '''# --- Exceedance curve + Distribution fit comparison ---
fig, axes = plt.subplots(1, 2, figsize=(18, 6))

# Panel 1: Exceedance survival curve
sorted_vals = np.sort(single_payment_values.dropna().values)
n = len(sorted_vals)
exceedance_pct = 100 * (1 - np.arange(1, n + 1) / n)
axes[0].plot(sorted_vals, exceedance_pct, color="#4C72B0", linewidth=1.5)
axes[0].set_xscale("log")
axes[0].set_xlabel("Payment Amount (2025$, log scale)", fontsize=12)
axes[0].set_ylabel("% of Claims Exceeding", fontsize=12)
axes[0].set_title("Exceedance Curve: Single-Payment Cases", fontsize=13, fontweight="bold")
for t, label in [(100_000, "$100K"), (500_000, "$500K"), (1_000_000, "$1M"), (5_000_000, "$5M")]:
    pct = (sorted_vals > t).sum() / n * 100
    axes[0].axvline(t, color="gray", linestyle="--", alpha=0.5)
    axes[0].annotate(f"{label}\\n{pct:.1f}%", (t, pct), fontsize=9, fontweight="bold",
                     textcoords="offset points", xytext=(8, 5), color="#C44E52")
axes[0].grid(True, alpha=0.3)

# Panel 2: Distribution fit AIC comparison
fit_df = distribution_fits.dropna(subset=["aic"]).copy()
fit_df = fit_df.sort_values("aic")
colors = ["#55A868" if i == 0 else "#4C72B0" for i in range(len(fit_df))]
bars = axes[1].barh(fit_df["distribution"], fit_df["aic"], color=colors)
axes[1].set_xlabel("AIC (lower = better fit)", fontsize=12)
axes[1].set_title("Distribution Fit Comparison (AIC)", fontsize=13, fontweight="bold")
for bar, aic_val in zip(bars, fit_df["aic"]):
    axes[1].text(bar.get_width(), bar.get_y() + bar.get_height()/2,
                 f"  {aic_val:,.0f}", va="center", fontsize=10, fontweight="bold")
axes[1].invert_yaxis()

plt.tight_layout()
plt.show()
''',
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECTION 10: Settlement — after cell 65 (wi_settlement_state table)
    # ═══════════════════════════════════════════════════════════════
    (
        65,
        '''# --- Settlement vs Judgment: Midwest peer comparison + trend ---
fig, axes = plt.subplots(1, 2, figsize=(18, 6))

# Panel 1: Judgment rate by Midwest peer state
judgment_rates = wi_settlement_state[wi_settlement_state["RESOLUTION_BINARY"] == "Judgment"].copy()
judgment_rates = judgment_rates.sort_values("pct_within_state", ascending=True)
colors = ["#C44E52" if s == "WI" else "#4C72B0" for s in judgment_rates["STATE"].astype(str)]
bars = axes[0].barh(judgment_rates["STATE"].astype(str), judgment_rates["pct_within_state"], color=colors)
axes[0].set_xlabel("Judgment Rate (%)", fontsize=12)
axes[0].set_title("Judgment Rate: Midwest Peers", fontsize=13, fontweight="bold")
for bar, pct_val in zip(bars, judgment_rates["pct_within_state"]):
    axes[0].text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
                 f"{pct_val:.1f}%", va="center", fontsize=10, fontweight="bold")

# Panel 2: Judgment share trend over time
settlement_period_pct = settlement_period.copy()
judgment_trend = settlement_period_pct[settlement_period_pct["RESOLUTION_BINARY"] == "Judgment"].copy()
axes[1].plot(judgment_trend["PERIOD_10Y"].astype(str), judgment_trend["pct_within_period"],
             "o-", color="#C44E52", linewidth=2.5, markersize=10)
axes[1].fill_between(range(len(judgment_trend)), judgment_trend["pct_within_period"].values,
                     alpha=0.15, color="#C44E52")
axes[1].set_ylabel("Judgment Share (%)", fontsize=12)
axes[1].set_title("Judgment Rate Declining Over Time", fontsize=13, fontweight="bold")
for _, row in judgment_trend.iterrows():
    axes[1].annotate(f'{row["pct_within_period"]:.1f}%\\n(n={row["count"]:,})',
                     (str(row["PERIOD_10Y"]), row["pct_within_period"]),
                     textcoords="offset points", xytext=(0, 14), ha="center", fontsize=10, fontweight="bold")

plt.tight_layout()
plt.show()
''',
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECTION 9: Practitioner Mobility — after cell 60 (mobility comparison table)
    # ═══════════════════════════════════════════════════════════════
    (
        60,
        '''# --- Practitioner mobility: payment comparison + top state pairs ---
fig, axes = plt.subplots(1, 2, figsize=(18, 6))

# Panel 1: Single-state vs multi-state payment comparison
mob_compare = mobility.groupby("multi_state_practitioner").agg(
    mean_payment=("total_payment_adj", "mean"),
    count=("PRACTNUM", "size"),
).reset_index()
mob_compare["label"] = mob_compare["multi_state_practitioner"].map({True: "Multi-State", False: "Single-State"})
colors = ["#4C72B0", "#C44E52"]
bars = axes[0].bar(mob_compare["label"], mob_compare["mean_payment"], color=colors, width=0.5)
axes[0].set_ylabel("Mean Total Payment (2025$)", fontsize=12)
axes[0].set_title("Payment by Practitioner Mobility", fontsize=13, fontweight="bold")
for bar, row in zip(bars, mob_compare.itertuples()):
    pct = row.count / mob_compare["count"].sum() * 100
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                 f"${bar.get_height():,.0f}\\n({row.count:,} | {pct:.1f}%)",
                 ha="center", va="bottom", fontsize=10, fontweight="bold")

# Panel 2: Top 15 state pairs
top_pairs = state_pairs.head(15).copy()
top_pairs["pair_label"] = top_pairs["state_1"].astype(str) + " - " + top_pairs["state_2"].astype(str)
top_pairs = top_pairs.sort_values("shared_practitioners")
bars = axes[1].barh(top_pairs["pair_label"], top_pairs["shared_practitioners"], color="#4C72B0")
axes[1].set_xlabel("Shared Practitioners", fontsize=12)
axes[1].set_title("Top State Pairs by Practitioner Overlap", fontsize=13, fontweight="bold")
for bar, val in zip(bars, top_pairs["shared_practitioners"]):
    axes[1].text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2,
                 f"{val:,}", va="center", fontsize=9, fontweight="bold")

plt.tight_layout()
plt.show()
''',
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECTION 8: Wisconsin — after cell 55 (wisconsin_only table)
    # ═══════════════════════════════════════════════════════════════
    (
        55,
        '''# --- Wisconsin deep dive: severity ratio + catastrophic trend ---
fig, axes = plt.subplots(1, 2, figsize=(18, 6))

# Panel 1: Mean-to-Median ratio across Midwest peers (highlights severity skew)
peer_ratio = wi_peer_summary.copy()
peer_ratio["mean_to_median"] = peer_ratio["mean_payment_adj"] / peer_ratio["median_payment_adj"]
latest_period = peer_ratio["PERIOD_10Y"].astype(str).max()
latest = peer_ratio[peer_ratio["PERIOD_10Y"].astype(str) == latest_period].sort_values("mean_to_median", ascending=True)
colors = ["#C44E52" if str(s) == "WI" else "#4C72B0" for s in latest["STATE"]]
bars = axes[0].barh(latest["STATE"].astype(str), latest["mean_to_median"], color=colors)
axes[0].set_xlabel("Mean-to-Median Ratio", fontsize=12)
axes[0].set_title(f"Payment Skew by State ({latest_period})", fontsize=13, fontweight="bold")
axes[0].axvline(x=1, color="gray", linestyle="--", alpha=0.5)
for bar, val in zip(bars, latest["mean_to_median"]):
    axes[0].text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                 f"{val:.1f}x", va="center", fontsize=10, fontweight="bold")

# Panel 2: Wisconsin claims over time with catastrophic overlay
wi_data = wi_peer_summary[wi_peer_summary["STATE"].astype(str) == "WI"].copy()
periods = wi_data["PERIOD_10Y"].astype(str).tolist()
x = np.arange(len(periods))
bars = axes[1].bar(x, wi_data["count"], color="#4C72B0", alpha=0.7, label="Total Claims")
ax2 = axes[1].twinx()
ax2.plot(x, wi_data["catastrophic_share"] * 100, "o-", color="#C44E52", linewidth=2.5, markersize=10, label="Catastrophic %")
axes[1].set_xticks(x)
axes[1].set_xticklabels(periods, fontsize=11)
axes[1].set_ylabel("Claim Count", fontsize=12)
ax2.set_ylabel("Catastrophic Share (%)", fontsize=12, color="#C44E52")
axes[1].set_title("Wisconsin: Volume Decline vs Catastrophic Rate", fontsize=13, fontweight="bold")
for bar, ct in zip(bars, wi_data["count"]):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                 f"{ct:,}", ha="center", va="bottom", fontsize=10, fontweight="bold")
for xi, pct in zip(x, wi_data["catastrophic_share"] * 100):
    ax2.annotate(f"{pct:.0f}%", (xi, pct), textcoords="offset points", xytext=(0, 10),
                 ha="center", fontsize=10, fontweight="bold", color="#C44E52")
lines1, labels1 = axes[1].get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
axes[1].legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=10)

plt.tight_layout()
plt.show()
''',
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECTION 7: State Analysis — after cell 46 (state_summary table)
    # ═══════════════════════════════════════════════════════════════
    (
        46,
        '''# --- Top states: dual metric bar chart + catastrophic scatter ---
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

top_n = state_summary.head(15).copy()

# Panel 1: Top 15 states — mean payment with count annotations
top_n_sorted = top_n.sort_values("mean_payment_adj", ascending=True)
bars = axes[0].barh(top_n_sorted["STATE"].astype(str), top_n_sorted["mean_payment_adj"], color="#4C72B0")
axes[0].set_xlabel("Mean Payment (2025$)", fontsize=12)
axes[0].set_title("Top 15 States: Mean Malpractice Payment", fontsize=13, fontweight="bold")
for bar, row in zip(bars, top_n_sorted.itertuples()):
    axes[0].text(bar.get_width(), bar.get_y() + bar.get_height()/2,
                 f"  ${row.mean_payment_adj:,.0f}  ({row.count:,} claims | {row.pct:.1f}%)",
                 va="center", fontsize=9, fontweight="bold")

# Panel 2: Bubble chart — claims vs mean payment, bubble = catastrophic share
scatter_data = state_summary.head(20).copy()
bubble_size = scatter_data["catastrophic_share"] * 1500
axes[1].scatter(scatter_data["count"], scatter_data["mean_payment_adj"],
                s=bubble_size, alpha=0.6, c="#4C72B0", edgecolors="white", linewidth=1.5)
for _, row in scatter_data.iterrows():
    axes[1].annotate(str(row["STATE"]),
                     (row["count"], row["mean_payment_adj"]),
                     fontsize=9, fontweight="bold", ha="center")
axes[1].set_xlabel("Total Claims", fontsize=12)
axes[1].set_ylabel("Mean Payment (2025$)", fontsize=12)
axes[1].set_title("Claims vs Severity (bubble = catastrophic %)", fontsize=13, fontweight="bold")
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
''',
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECTION 6: Time Grouped — after cell 43 (report_vs_incident table)
    # heatmap of report year vs incident year
    # ═══════════════════════════════════════════════════════════════
    (
        43,
        '''# --- Report year vs Incident year heatmap ---
fig, ax = plt.subplots(figsize=(14, 8))

# Filter to meaningful periods only
rvi = report_vs_incident.copy()
rvi = rvi[rvi["MAL_PERIOD_10Y"].astype(str).str.match(r"^(19|20)")]
rvi = rvi[rvi["count"] >= 10]  # drop tiny cells

pivot = rvi.pivot_table(index="PERIOD_10Y", columns="MAL_PERIOD_10Y",
                        values="mean_payment_adj", aggfunc="first")
pivot = pivot.reindex(sorted(pivot.index, key=str), axis=0)
pivot = pivot.reindex(sorted(pivot.columns, key=str), axis=1)

sns.heatmap(pivot, annot=True, fmt=",.0f", cmap="YlOrRd", linewidths=0.5, ax=ax,
            cbar_kws={"label": "Mean Payment (2025$)"})
ax.set_xlabel("Incident Decade (MALYEAR1)", fontsize=12)
ax.set_ylabel("Report Decade (ORIGYEAR)", fontsize=12)
ax.set_title("Mean Payment by Report Era vs Incident Era\\n(filtered to n >= 10 per cell)",
             fontsize=13, fontweight="bold")
plt.tight_layout()
plt.show()
''',
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECTION 5: Linkage — after cell 36 (total_source_summary table)
    # ═══════════════════════════════════════════════════════════════
    (
        36,
        '''# --- Linkage source: pie chart + mean payment comparison ---
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Panel 1: Donut chart of TOTALPMT source
source_data = total_source_summary.copy()
colors = ["#55A868", "#4C72B0", "#CCCCCC"]
wedges, texts, autotexts = axes[0].pie(
    source_data["count"], labels=source_data["TOTALPMT_SOURCE"],
    autopct=lambda p: f"{p:.1f}%\\n({int(p * source_data['count'].sum() / 100):,})",
    colors=colors, startangle=90, pctdistance=0.75,
    textprops={"fontsize": 11, "fontweight": "bold"})
centre = plt.Circle((0, 0), 0.55, fc="white")
axes[0].add_artist(centre)
axes[0].set_title("TOTALPMT Source Distribution", fontsize=13, fontweight="bold")

# Panel 2: Mean TOTALPMT_BEST by source (exclude unresolved)
valid_sources = source_data[source_data["TOTALPMT_SOURCE"] != "unresolved"].copy()
bars = axes[1].bar(valid_sources["TOTALPMT_SOURCE"], valid_sources["mean_total_best"],
                   color=["#55A868", "#4C72B0"], width=0.5)
axes[1].set_ylabel("Mean TOTALPMT_BEST (2025$)", fontsize=12)
axes[1].set_title("Reconstructed vs Observed: Mean Total Payment", fontsize=13, fontweight="bold")
for bar, row in zip(bars, valid_sources.itertuples()):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                 f"${row.mean_total_best:,.0f}\\n({row.pct:.1f}%)",
                 ha="center", va="bottom", fontsize=11, fontweight="bold")

plt.tight_layout()
plt.show()
''',
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4: Practitioner classification — after cell 27 (examples cell)
    # ═══════════════════════════════════════════════════════════════
    (
        28,
        '''# --- Practitioner profile classification visualization ---
if "practitioner_profile" in classified.columns and len(classified) > 0:
    fig, axes = plt.subplots(1, 2, figsize=(18, 6))

    # Panel 1: Profile distribution (count + pct)
    prof_counts = classified["practitioner_profile"].value_counts().sort_values()
    total_pract = prof_counts.sum()
    profile_colors = {
        "Chronic Repeater": "#C44E52", "Catastrophic Event": "#DD8452",
        "Batch Reporter": "#4C72B0", "Moderate Repeater": "#55A868"
    }
    bar_colors = [profile_colors.get(p, "#999999") for p in prof_counts.index]
    bars = axes[0].barh(prof_counts.index, prof_counts.values, color=bar_colors)
    axes[0].set_xlabel("Number of Practitioners", fontsize=12)
    axes[0].set_title("Multi-Payment Practitioner Profiles", fontsize=13, fontweight="bold")
    for bar, ct in zip(bars, prof_counts.values):
        axes[0].text(bar.get_width(), bar.get_y() + bar.get_height()/2,
                     f"  {ct:,} ({ct/total_pract*100:.1f}%)",
                     va="center", fontsize=10, fontweight="bold")

    # Panel 2: Mean total payment by profile
    prof_payment = classified.groupby("practitioner_profile")["total_payment_adj"].mean().reindex(prof_counts.index)
    bars2 = axes[1].barh(prof_payment.index, prof_payment.values, color=bar_colors)
    axes[1].set_xlabel("Mean Total Payment (2025$)", fontsize=12)
    axes[1].set_title("Mean Liability by Profile Type", fontsize=13, fontweight="bold")
    for bar, val in zip(bars2, prof_payment.values):
        axes[1].text(bar.get_width(), bar.get_y() + bar.get_height()/2,
                     f"  ${val:,.0f}", va="center", fontsize=10, fontweight="bold")

    plt.tight_layout()
    plt.show()
''',
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4: Payment mode by period — after cell 29 (payment_mode_by_period table)
    # ═══════════════════════════════════════════════════════════════
    (
        29,
        '''# --- Payment mode trend over time (stacked bar with percentages) ---
fig, ax = plt.subplots(figsize=(12, 6))

pmbp = payment_mode_by_period.copy()
pivot = pmbp.pivot_table(index="PERIOD_10Y", columns="PAYMENT_MODE", values="pct", fill_value=0)
pivot = pivot.reindex(sorted(pivot.index, key=str))

# Stacked bar
bottom = np.zeros(len(pivot))
mode_colors = {"Single Payment": "#4C72B0", "Multiple Payments": "#C44E52", "Unknown Payment Mode": "#CCCCCC"}
for col in pivot.columns:
    bars = ax.bar(range(len(pivot)), pivot[col], bottom=bottom,
                  label=col, color=mode_colors.get(col, "#999999"), width=0.6)
    for i, (val, bot) in enumerate(zip(pivot[col], bottom)):
        if val > 1:
            ax.text(i, bot + val/2, f"{val:.1f}%", ha="center", va="center",
                    fontsize=10, fontweight="bold", color="white")
    bottom += pivot[col].values

ax.set_xticks(range(len(pivot)))
ax.set_xticklabels(pivot.index.astype(str), fontsize=11)
ax.set_ylabel("Share (%)", fontsize=12)
ax.set_title("Payment Mode Mix by Decade (Post-2004)", fontsize=13, fontweight="bold")
ax.legend(fontsize=11, loc="upper right")
ax.set_ylim(0, 105)
plt.tight_layout()
plt.show()
''',
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4: Single vs Multiple comparison — after cell 23 (comparison table)
    # Add percentage formatted version
    # ═══════════════════════════════════════════════════════════════
    (
        23,
        '''# --- Single vs Multiple: Enhanced comparison with percentages ---
compare_display = payment_mode_compare.copy()
total_payment = compare_display["total_payment_adj"].sum()
compare_display["pct_of_total_dollars"] = (compare_display["total_payment_adj"] / total_payment * 100).round(1)
compare_display["mean_fmt"] = compare_display["mean_payment_adj"].apply(lambda x: f"${x:,.0f}")
compare_display["median_fmt"] = compare_display["median_payment_adj"].apply(lambda x: f"${x:,.0f}")
compare_display["total_fmt"] = compare_display["total_payment_adj"].apply(lambda x: f"${x:,.0f}")
compare_display["count_pct"] = compare_display["pct"].apply(lambda x: f"{x:.1f}%")
print("=== Single vs Multiple Payment: Key Metrics ===\\n")
print(compare_display[["PAYMENT_MODE", "count", "count_pct", "mean_fmt", "median_fmt",
                        "total_fmt", "pct_of_total_dollars"]].to_string(index=False))
print(f"\\nMean-to-Median Ratios:")
for _, row in compare_display.iterrows():
    ratio = row["mean_payment_adj"] / row["median_payment_adj"]
    print(f"  {row['PAYMENT_MODE']}: {ratio:.2f}x")
''',
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECTION 2: Missingness — after cell 13 (missingness by rectype table)
    # ═══════════════════════════════════════════════════════════════
    (
        13,
        '''# --- Missingness heatmap by RECTYPE ---
fig, ax = plt.subplots(figsize=(12, 6))

miss_data = clean_df[clean_df["RECTYPE"].isin(["M", "P"])].copy()
miss_cols = ["TOTALPMT", "OUTCOME", "PTSEX", "PTAGE", "WORKSTAT", "PAYNUMBR", "ALGNNATR"]
miss_pcts = miss_data.groupby("RECTYPE")[miss_cols].apply(lambda g: g.isna().mean() * 100)
miss_pcts = miss_pcts.reindex(["M", "P"])

sns.heatmap(miss_pcts, annot=True, fmt=".1f", cmap="RdYlGn_r", linewidths=0.5, ax=ax,
            vmin=0, vmax=100, cbar_kws={"label": "% Missing"})
ax.set_xlabel("Column", fontsize=12)
ax.set_ylabel("Record Type", fontsize=12)
ax.set_yticklabels(["M (Pre-2004)", "P (Post-2004)"], rotation=0, fontsize=11)
ax.set_title("Missingness by Record Type: Malpractice Records Only", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.show()
''',
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECTION 1: Raw audit — after cell 6 (RECTYPE distribution table)
    # ═══════════════════════════════════════════════════════════════
    (
        6,
        '''# --- Record type distribution: pie chart ---
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

rectype_counts = raw_df["RECTYPE"].value_counts()
rec_colors = {"C": "#4C72B0", "P": "#55A868", "M": "#DD8452", "A": "#C44E52"}
colors = [rec_colors.get(r, "#999999") for r in rectype_counts.index]

# Panel 1: All record types
wedges, texts, autotexts = axes[0].pie(
    rectype_counts.values, labels=rectype_counts.index,
    autopct=lambda p: f"{p:.1f}%\\n({int(p * len(raw_df) / 100):,})",
    colors=colors, startangle=90, pctdistance=0.75,
    textprops={"fontsize": 11, "fontweight": "bold"})
centre = plt.Circle((0, 0), 0.55, fc="white")
axes[0].add_artist(centre)
axes[0].set_title("All NPDB Records by Type", fontsize=13, fontweight="bold")

# Panel 2: Malpractice only (M vs P)
mal_counts = rectype_counts[rectype_counts.index.isin(["M", "P"])]
mal_colors = [rec_colors[r] for r in mal_counts.index]
wedges2, texts2, autotexts2 = axes[1].pie(
    mal_counts.values, labels=["P (Post-2004)", "M (Pre-2004)"],
    autopct=lambda p: f"{p:.1f}%\\n({int(p * mal_counts.sum() / 100):,})",
    colors=mal_colors, startangle=90, pctdistance=0.75,
    textprops={"fontsize": 11, "fontweight": "bold"})
centre2 = plt.Circle((0, 0), 0.55, fc="white")
axes[1].add_artist(centre2)
axes[1].set_title("Malpractice Records Only (M + P)", fontsize=13, fontweight="bold")

plt.tight_layout()
plt.show()
''',
    ),
]

# Sort by position descending so insertions don't shift indices
viz_cells.sort(key=lambda x: x[0], reverse=True)

for after_idx, code in viz_cells:
    new_cell = make_code_cell(code)
    nb["cells"].insert(after_idx + 1, new_cell)
    print(f"Inserted viz cell after cell {after_idx}")

with open(NOTEBOOK, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"\nDone. Inserted {len(viz_cells)} visualization cells.")
print(f"New total cells: {len(nb['cells'])}")
