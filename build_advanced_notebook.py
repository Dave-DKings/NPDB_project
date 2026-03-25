#!/usr/bin/env python3
"""Generate the structured advanced NPDB analysis notebook."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
NOTEBOOK_PATH = PROJECT_ROOT / "advanced_NPDB.ipynb"


def md_cell(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line if line.endswith("\n") else f"{line}\n" for line in source.strip("\n").splitlines()],
    }


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line if line.endswith("\n") else f"{line}\n" for line in source.strip("\n").splitlines()],
    }


def build_cells() -> list[dict]:
    return [
        md_cell(
            """
            # NPDB Advanced Analysis

            This notebook implements the advanced workflow for malpractice payment structure, hierarchical state analysis, Wisconsin peer benchmarking, linkage validation, and predictive modeling.

            **Core rules**

            - malpractice cohort only: `RECTYPE in ['M', 'P']`
            - all money shown in **2025 dollars**
            - report both **counts and percentages**
            - keep **single**, **multiple**, and **unknown** payment modes separate
            - distinguish **observed**, **reconstructed**, and **unresolved** total payments
            """
        ),
        md_cell(
            """
            ## Workflow Artifacts

            The notebook is intentionally thin. Most logic lives in reusable modules under `npdb_analysis/`.

            Supporting methodology notes:

            - `docs/linkage_methodology.md`
            - `docs/wisconsin_peer_selection.md`
            - `docs/policy_notes_settlement_disclosure.md`
            """
        ),
        md_cell(
            """
            ## Notebook Map

            This notebook is organized in execution order.

            1. raw load and schema audit
            2. initial transformation, dtype correction, and NaN handling
            3. feature engineering and 2025-dollar normalization
            4. payment mode separation
            5. linkage validation and cautious pre-2004 reconstruction
            6. time-grouped analysis
            7. hierarchical all-state analysis
            8. Wisconsin and peer-state comparison
            9. practitioner multi-state presence
            10. settlement vs judgment context
            11. severity and catastrophic modeling
            12. time-to-payment analysis

            The notebook is designed to be run top-to-bottom the first time. After the foundation sections are executed, descriptive and modeling sections can be rerun independently.
            """
        ),
        md_cell(
            """
            ## Runtime Bootstrap

            This section is especially important in Colab. It tries to find the project root, add it to `sys.path`, and resolve the CSV path without requiring manual edits inside the analysis modules.
            """
        ),
        md_cell(
            """
            ### Colab Data Flow

            In Colab, the bootstrap cell below will:

            1. mount Google Drive
            2. look for `NPDB2510.CSV` in Drive first
            3. if it is not already in Drive, accept a one-time upload into the Colab session
            4. copy that uploaded file into Drive
            5. continue using the Drive-backed CSV path for the rest of the notebook

            This avoids re-uploading the raw CSV every time you reconnect to Colab.
            """
        ),
        code_cell(
            """
            import os
            import shutil
            import sys
            from pathlib import Path

            def detect_colab() -> bool:
                try:
                    import google.colab  # type: ignore
                    return True
                except ImportError:
                    return False

            IS_COLAB = detect_colab()

            DRIVE_PROJECT_DATA_DIR = Path("/content/drive/MyDrive/NPDB Project/NpdbPublicUseDataCsv")
            DRIVE_DATA_PATH = DRIVE_PROJECT_DATA_DIR / "NPDB2510.CSV"

            if IS_COLAB:
                from google.colab import drive, files  # type: ignore

                drive.mount("/content/drive", force_remount=False)
                DRIVE_PROJECT_DATA_DIR.mkdir(parents=True, exist_ok=True)

            candidate_roots = []
            env_root = os.environ.get("NPDB_PROJECT_ROOT")
            if env_root:
                candidate_roots.append(Path(env_root).expanduser())

            candidate_roots.extend(
                [
                    Path.cwd(),
                    Path.cwd() / "NPDB_project",
                    Path.cwd() / "npdb_project",
                    Path("/content/NPDB_project"),
                    Path("/content/npdb_project"),
                    Path("/content/drive/MyDrive/NPDB Project"),
                    Path("/content/drive/MyDrive/NPDB_project"),
                ]
            )

            PROJECT_ROOT = None
            for candidate in candidate_roots:
                if (candidate / "npdb_analysis").exists():
                    PROJECT_ROOT = candidate.resolve()
                    break

            if PROJECT_ROOT is None:
                raise FileNotFoundError(
                    "Could not find the project root containing 'npdb_analysis'. "
                    "In Colab, clone the GitHub repo first, for example: "
                    "!git clone https://github.com/Dave-DKings/NPDB_project.git /content/npdb_project"
                )

            if str(PROJECT_ROOT) not in sys.path:
                sys.path.insert(0, str(PROJECT_ROOT))

            os.environ["NPDB_PROJECT_ROOT"] = str(PROJECT_ROOT)

            data_candidates = []
            env_data = os.environ.get("NPDB_DATA_PATH")
            if env_data:
                data_candidates.append(Path(env_data).expanduser())

            if IS_COLAB and DRIVE_DATA_PATH.exists():
                data_candidates.append(DRIVE_DATA_PATH)

            data_candidates.extend(
                [
                    PROJECT_ROOT / "NpdbPublicUseDataCsv" / "NPDB2510.CSV",
                    Path("/content/NPDB2510.CSV"),
                    Path("/content/drive/MyDrive/NPDB2510.CSV"),
                    Path("/content/drive/MyDrive/NPDB Project/NpdbPublicUseDataCsv/NPDB2510.CSV"),
                ]
            )

            DATA_PATH_OVERRIDE = None
            for candidate in data_candidates:
                if candidate.exists():
                    DATA_PATH_OVERRIDE = candidate.resolve()
                    break

            if IS_COLAB:
                if DATA_PATH_OVERRIDE is None:
                    print("NPDB2510.CSV not found in Drive or the current Colab session.")
                    print("Choose the file now. It will be copied into Google Drive for reuse.")
                    uploaded = files.upload()
                    if "NPDB2510.CSV" not in uploaded:
                        raise FileNotFoundError(
                            "Upload failed or a file other than 'NPDB2510.CSV' was provided. "
                            "Upload the raw NPDB CSV with the exact filename 'NPDB2510.CSV'."
                        )
                    uploaded_path = Path("/content/NPDB2510.CSV")
                    shutil.copy2(uploaded_path, DRIVE_DATA_PATH)
                    DATA_PATH_OVERRIDE = DRIVE_DATA_PATH.resolve()
                    print(f"Uploaded file copied to Drive: {DATA_PATH_OVERRIDE}")
                elif DATA_PATH_OVERRIDE.name == "NPDB2510.CSV" and str(DATA_PATH_OVERRIDE).startswith("/content/") and not str(DATA_PATH_OVERRIDE).startswith("/content/drive/"):
                    shutil.copy2(DATA_PATH_OVERRIDE, DRIVE_DATA_PATH)
                    DATA_PATH_OVERRIDE = DRIVE_DATA_PATH.resolve()
                    print(f"Session upload copied to Drive: {DATA_PATH_OVERRIDE}")

            if DATA_PATH_OVERRIDE is not None:
                os.environ["NPDB_DATA_PATH"] = str(DATA_PATH_OVERRIDE)

            print(f"Colab runtime: {IS_COLAB}")
            print(f"Project root: {PROJECT_ROOT}")
            print(f"Data path found: {DATA_PATH_OVERRIDE}")
            """
        ),
        code_cell(
            """
            import matplotlib.pyplot as plt
            import numpy as np
            import pandas as pd
            import seaborn as sns

            from npdb_analysis.aggregation import (
                hierarchical_state_period_mode,
                multi_state_pairs,
                practitioner_state_mobility,
                state_level_summary,
                summarize_by_period,
                wisconsin_peer_comparison,
            )
            from npdb_analysis.config import DATA_PATH, NPDB_PEER_STATES, PROJECT_ROOT
            from npdb_analysis.features import add_common_features
            from npdb_analysis.linkage import (
                derive_payment_episodes,
                merge_total_payment_best,
                validate_linkage,
                validation_metrics,
            )
            from npdb_analysis.loading import build_column_profile, load_npdb_csv, rectype_counts
            from npdb_analysis.modeling import (
                exceedance_table,
                fit_catastrophic_logit,
                fit_gamma_glm,
                fit_log_ols,
                fit_single_payment_distributions,
                prepare_lag_frame,
                prepare_severity_frame,
            )
            from npdb_analysis.payment_modes import (
                add_payment_mode_labels,
                payment_mode_distribution,
                practitioner_multi_payment_profile,
                single_multiple_comparison,
            )
            from npdb_analysis.plotting import plot_count_pct_bar, plot_state_period_heatmap, plot_wisconsin_peers
            from npdb_analysis.transforms import clean_npdb, dtype_audit, structural_missingness_summary

            pd.set_option("display.max_columns", 80)
            pd.set_option("display.max_rows", 200)
            pd.set_option("display.float_format", "{:,.2f}".format)
            sns.set_theme(style="whitegrid", context="talk")

            PROJECT_ROOT, DATA_PATH
            """
        ),
        md_cell(
            """
            ### Runtime Check

            If this import cell fails, fix the environment first. The rest of the notebook assumes the reusable modules are importable and the NPDB CSV is available at the configured path.
            """
        ),
        md_cell(
            """
            ## 1. Raw Data Load and Initial Audit

            This section checks schema shape, record types, and the raw missingness profile before any transformation.
            """
        ),
        code_cell(
            """
            raw_df = load_npdb_csv(DATA_PATH, low_memory=False)

            print(f"Raw shape: {raw_df.shape[0]:,} rows x {raw_df.shape[1]} columns")
            print(f"ORIGYEAR range: {raw_df['ORIGYEAR'].min()} - {raw_df['ORIGYEAR'].max()}")

            rectype_counts(raw_df)
            """
        ),
        code_cell(
            """
            raw_profile = build_column_profile(raw_df)
            raw_profile.head(20)
            """
        ),
        code_cell(
            """
            key_columns = [
                "RECTYPE",
                "ORIGYEAR",
                "MALYEAR1",
                "PAYMENT",
                "TOTALPMT",
                "PAYNUMBR",
                "PAYTYPE",
                "WORKSTAT",
                "LICNSTAT",
                "HOMESTAT",
                "PRACTNUM",
                "ALGNNATR",
                "OUTCOME",
            ]
            raw_profile[raw_profile["column"].isin(key_columns)].sort_values("column")
            """
        ),
        md_cell(
            """
            ## 2. Data Transformation and Missingness Handling

            This is the mandatory foundation layer:

            - fix dollar-string columns
            - cast coded numeric fields carefully
            - normalize string code fields
            - separate structural from non-structural missingness
            """
        ),
        code_cell(
            """
            clean_df = clean_npdb(raw_df)

            print("Cleaned dtype audit:")
            dtype_audit(clean_df).head(20)
            """
        ),
        code_cell(
            """
            dtype_audit(clean_df).query("column in @key_columns").sort_values("column")
            """
        ),
        code_cell(
            """
            missingness_cols = [
                "TOTALPMT",
                "OUTCOME",
                "PTSEX",
                "PTAGE",
                "WORKSTAT",
                "PAYNUMBR",
                "ALGNNATR",
                "PAYTYPE",
            ]
            missingness_summary = structural_missingness_summary(clean_df, missingness_cols)
            missingness_summary
            """
        ),
        md_cell(
            """
            ### Interpretation Checkpoint

            Before proceeding, confirm the expected structural missingness pattern:

            - legacy malpractice records should drive much of the missingness in `TOTALPMT`, `OUTCOME`, `PTAGE`, `PTSEX`, and `PAYNUMBR`
            - state fields should show partial coverage, which is why the composite fallback is required
            """
        ),
        md_cell(
            """
            ## 3. Common Feature Engineering

            The analysis dataset adds:

            - malpractice-only cohort filter
            - composite `STATE`
            - 5-year and 10-year period groupings
            - CPI-normalized money columns
            - resolution flags
            - lag and catastrophic indicators
            """
        ),
        code_cell(
            """
            mal = add_common_features(clean_df)
            mal = add_payment_mode_labels(mal)

            print(f"Malpractice analysis shape: {mal.shape[0]:,} rows x {mal.shape[1]} columns")
            mal[[
                "SEQNO",
                "RECTYPE",
                "STATE",
                "PERIOD_10Y",
                "MAL_PERIOD_10Y",
                "PAYMENT",
                "PAYMENT_ADJ",
                "TOTALPMT",
                "TOTALPMT_ADJ",
                "PAYMENT_MODE",
                "RESOLUTION_BINARY",
                "LAG_YEARS",
            ]].head()
            """
        ),
        code_cell(
            """
            baseline_summary = pd.DataFrame(
                {
                    "metric": [
                        "malpractice_rows",
                        "states_with_data",
                        "mean_payment_adj",
                        "median_payment_adj",
                        "catastrophic_share_pct",
                        "judgment_share_pct",
                    ],
                    "value": [
                        len(mal),
                        mal["STATE"].nunique(dropna=True),
                        mal["PAYMENT_ADJ"].mean(),
                        mal["PAYMENT_ADJ"].median(),
                        mal["CATASTROPHIC"].mean() * 100,
                        mal["IS_JUDGMENT"].mean() * 100,
                    ],
                }
            )
            baseline_summary
            """
        ),
        code_cell(
            """
            feature_quality = pd.DataFrame(
                {
                    "metric": [
                        "missing_state_pct",
                        "missing_allegation_pct",
                        "missing_outcome_pct",
                        "payment_mode_known_pct",
                        "observed_totalpmt_pct",
                    ],
                    "value": [
                        mal["MISSING_STATE"].mean() * 100,
                        mal["MISSING_ALLEGATION"].mean() * 100,
                        mal["MISSING_OUTCOME"].mean() * 100,
                        (~mal["PAYMENT_MODE"].isin(["Unknown Payment Mode", "Unavailable Pre-2004"])).mean() * 100,
                        mal["TOTALPMT_ADJ"].notna().mean() * 100,
                    ],
                }
            )
            feature_quality
            """
        ),
        md_cell(
            """
            ## 4. Payment Mode Separation

            This section separates post-2004 single-payment and multiple-payment structures while keeping unknown/unavailable categories explicit.
            """
        ),
        code_cell(
            """
            payment_mode_overall = payment_mode_distribution(mal)
            payment_mode_overall
            """
        ),
        code_cell(
            """
            payment_mode_compare = single_multiple_comparison(mal)
            payment_mode_compare
            """
        ),
        code_cell(
            """
            fig, axes = plt.subplots(1, 2, figsize=(18, 6))
            plot_count_pct_bar(payment_mode_overall, category_col="PAYMENT_MODE", ax=axes[0])
            axes[0].tick_params(axis="x", rotation=30)

            sns.boxplot(
                data=mal[mal["PAYMENT_MODE"].isin(["Single Payment", "Multiple Payments"])],
                x="PAYMENT_MODE",
                y="PAYMENT_ADJ",
                ax=axes[1],
            )
            axes[1].set_yscale("log")
            axes[1].tick_params(axis="x", rotation=20)
            axes[1].set_title("Adjusted Payment Distribution by Payment Mode")
            plt.tight_layout()
            plt.show()
            """
        ),
        code_cell(
            """
            multi_practitioner_profile = practitioner_multi_payment_profile(mal)
            multi_practitioner_profile.head(20)
            """
        ),
        code_cell(
            """
            payment_mode_by_period = payment_mode_distribution(
                mal[mal["RECTYPE"].astype("string") == "P"].copy(),
                group_cols=["PERIOD_10Y"],
            )
            payment_mode_by_period.head(20)
            """
        ),
        md_cell(
            """
            ## 5. Linkage Validation and Pre-2004 Reconstruction

            The goal is not to assume a true claim ID exists. Instead, this section validates a `derived payment episode` rule on post-2004 records before any pre-2004 reconstruction is attempted.
            """
        ),
        code_cell(
            """
            post_2004 = mal[mal["RECTYPE"].astype("string") == "P"].copy()
            pre_2004 = mal[mal["RECTYPE"].astype("string") == "M"].copy()

            strict_episodes, strict_validation = validate_linkage(post_2004, tier="strict")
            moderate_episodes, moderate_validation = validate_linkage(post_2004, tier="moderate")

            strict_metrics = validation_metrics(strict_validation)
            strict_metrics["tier"] = "strict"
            moderate_metrics = validation_metrics(moderate_validation)
            moderate_metrics["tier"] = "moderate"

            pd.concat([strict_metrics, moderate_metrics], ignore_index=True)
            """
        ),
        code_cell(
            """
            strict_validation.sort_values("absolute_pct_error").head(20)
            """
        ),
        code_cell(
            """
            strict_episodes["ambiguous_episode"].value_counts(dropna=False).rename_axis("ambiguous_episode").reset_index(name="count")
            """
        ),
        code_cell(
            """
            # Prefer strict linkage by default.
            all_strict_episodes = derive_payment_episodes(mal, tier="strict")
            mal_linked = merge_total_payment_best(mal, all_strict_episodes)

            mal_linked["TOTALPMT_SOURCE"].value_counts(dropna=False).rename_axis("TOTALPMT_SOURCE").reset_index(name="count")
            """
        ),
        code_cell(
            """
            total_source_summary = (
                mal_linked.groupby("TOTALPMT_SOURCE")
                .agg(
                    count=("SEQNO", "size"),
                    mean_total_best=("TOTALPMT_BEST", "mean"),
                    median_total_best=("TOTALPMT_BEST", "median"),
                    total_total_best=("TOTALPMT_BEST", "sum"),
                )
                .reset_index()
            )
            total_source_summary["pct"] = total_source_summary["count"] / total_source_summary["count"].sum() * 100
            total_source_summary
            """
        ),
        md_cell(
            """
            ### Reconstruction Rule

            If strict-linkage validation looks poor, stop here and keep `TOTALPMT_BEST` out of interpretive sections. The notebook is designed so the rest of the descriptive workflow can still run on report-level adjusted payments.
            """
        ),
        md_cell(
            """
            ## 6. Time-Grouped Analysis

            Use both report-year and incident-year buckets. `ORIGYEAR` supports reporting/payment system trends, while `MALYEAR1` is closer to incident-era and legal-environment timing.
            """
        ),
        code_cell(
            """
            period_10y_summary = summarize_by_period(mal_linked, "PERIOD_10Y")
            period_5y_summary = summarize_by_period(mal_linked, "PERIOD_5Y")

            period_10y_summary
            """
        ),
        code_cell(
            """
            mal_period_10y_summary = summarize_by_period(mal_linked.dropna(subset=["MAL_PERIOD_10Y"]), "MAL_PERIOD_10Y")
            mal_period_10y_summary
            """
        ),
        code_cell(
            """
            fig, axes = plt.subplots(1, 2, figsize=(18, 6))
            sns.barplot(data=period_10y_summary, x="PERIOD_10Y", y="count", ax=axes[0], color="steelblue")
            axes[0].tick_params(axis="x", rotation=45)
            axes[0].set_title("Report-Year 10Y Count")

            sns.lineplot(data=period_10y_summary, x="PERIOD_10Y", y="mean_payment_adj", marker="o", ax=axes[1])
            axes[1].tick_params(axis="x", rotation=45)
            axes[1].set_title("Mean Adjusted Payment by Report-Year 10Y")
            plt.tight_layout()
            plt.show()
            """
        ),
        code_cell(
            """
            report_vs_incident = (
                mal_linked.dropna(subset=["PERIOD_10Y", "MAL_PERIOD_10Y"])
                .groupby(["PERIOD_10Y", "MAL_PERIOD_10Y"])
                .agg(mean_payment_adj=("PAYMENT_ADJ", "mean"), count=("SEQNO", "size"))
                .reset_index()
            )
            report_vs_incident.head(20)
            """
        ),
        md_cell(
            """
            ## 7. Hierarchical State Analysis

            The core grouped table is:

            `STATE -> PERIOD_10Y -> PAYMENT_MODE`

            This table supports national comparisons, state drilldowns, and Wisconsin-focused analysis from one consistent structure.
            """
        ),
        code_cell(
            """
            state_summary = state_level_summary(mal_linked)
            state_summary.head(20)
            """
        ),
        code_cell(
            """
            state_period_mode = hierarchical_state_period_mode(
                mal_linked[mal_linked["RECTYPE"].astype("string") == "P"].copy()
            )
            state_period_mode.head(20)
            """
        ),
        code_cell(
            """
            top_states = state_summary["STATE"].dropna().astype(str).head(15).tolist()
            heatmap_input = (
                state_period_mode[state_period_mode["STATE"].astype("string").isin(top_states)]
                .groupby(["STATE", "PERIOD_10Y"])
                .agg(mean_payment_adj=("mean_payment_adj", "mean"))
                .reset_index()
            )

            plt.figure(figsize=(14, 10))
            plot_state_period_heatmap(heatmap_input)
            plt.tight_layout()
            plt.show()
            """
        ),
        code_cell(
            """
            state_period_summary = (
                state_period_mode.groupby(["STATE", "PERIOD_10Y"])
                .agg(
                    total_count=("count", "sum"),
                    avg_mean_payment_adj=("mean_payment_adj", "mean"),
                    avg_catastrophic_share=("catastrophic_share", "mean"),
                )
                .reset_index()
                .sort_values(["STATE", "PERIOD_10Y"])
            )
            state_period_summary.head(20)
            """
        ),
        md_cell(
            """
            ## 8. Wisconsin and Peer-State Comparison

            Wisconsin is analyzed both on its own and against a fixed Upper Midwest peer set.
            """
        ),
        code_cell(
            """
            wi_peer_summary = wisconsin_peer_comparison(mal_linked, states=NPDB_PEER_STATES)
            wi_peer_summary
            """
        ),
        code_cell(
            """
            plt.figure(figsize=(14, 7))
            plot_wisconsin_peers(wi_peer_summary, value_col="mean_payment_adj")
            plt.tight_layout()
            plt.show()
            """
        ),
        code_cell(
            """
            wi_state_period_mode = state_period_mode[state_period_mode["STATE"].astype("string").isin(NPDB_PEER_STATES)]
            wi_state_period_mode.sort_values(["STATE", "PERIOD_10Y", "PAYMENT_MODE"]).head(30)
            """
        ),
        code_cell(
            """
            wisconsin_only = wi_peer_summary[wi_peer_summary["STATE"].astype("string") == "WI"].copy()
            wisconsin_only
            """
        ),
        md_cell(
            """
            ## 9. Practitioner Multi-State Presence

            This section is descriptive. A practitioner appearing in multiple states can reflect relocation, multi-state licensure, or reporting variation.
            """
        ),
        code_cell(
            """
            mobility = practitioner_state_mobility(mal_linked)

            mobility_summary = pd.DataFrame(
                {
                    "metric": [
                        "practitioners_total",
                        "multi_state_practitioners",
                        "multi_state_share_pct",
                        "mean_payment_single_state",
                        "mean_payment_multi_state",
                    ],
                    "value": [
                        len(mobility),
                        int(mobility["multi_state_practitioner"].sum()),
                        mobility["multi_state_practitioner"].mean() * 100,
                        mobility.loc[~mobility["multi_state_practitioner"], "mean_payment_adj"].mean(),
                        mobility.loc[mobility["multi_state_practitioner"], "mean_payment_adj"].mean(),
                    ],
                }
            )
            mobility_summary
            """
        ),
        code_cell(
            """
            state_pairs = multi_state_pairs(mal_linked, top_n=20)
            state_pairs
            """
        ),
        code_cell(
            """
            mobility.groupby("multi_state_practitioner").agg(
                practitioners=("PRACTNUM", "size"),
                mean_record_count=("record_count", "mean"),
                mean_total_payment_adj=("total_payment_adj", "mean"),
                mean_years_spanned=("years_spanned", "mean"),
            )
            """
        ),
        md_cell(
            """
            ## 10. Settlement vs Judgment and Policy Context

            NPDB data supports quantitative resolution analysis. It does not, by itself, identify causal effects of settlement-disclosure law.
            """
        ),
        code_cell(
            """
            settlement_state = (
                mal_linked.groupby(["STATE", "RESOLUTION_BINARY"])
                .agg(
                    count=("SEQNO", "size"),
                    mean_payment_adj=("PAYMENT_ADJ", "mean"),
                    median_payment_adj=("PAYMENT_ADJ", "median"),
                )
                .reset_index()
            )
            settlement_state["pct_within_state"] = (
                settlement_state["count"]
                / settlement_state.groupby("STATE")["count"].transform("sum")
                * 100
            ).round(2)
            settlement_state.head(30)
            """
        ),
        code_cell(
            """
            settlement_period = (
                mal_linked.groupby(["PERIOD_10Y", "RESOLUTION_BINARY"])
                .size()
                .reset_index(name="count")
            )
            settlement_period["pct_within_period"] = (
                settlement_period["count"]
                / settlement_period.groupby("PERIOD_10Y")["count"].transform("sum")
                * 100
            ).round(2)
            settlement_period
            """
        ),
        code_cell(
            """
            wi_settlement_state = settlement_state[settlement_state["STATE"].astype("string").isin(NPDB_PEER_STATES)].copy()
            wi_settlement_state.head(30)
            """
        ),
        md_cell(
            """
            ## 11. Loss Distribution Fitting and Severity Modeling

            Distribution fitting is restricted to single-payment records. Severity models should mainly use post-2004 records when they rely on richer patient or outcome fields.
            """
        ),
        code_cell(
            """
            single_payment_values = mal_linked.loc[mal_linked["PAYMENT_MODE"] == "Single Payment", "PAYMENT_ADJ"]
            distribution_fits = fit_single_payment_distributions(single_payment_values)
            distribution_fits
            """
        ),
        code_cell(
            """
            thresholds = [100_000, 250_000, 500_000, 1_000_000, 2_000_000, 5_000_000]
            exceedance_table(single_payment_values, thresholds)
            """
        ),
        code_cell(
            """
            severity_columns = ["OUTCOME", "PRACTAGE", "STATE", "PERIOD_10Y", "RESOLUTION_BINARY", "ALGNNATR"]
            severity_df = prepare_severity_frame(
                mal_linked[mal_linked["RECTYPE"].astype("string") == "P"].copy(),
                severity_columns,
            )

            severity_formula = "LOG_PAYMENT_ADJ ~ C(OUTCOME) + C(RESOLUTION_BINARY) + C(PERIOD_10Y) + C(STATE)"
            severity_ols = fit_log_ols(severity_df, severity_formula)
            severity_ols.summary().tables[1]
            """
        ),
        code_cell(
            """
            gamma_formula = "PAYMENT_ADJ ~ C(OUTCOME) + C(RESOLUTION_BINARY) + C(PERIOD_10Y) + C(STATE)"
            severity_gamma = fit_gamma_glm(severity_df, gamma_formula)
            severity_gamma.summary().tables[1]
            """
        ),
        code_cell(
            """
            catastrophic_features = ["OUTCOME", "PRACTAGE", "LAG_YEARS", "STATE", "RESOLUTION_BINARY", "ALGNNATR"]
            catastrophic_results = fit_catastrophic_logit(
                severity_df,
                feature_columns=catastrophic_features,
                target="CATASTROPHIC",
            )
            catastrophic_results
            """
        ),
        md_cell(
            """
            ### Modeling Checkpoint

            The severity and catastrophic models are intended as first-pass research models, not final production estimators. Revisit feature scope, interactions, and validation once the descriptive state and payment-mode findings are stable.
            """
        ),
        md_cell(
            """
            ## 12. Time-to-Payment Analysis

            This is a paid-claim lag analysis, not a full censored-claims survival dataset.
            """
        ),
        code_cell(
            """
            lag_df = prepare_lag_frame(mal_linked)

            lag_summary = pd.DataFrame(
                {
                    "metric": [
                        "rows",
                        "mean_lag_years",
                        "median_lag_years",
                        "p90_lag_years",
                        "p95_lag_years",
                    ],
                    "value": [
                        len(lag_df),
                        lag_df["LAG_YEARS"].mean(),
                        lag_df["LAG_YEARS"].median(),
                        lag_df["LAG_YEARS"].quantile(0.90),
                        lag_df["LAG_YEARS"].quantile(0.95),
                    ],
                }
            )
            lag_summary
            """
        ),
        code_cell(
            """
            lag_by_resolution = (
                lag_df.groupby("RESOLUTION_BINARY")
                .agg(
                    count=("SEQNO", "size"),
                    mean_lag_years=("LAG_YEARS", "mean"),
                    median_lag_years=("LAG_YEARS", "median"),
                )
                .reset_index()
            )
            lag_by_resolution
            """
        ),
        code_cell(
            """
            plt.figure(figsize=(12, 6))
            sns.boxplot(data=lag_df[lag_df["LAG_YEARS"].between(0, 20)], x="RESOLUTION_BINARY", y="LAG_YEARS")
            plt.title("Time to Payment by Resolution Type")
            plt.tight_layout()
            plt.show()
            """
        ),
        md_cell(
            """
            ## 13. Recommended Team Workflow

            - Kelvin or David: rerun Sections 1-8 after any data-refresh or transformation change
            - linkage work: review Section 5 together with `docs/linkage_methodology.md`
            - policy interpretation: review Section 10 together with `docs/policy_notes_settlement_disclosure.md`
            - modeling iterations: begin only after the state and payment-mode tables are accepted
            """
        ),
        md_cell(
            """
            ## 14. Execution Notes

            Recommended execution order:

            1. run Sections 1-3 once per data refresh
            2. rerun Sections 4-10 for descriptive outputs
            3. rerun Sections 11-12 only after validating the data slice you want to model

            The notebook depends on the reusable package files under `npdb_analysis/`, so those should remain the primary place for logic changes.
            """
        ),
    ]


def build_notebook() -> dict:
    return {
        "cells": build_cells(),
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    notebook = build_notebook()
    NOTEBOOK_PATH.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    print(f"Wrote {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()
