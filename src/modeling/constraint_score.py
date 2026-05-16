"""Constraint score in [0, 1] -- rebuilt per council fix M2.

Council Skeptic + Statistician independently flagged that the team's previous
rank-sum constraint score was a re-labelled "outlet bigness" indicator, with
10% weight on `valid_coordinate_rank` (a data-quality flag, NOT a demand signal).

This rebuild uses three orthogonal signals:
  1. **Frontier residual z-score** -- (peer_q90 - observed_max) / sd(peer)
     Bigger gap = more likely under-realising true demand.
  2. **Plateau gate** -- months_since_new_max + variance ratio of recent vs all
     history. Old, flat sales = constraint signal.
  3. **PCA-decorrelated capacity** -- combine cooler_count, sku_breadth,
     catchment density into one orthogonalised capacity component.

Composed via sigmoid into [0, 1]. No double-counting, no DQ flags.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def _peer_q90(features: pd.DataFrame) -> pd.Series:
    return features.groupby(["Outlet_Type", "Outlet_Size"])[
        "observed_max_monthly_liters"
    ].transform(lambda s: s.quantile(0.90))


def _peer_sd(features: pd.DataFrame) -> pd.Series:
    return features.groupby(["Outlet_Type", "Outlet_Size"])[
        "observed_max_monthly_liters"
    ].transform("std").fillna(1.0).replace(0, 1.0)


def _frontier_residual_z(features: pd.DataFrame) -> pd.Series:
    peer_q90 = _peer_q90(features)
    peer_sd = _peer_sd(features)
    z = (peer_q90 - features["observed_max_monthly_liters"]) / peer_sd
    return z.clip(lower=-3, upper=5)


def _plateau_signal(transactions: pd.DataFrame) -> pd.DataFrame:
    """Per outlet: months_since_new_max, recent variance ratio."""
    monthly = (
        transactions.groupby(["Outlet_ID", "Year", "Month"], as_index=False)
        .agg(monthly_volume=("Volume_Liters", "sum"))
        .sort_values(["Outlet_ID", "Year", "Month"])
    )

    rows: list[dict] = []
    for outlet, g in monthly.groupby("Outlet_ID", sort=False):
        vals = g["monthly_volume"].values
        n = len(vals)
        if n == 0:
            continue
        argmax = int(np.argmax(vals))
        months_since_max = n - 1 - argmax
        recent_n = min(12, n)
        recent_var = float(np.var(vals[-recent_n:])) if recent_n > 1 else 0.0
        all_var = float(np.var(vals)) if n > 1 else 1.0
        var_ratio = recent_var / max(all_var, 1e-6)
        plateau = float((months_since_max > 6) and (var_ratio < 0.4))
        rows.append({
            "Outlet_ID": outlet,
            "months_since_new_max": months_since_max,
            "recent_variance_ratio": var_ratio,
            "plateau_signal": plateau,
        })
    return pd.DataFrame(rows)


def _pca_capacity(features: pd.DataFrame, capacity_cols: list[str]) -> pd.Series:
    """First PC of capacity columns, scaled to z-score units."""
    X = features[capacity_cols].copy()
    X = X.fillna(X.median(numeric_only=True)).fillna(0.0)
    Xs = StandardScaler().fit_transform(X.values)
    pca = PCA(n_components=1, random_state=42)
    pc = pca.fit_transform(Xs).ravel()
    # orient so higher capacity -> larger value
    if pc[X.shape[0] // 2] < 0 and X.iloc[X.shape[0] // 2].sum() > X.values.mean():
        pc = -pc
    return pd.Series(pc, index=features.index, name="capacity_pc1")


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def build_constraint_score(
    features: pd.DataFrame,
    transactions: pd.DataFrame,
    capacity_cols: tuple[str, ...] = (
        "Cooler_Count",
        "sku_breadth",
        "catchment_density_score",
    ),
    weight_frontier: float = 0.5,
    weight_plateau: float = 0.3,
    weight_capacity: float = 0.2,
) -> pd.DataFrame:
    """Returns DataFrame with Outlet_ID + constraint_score (in [0,1]) + 3 signal cols."""
    df = features.copy().reset_index(drop=True)

    df["frontier_residual_z"] = _frontier_residual_z(df).fillna(0.0)

    plateau = _plateau_signal(transactions)
    df = df.merge(plateau, on="Outlet_ID", how="left")
    df["months_since_new_max"] = df["months_since_new_max"].fillna(0)
    df["recent_variance_ratio"] = df["recent_variance_ratio"].fillna(1.0)
    df["plateau_signal"] = df["plateau_signal"].fillna(0.0)

    available_cap_cols = [c for c in capacity_cols if c in df.columns]
    if available_cap_cols:
        df["capacity_pc1"] = _pca_capacity(df, available_cap_cols)
    else:
        df["capacity_pc1"] = 0.0

    z_frontier = (df["frontier_residual_z"] - df["frontier_residual_z"].mean()) / (
        df["frontier_residual_z"].std() or 1.0
    )
    z_plateau = df["plateau_signal"].astype(float) * 1.5  # +1.5 z if plateaued
    z_capacity_inv = -df["capacity_pc1"]  # low capacity = more constrained

    raw = (
        weight_frontier * z_frontier
        + weight_plateau * z_plateau
        + weight_capacity * z_capacity_inv
    )
    df["constraint_score"] = _sigmoid(raw.values)

    return df[
        [
            "Outlet_ID",
            "frontier_residual_z",
            "plateau_signal",
            "months_since_new_max",
            "recent_variance_ratio",
            "capacity_pc1",
            "constraint_score",
        ]
    ]
