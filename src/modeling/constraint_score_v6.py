"""Constraint score v6 — deterministic PCA sign anchor.

Replaces the fragile median-row heuristic in constraint_score.py:83-84 with
a Cooler_Count-anchored sign that is deterministic and reproducible across
all platforms and data orderings.

R2 O4 flagged the original heuristic as "essentially random".
R6 Modeling Diagnostician confirmed it's still fragile.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def _pca_capacity_v6(features: pd.DataFrame, capacity_cols: list[str]) -> pd.Series:
    """First PC of capacity columns, sign-anchored on Cooler_Count.

    Higher Cooler_Count = higher capacity = lower constraint.
    The PC sign is flipped if negatively correlated with Cooler_Count,
    guaranteeing deterministic orientation across all runs.
    """
    X = features[capacity_cols].copy()
    X = X.fillna(X.median(numeric_only=True)).fillna(0.0)
    Xs = StandardScaler().fit_transform(X.values)
    pca = PCA(n_components=1, random_state=42)
    pc = pca.fit_transform(Xs).ravel()

    if "Cooler_Count" in X.columns:
        anchor_corr = np.corrcoef(X["Cooler_Count"].fillna(0).values, pc)[0, 1]
        if anchor_corr < 0:
            pc = -pc

    return pd.Series(pc, index=features.index, name="capacity_pc1")


def build_constraint_score_v6(
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
    """Returns DataFrame with Outlet_ID + constraint_score_v6 (in [0,1]).

    Uses the deterministic PCA sign anchor from _pca_capacity_v6.
    Otherwise identical to build_constraint_score().
    """
    from .constraint_score import (
        _frontier_residual_z,
        _plateau_signal,
        _sigmoid,
    )

    df = features.copy().reset_index(drop=True)

    df["frontier_residual_z"] = _frontier_residual_z(df).fillna(0.0)

    plateau = _plateau_signal(transactions)
    df = df.merge(plateau, on="Outlet_ID", how="left")
    df["months_since_new_max"] = df["months_since_new_max"].fillna(0)
    df["recent_variance_ratio"] = df["recent_variance_ratio"].fillna(1.0)
    df["plateau_signal"] = df["plateau_signal"].fillna(0.0)

    available_cap_cols = [c for c in capacity_cols if c in df.columns]
    if available_cap_cols:
        df["capacity_pc1"] = _pca_capacity_v6(df, available_cap_cols)
    else:
        df["capacity_pc1"] = 0.0

    z_frontier = (df["frontier_residual_z"] - df["frontier_residual_z"].mean()) / (
        df["frontier_residual_z"].std() or 1.0
    )
    z_plateau = df["plateau_signal"].astype(float) * 1.5
    z_capacity_inv = -df["capacity_pc1"]

    raw = (
        weight_frontier * z_frontier
        + weight_plateau * z_plateau
        + weight_capacity * z_capacity_inv
    )
    df["constraint_score_v6"] = _sigmoid(raw.values)

    return df[
        [
            "Outlet_ID",
            "frontier_residual_z",
            "plateau_signal",
            "months_since_new_max",
            "recent_variance_ratio",
            "capacity_pc1",
            "constraint_score_v6",
        ]
    ]
