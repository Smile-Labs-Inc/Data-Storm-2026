"""Chernozhukov-Hong 3-step censored quantile regression.

Reference: Chernozhukov & Hong (2002), "Three-step censored quantile regression
and extramarital affairs".

The team's q90 is currently fitted on observed (capped) sales, so it produces a
DOWNWARD-biased frontier estimate. This module implements the standard fix:

  Step 1: Build a censoring-indicator delta from observable proxies
          (plateau / stockout / credit-cycle / delivery gaps).
  Step 2: Fit a propensity model:  P(censored | X)
  Step 3: Refit the q90 quantile model only on rows where P(censored) < tau.
          The quantile estimate on the uncensored sub-population is
          consistent for q90(true_demand).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


@dataclass
class CensoringCorrection:
    propensity_threshold: float
    n_total: int
    n_uncensored_kept: int
    propensity_summary: pd.DataFrame


def build_censoring_proxy(
    monthly: pd.DataFrame,
    plateau_threshold_months: int = 6,
    variance_ratio_threshold: float = 0.4,
) -> pd.DataFrame:
    """Per outlet-month delta in {0, 1}. 1 = likely censored, 0 = likely uncensored.

    Signals (any one fires -> delta=1):
      - This month is at least plateau_threshold_months below the outlet's max-month
        AND volume is within 5% of the outlet's recent rolling-mean (flat plateau).
      - Volume is within 5% of the outlet's historical max for 3+ consecutive months
        (stuck at ceiling -> capped delivery / credit).
    """
    out = monthly.copy().sort_values(["Outlet_ID", "Year", "Month"])
    rows: list[dict] = []
    for outlet, g in out.groupby("Outlet_ID", sort=False):
        v = g["monthly_volume"].values
        n = len(v)
        if n < 3:
            for _, row in g.iterrows():
                rows.append({
                    "Outlet_ID": outlet,
                    "Year": int(row["Year"]),
                    "Month": int(row["Month"]),
                    "delta": 0,
                })
            continue
        max_v = float(np.max(v))
        roll_mean = pd.Series(v).rolling(3, min_periods=1).mean().values
        for i, row in enumerate(g.itertuples(index=False)):
            stuck_at_ceiling = (
                i >= 2
                and v[i] >= 0.95 * max_v
                and v[i - 1] >= 0.95 * max_v
                and v[i - 2] >= 0.95 * max_v
            )
            recent_flat = (
                i >= plateau_threshold_months
                and abs(v[i] - roll_mean[i]) / max(roll_mean[i], 1e-6) < 0.05
            )
            delta = int(stuck_at_ceiling or recent_flat)
            rows.append({
                "Outlet_ID": outlet,
                "Year": int(row.Year),
                "Month": int(row.Month),
                "delta": delta,
            })
    return pd.DataFrame(rows)


def fit_propensity(
    X: pd.DataFrame,
    delta: pd.Series,
    feature_subset: list[str] | None = None,
) -> tuple[LogisticRegression, pd.Series, StandardScaler]:
    cols = feature_subset or list(X.columns)
    X_use = X[cols].fillna(X[cols].median(numeric_only=True)).fillna(0.0).values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X_use)
    model = LogisticRegression(max_iter=200, n_jobs=-1)
    model.fit(Xs, delta.values.astype(int))
    p = pd.Series(model.predict_proba(Xs)[:, 1], index=X.index, name="p_censored")
    return model, p, scaler


def select_uncensored(
    p_censored: pd.Series,
    threshold: float = 0.10,
) -> pd.Series:
    """Boolean mask: True if row is likely uncensored (P(censored) < threshold)."""
    return p_censored < threshold


def chernozhukov_hong_correction(
    X: pd.DataFrame,
    y: pd.Series,
    delta_proxy: pd.Series,
    propensity_threshold: float = 0.10,
) -> tuple[pd.DataFrame, pd.Series, CensoringCorrection]:
    """Returns (X_uncensored, y_uncensored, correction_summary).

    The caller then refits their q90 model on the returned subset.
    """
    _, p_censored, _ = fit_propensity(X, delta_proxy)
    keep_mask = select_uncensored(p_censored, propensity_threshold)
    n_total = int(len(X))
    n_kept = int(keep_mask.sum())

    summary = pd.DataFrame({
        "min": [float(p_censored.min())],
        "p25": [float(p_censored.quantile(0.25))],
        "median": [float(p_censored.median())],
        "p75": [float(p_censored.quantile(0.75))],
        "max": [float(p_censored.max())],
        "n_total": [n_total],
        "n_kept": [n_kept],
        "kept_pct": [round(100 * n_kept / max(n_total, 1), 2)],
    })

    return (
        X.loc[keep_mask].copy(),
        y.loc[keep_mask].copy(),
        CensoringCorrection(
            propensity_threshold=propensity_threshold,
            n_total=n_total,
            n_uncensored_kept=n_kept,
            propensity_summary=summary,
        ),
    )
