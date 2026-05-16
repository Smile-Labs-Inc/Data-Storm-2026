"""Robust lower bound for latent potential.

Council fix M3: the team's `max(historical_max, january_max, recent_3mo_max)`
is dominated by `historical_max` and is fragile to one-month spikes (a single
festival or data error becomes the permanent floor).

This replacement:
  1. Sorts the outlet's monthly volumes high-to-low.
  2. Default lower_bound = the 3rd-highest month -- robust to single-month spikes
     while still using strong evidence.
  3. If the outlet has fewer than 6 active months: fall back to its
     own 95th-percentile.
  4. Always >= the outlet's median.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MIN_ACTIVE_MONTHS_FOR_3RD_HIGHEST = 6


def _per_outlet_monthly_series(transactions: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        transactions.groupby(["Outlet_ID", "Year", "Month"], as_index=False)
        .agg(monthly_volume=("Volume_Liters", "sum"))
    )
    return monthly


def robust_lower_bound(
    transactions: pd.DataFrame,
    min_active_months: int = MIN_ACTIVE_MONTHS_FOR_3RD_HIGHEST,
) -> pd.DataFrame:
    """Returns DataFrame with columns Outlet_ID + lower_bound."""
    monthly = _per_outlet_monthly_series(transactions)

    def per_outlet(s: pd.Series) -> float:
        sorted_vals = np.sort(s.values)[::-1]
        n = len(sorted_vals)
        if n == 0:
            return 0.0
        if n >= 3 and n >= min_active_months:
            third_highest = float(sorted_vals[2])
            median_floor = float(np.median(sorted_vals))
            return max(third_highest, median_floor)
        # too few months: use own p95, never below the median
        p95 = float(np.quantile(sorted_vals, 0.95))
        median_floor = float(np.median(sorted_vals))
        return max(p95, median_floor)

    out = (
        monthly.groupby("Outlet_ID")["monthly_volume"]
        .apply(per_outlet)
        .rename("lower_bound")
        .reset_index()
    )
    return out
