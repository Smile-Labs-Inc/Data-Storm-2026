"""Manski-style worst-case bounds for latent potential.

The target is NOT point-identified from observational data alone (no exogenous
variation in constraints). Per Manski (2003) "Partial Identification...", the
right thing to do is report a defensible interval:

    lower(i) = strongest observed evidence -- the robust historical max
              (this is what the outlet has DEMONSTRABLY achieved at least once)

    upper(i) = peer 99th-percentile demand frontier scaled by an empirically
              estimated maximum-uplift multiplier (from caps bootstrap).
              Anything above this would require unverifiable assumptions.

    point(i) = the modeler's best guess inside the interval.

The interval is the report-grade honest disclosure. The point estimate is what
goes in the submission CSV.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_MAX_UPLIFT = 6.0  # absolute ceiling on multiplier vs lower bound


def compute_manski_bands(
    predictions: pd.DataFrame,
    cap_table: pd.DataFrame | None = None,
    max_uplift: float = DEFAULT_MAX_UPLIFT,
) -> pd.DataFrame:
    """Returns Outlet_ID + manski_lower + point + manski_upper.

    `predictions` must have columns:
      Outlet_ID, Outlet_Type, Outlet_Size, lower_bound,
      Maximum_Monthly_Liters (the point estimate),
      observed_max_monthly_liters.
    """
    df = predictions.copy()
    # FIX N2 (council round 2): Manski floor for right-censored data is the
    # *observed maximum*, not the robust lower_bound. The strongest known truth
    # about latent demand is "the outlet has demonstrably hit observed_max
    # at least once". A lower_bound below that violates the trivial Manski floor.
    df["manski_lower"] = np.maximum(
        df["lower_bound"].fillna(0.0),
        df["observed_max_monthly_liters"].fillna(0.0),
    )

    peer_p99 = df.groupby(["Outlet_Type", "Outlet_Size"])[
        "observed_max_monthly_liters"
    ].transform(lambda s: s.quantile(0.99))

    if cap_table is not None:
        df = df.merge(
            cap_table[["Outlet_Type", "Outlet_Size", "cap_uplift"]],
            on=["Outlet_Type", "Outlet_Size"],
            how="left",
            suffixes=("", "_cap"),
        )
        cap = df["cap_uplift"].fillna(max_uplift)
    else:
        cap = pd.Series(max_uplift, index=df.index)

    upper_a = peer_p99.fillna(df["observed_max_monthly_liters"])
    upper_b = df["lower_bound"] * np.minimum(cap, max_uplift)
    df["manski_upper"] = np.maximum(upper_a, upper_b)

    df["point"] = df["Maximum_Monthly_Liters"]
    df["point"] = np.clip(df["point"], df["manski_lower"], df["manski_upper"])

    return df[["Outlet_ID", "manski_lower", "point", "manski_upper"]]
