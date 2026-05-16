"""Final latent-potential formula. Council fix M1: drop quadruple throttling.

Old chain (BAD):
    uncap_weight = constraint_score ** 1.25
    uncap_weight = uncap_weight.clip(0, 0.65)
    raw = lower_bound + uncap_weight * (frontier - lower_bound)
    raw = min(raw, peer_p98 * 1.35)
    raw = min(raw, lower_bound * size_cap)

  -> 4 layers of throttle, mechanically forces median uplift to ~1.20x.

New formula (clean):
    potential = lower_bound + constraint_score * (frontier - lower_bound)
    potential = min(potential, bootstrap_cap)            # ONE evidence-derived cap
    potential = max(potential, lower_bound)              # never below evidence
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .caps import apply_caps


def latent_potential(
    features: pd.DataFrame,
    constraint_scores: pd.DataFrame,
    lower_bounds: pd.DataFrame,
    frontier: pd.DataFrame,
    cap_table: pd.DataFrame,
) -> pd.DataFrame:
    """Combines all parts into one row-per-outlet potential table.

    Inputs:
      features: must contain Outlet_ID, Outlet_Type, Outlet_Size, observed_max_monthly_liters.
      constraint_scores: Outlet_ID + constraint_score in [0, 1].
      lower_bounds: Outlet_ID + lower_bound.
      frontier: Outlet_ID + frontier_q90.
      cap_table: from `bootstrap_size_type_caps`.

    Output: Outlet_ID + lower_bound + frontier_q90 + constraint_score +
            potential_raw + potential_capped + uplift_ratio.
    """
    df = (
        features[["Outlet_ID", "Outlet_Type", "Outlet_Size", "observed_max_monthly_liters"]]
        .merge(lower_bounds, on="Outlet_ID", how="left")
        .merge(frontier, on="Outlet_ID", how="left")
        .merge(constraint_scores[["Outlet_ID", "constraint_score"]], on="Outlet_ID", how="left")
    )

    df["lower_bound"] = df["lower_bound"].fillna(df["observed_max_monthly_liters"]).fillna(0.0)
    df["frontier_q90"] = df["frontier_q90"].fillna(df["lower_bound"])
    df["constraint_score"] = df["constraint_score"].fillna(0.0)

    gap = (df["frontier_q90"] - df["lower_bound"]).clip(lower=0)
    df["potential_raw"] = df["lower_bound"] + df["constraint_score"] * gap

    # FIX N1 (council round 2): floor at observed_max, not lower_bound.
    # Validation V3b requires `predicted >= historical_max` for >= 99% of outlets.
    # Lower_bound (3rd-highest month) is by definition <= observed_max, so flooring
    # at lower_bound would let predictions sneak below observed_max and fail V3b.
    historical_max = df["observed_max_monthly_liters"].fillna(df["lower_bound"])
    df["potential_raw"] = np.maximum(df["potential_raw"], historical_max)

    df_capped = apply_caps(
        df.rename(columns={"potential_raw": "potential"}),
        cap_table,
        bucket_cols=("Outlet_Type", "Outlet_Size"),
        pred_col="potential",
        historical_max_col="observed_max_monthly_liters",
        out_col="potential_capped",
    )

    df_capped["uplift_ratio"] = (
        df_capped["potential_capped"] / df_capped["observed_max_monthly_liters"].replace(0, np.nan)
    ).fillna(1.0)

    return df_capped[
        [
            "Outlet_ID",
            "Outlet_Type",
            "Outlet_Size",
            "observed_max_monthly_liters",
            "lower_bound",
            "frontier_q90",
            "constraint_score",
            "cap_uplift",
            "potential_capped",
            "uplift_ratio",
        ]
    ].rename(columns={"potential_capped": "Maximum_Monthly_Liters"})
