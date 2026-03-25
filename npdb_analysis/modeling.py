"""Statistical modeling utilities for advanced NPDB analysis."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _prepare_formula_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Convert pandas extension dtypes into statsmodels-friendly dtypes."""
    frame = df.copy()
    for column in frame.columns:
        series = frame[column]
        if pd.api.types.is_integer_dtype(series.dtype) and str(series.dtype) == "Int64":
            frame[column] = pd.to_numeric(series, errors="coerce").astype(float)
        elif pd.api.types.is_bool_dtype(series.dtype) and str(series.dtype) in {"boolean", "BooleanDtype"}:
            frame[column] = series.astype(object)
        elif pd.api.types.is_categorical_dtype(series.dtype):
            frame[column] = series.astype(str)
            frame.loc[series.isna(), column] = np.nan
        elif pd.api.types.is_string_dtype(series.dtype):
            frame[column] = series.astype(object)
    return frame


def prepare_severity_frame(df: pd.DataFrame, required_columns: list[str]) -> pd.DataFrame:
    """Prepare a modeling frame with non-missing covariates."""
    frame = df.copy()
    available = [column for column in required_columns if column in frame.columns]
    frame = frame.dropna(subset=available + ["PAYMENT_ADJ"]).copy()
    frame = frame[frame["PAYMENT_ADJ"] > 0].copy()
    return frame


def fit_log_ols(df: pd.DataFrame, formula: str):
    """Fit an OLS model on log-adjusted payment."""
    import statsmodels.formula.api as smf

    model_df = _prepare_formula_frame(df)
    return smf.ols(formula=formula, data=model_df).fit()


def fit_gamma_glm(df: pd.DataFrame, formula: str):
    """Fit a Gamma GLM with log link."""
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    model_df = _prepare_formula_frame(df)
    return smf.glm(
        formula=formula,
        data=model_df,
        family=sm.families.Gamma(link=sm.families.links.log()),
    ).fit()


def fit_catastrophic_logit(df: pd.DataFrame, feature_columns: list[str], target: str = "CATASTROPHIC") -> dict:
    """Fit a class-weighted logistic regression and return metrics."""
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    frame = df.dropna(subset=[target]).copy()
    X = frame[feature_columns]
    y = frame[target].astype(int)

    numeric_features = [column for column in feature_columns if pd.api.types.is_numeric_dtype(frame[column])]
    categorical_features = [column for column in feature_columns if column not in numeric_features]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            ),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )
    model.fit(X_train, y_train)
    probabilities = model.predict_proba(X_test)[:, 1]
    return {
        "model": model,
        "roc_auc": roc_auc_score(y_test, probabilities),
        "average_precision": average_precision_score(y_test, probabilities),
        "test_rows": len(X_test),
    }


def fit_single_payment_distributions(values: pd.Series) -> pd.DataFrame:
    """Fit common severity distributions by maximum likelihood and rank by AIC/BIC."""
    from scipy import stats

    clean = pd.Series(values).dropna()
    clean = clean[clean > 0]
    if clean.empty:
        return pd.DataFrame()

    candidates = {
        "exponential": stats.expon,
        "gamma": stats.gamma,
        "lognormal": stats.lognorm,
        "weibull_min": stats.weibull_min,
        "lomax": stats.lomax,
    }

    rows = []
    n = len(clean)
    for name, distribution in candidates.items():
        params = distribution.fit(clean)
        log_likelihood = distribution.logpdf(clean, *params).sum()
        k = len(params)
        rows.append(
            {
                "distribution": name,
                "params": params,
                "log_likelihood": log_likelihood,
                "aic": 2 * k - 2 * log_likelihood,
                "bic": math.log(n) * k - 2 * log_likelihood,
            }
        )
    return pd.DataFrame(rows).sort_values(["aic", "bic"]).reset_index(drop=True)


def exceedance_table(values: pd.Series, thresholds: list[float]) -> pd.DataFrame:
    """Compute exceedance probabilities above analyst-chosen thresholds."""
    clean = pd.Series(values).dropna()
    clean = clean[clean > 0]
    if clean.empty:
        return pd.DataFrame()
    rows = []
    for threshold in thresholds:
        exceed_count = int((clean >= threshold).sum())
        rows.append(
            {
                "threshold": threshold,
                "count": exceed_count,
                "pct": round(exceed_count / len(clean) * 100, 4),
            }
        )
    return pd.DataFrame(rows)


def prepare_lag_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Keep observations with valid payment lag."""
    frame = df[df["VALID_LAG"]].copy()
    return frame.dropna(subset=["LAG_YEARS"])
