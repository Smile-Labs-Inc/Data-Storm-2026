"""Bootstrap-derived size x type uplift caps -- council fix.

Replaces the team's hardcoded {Small: 3.0, Medium: 3.5, Large: 4.0,
Extra Large: 4.5} multipliers with bucket-empirical 95th-percentile uplifts
from peer top-decile vs median behaviour. Defensible in the report, not magic.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def bootstrap_size_type_caps(
    features: pd.DataFrame,
    bucket_cols: tuple[str, ...] = ("Outlet_Type", "Outlet_Size"),
    cap_quantile: float = 0.95,
    min_bucket_n: int = 30,
    max_cap: float = 6.0,
    min_cap: float = 1.5,
) -> pd.DataFrame:
    """Returns one row per bucket with the empirical cap (uplift multiplier)."""
    df = features.copy()
    df["_uplift_proxy"] = (
        df["observed_max_monthly_liters"]
        / df["observed_median_monthly_liters"].replace(0, np.nan)
    )

    rows: list[dict] = []
    for keys, sub in df.groupby(list(bucket_cols)):
        if len(sub) < min_bucket_n:
            cap = float(np.nanquantile(df["_uplift_proxy"].dropna(), cap_quantile))
        else:
            cap = float(np.nanquantile(sub["_uplift_proxy"].dropna(), cap_quantile))
        cap = float(np.clip(cap, min_cap, max_cap))
        row: dict = {"cap_uplift": cap, "n_in_bucket": len(sub)}
        if isinstance(keys, tuple):
            for col, val in zip(bucket_cols, keys):
                row[col] = val
        else:
            row[bucket_cols[0]] = keys
        rows.append(row)

    return pd.DataFrame(rows)


def apply_caps(
    predictions: pd.DataFrame,
    cap_table: pd.DataFrame,
    bucket_cols: tuple[str, ...] = ("Outlet_Type", "Outlet_Size"),
    pred_col: str = "potential",
    historical_max_col: str = "observed_max_monthly_liters",
    out_col: str = "potential_capped",
) -> pd.DataFrame:
    """Caps predictions at `cap_uplift * historical_max` per bucket."""
    out = predictions.merge(cap_table, on=list(bucket_cols), how="left")
    out["cap_uplift"] = out["cap_uplift"].fillna(out["cap_uplift"].median() or 3.0)
    out[out_col] = np.minimum(
        out[pred_col].values,
        out["cap_uplift"].values * out[historical_max_col].values,
    )
    return out
