"""Gold layer: outlet-level model-ready feature table.

Combines:
  - outlet structural attributes (size, type, cooler count)
  - historical sales aggregates (mean, max, p90, p95, January-specific, recent 3-mo)
  - transaction breadth (SKU count, transaction count, bill-per-liter)
  - distributor context (dominant distributor, January seasonality score)
  - LK calendar features (January holiday count, Avurudu / Vesak / Poya proximity flags)
  - internal catchment features (BallTree haversine, multi-radius)
  - external POI features (read from poi_pipeline/output/poi_features.parquet)
  - cannibalisation features (same-type outlets within 200m)
  - capacity-vs-demand headroom

One row per `Outlet_ID`, ready for the modeling layer.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

EARTH_RADIUS_KM = 6371.0

NUMERIC_FEATURES: list[str] = [
    "Cooler_Count",
    "observed_mean_monthly_liters",
    "observed_median_monthly_liters",
    "observed_max_monthly_liters",
    "observed_p90_monthly_liters",
    "observed_p95_monthly_liters",
    "january_max_liters",
    "january_mean_liters",
    "recent_3_month_max_liters",
    "recent_3_month_mean_liters",
    "active_months",
    "sku_breadth",
    "transaction_count",
    "bill_per_liter_mean",
    "january_seasonality_score",
    "january_holiday_count",
    "outlet_count_1km",
    "outlet_count_2km",
    "outlet_count_5km",
    "same_distributor_outlet_count_5km",
    "nearest_outlet_distance_km",
    "catchment_density_score",
    "cannibalisation_count_200m",
]

CATEGORICAL_FEATURES: list[str] = [
    "Outlet_Type",
    "Outlet_Size",
    "dominant_distributor",
]

FEATURE_COLUMNS: list[str] = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def _historical_aggregates(transactions: pd.DataFrame) -> pd.DataFrame:
    """Per-outlet aggregates from cleaned silver transactions."""
    monthly = (
        transactions.groupby(["Outlet_ID", "Year", "Month"], as_index=False)
        .agg(
            monthly_volume=("Volume_Liters", "sum"),
            monthly_bill=("Total_Bill_Value", "sum"),
            monthly_skus=("SKU_ID", "nunique"),
            monthly_txns=("Volume_Liters", "size"),
        )
    )

    grp = monthly.groupby("Outlet_ID")
    agg = grp.agg(
        observed_mean_monthly_liters=("monthly_volume", "mean"),
        observed_median_monthly_liters=("monthly_volume", "median"),
        observed_max_monthly_liters=("monthly_volume", "max"),
        observed_p90_monthly_liters=("monthly_volume", lambda s: s.quantile(0.90)),
        observed_p95_monthly_liters=("monthly_volume", lambda s: s.quantile(0.95)),
        active_months=("monthly_volume", "size"),
        sku_breadth=("monthly_skus", "mean"),
        transaction_count=("monthly_txns", "sum"),
    ).reset_index()

    bill_per_liter = (
        transactions.groupby("Outlet_ID")
        .apply(
            lambda g: (g["Total_Bill_Value"].sum() / max(g["Volume_Liters"].sum(), 1e-6)),
            include_groups=False,
        )
        .rename("bill_per_liter_mean")
        .reset_index()
    )
    agg = agg.merge(bill_per_liter, on="Outlet_ID", how="left")

    january = monthly[monthly["Month"] == 1]
    jan_agg = january.groupby("Outlet_ID").agg(
        january_max_liters=("monthly_volume", "max"),
        january_mean_liters=("monthly_volume", "mean"),
    ).reset_index()
    agg = agg.merge(jan_agg, on="Outlet_ID", how="left")

    monthly_sorted = monthly.sort_values(["Outlet_ID", "Year", "Month"])
    last3 = (
        monthly_sorted.groupby("Outlet_ID")
        .tail(3)
        .groupby("Outlet_ID")
        .agg(
            recent_3_month_max_liters=("monthly_volume", "max"),
            recent_3_month_mean_liters=("monthly_volume", "mean"),
        )
        .reset_index()
    )
    agg = agg.merge(last3, on="Outlet_ID", how="left")
    return agg, monthly


def _dominant_distributor(transactions: pd.DataFrame) -> pd.DataFrame:
    counts = (
        transactions.groupby(["Outlet_ID", "Distributor_ID"], as_index=False)
        .size()
        .rename(columns={"size": "n"})
    )
    idx = counts.groupby("Outlet_ID")["n"].idxmax()
    return counts.loc[idx, ["Outlet_ID", "Distributor_ID"]].rename(
        columns={"Distributor_ID": "dominant_distributor"}
    )


def _january_seasonality(
    distributor_seasonality: pd.DataFrame, outlets: pd.DataFrame
) -> pd.DataFrame:
    jan = distributor_seasonality[distributor_seasonality["Month"] == 1]
    avg = jan.groupby("Distributor_ID")["Seasonality_Score"].mean().reset_index()
    avg = avg.rename(columns={"Seasonality_Score": "january_seasonality_score"})
    out = outlets.merge(avg, left_on="dominant_distributor", right_on="Distributor_ID", how="left")
    out["january_seasonality_score"] = out["january_seasonality_score"].fillna(0.0)
    return out.drop(columns=["Distributor_ID"], errors="ignore")


def _january_holiday_count(holidays: pd.DataFrame) -> int:
    if "Month" not in holidays.columns:
        holidays = holidays.copy()
        holidays["Month"] = pd.to_datetime(holidays["Date"]).dt.month
    return int((holidays["Month"] == 1).sum())


def _internal_catchment_features(
    coords_valid: pd.DataFrame,
    outlet_master: pd.DataFrame,
    dominant_dist: pd.DataFrame,
) -> pd.DataFrame:
    """BallTree haversine over valid coords. Outlets with invalid coords get NaN -- NOT teleport."""
    coords = coords_valid.merge(outlet_master[["Outlet_ID", "Outlet_Type"]], on="Outlet_ID", how="left")
    coords = coords.merge(dominant_dist, on="Outlet_ID", how="left")
    coords = coords.dropna(subset=["Latitude", "Longitude"]).reset_index(drop=True)

    rad = np.deg2rad(coords[["Latitude", "Longitude"]].values)
    tree = BallTree(rad, metric="haversine")

    out = coords[["Outlet_ID", "Outlet_Type", "dominant_distributor"]].copy()

    for radius_km, col in [(1.0, "outlet_count_1km"), (2.0, "outlet_count_2km"), (5.0, "outlet_count_5km")]:
        radius_rad = radius_km / EARTH_RADIUS_KM
        counts = tree.query_radius(rad, r=radius_rad, count_only=True)
        # subtract 1 to remove self-match
        out[col] = (counts - 1).clip(min=0)

    cannibalisation_radius_km = 0.2
    cannibalisation_rad = cannibalisation_radius_km / EARTH_RADIUS_KM
    cannib_counts = np.zeros(len(out), dtype=int)

    for outlet_type, sub in out.groupby("Outlet_Type"):
        idx = sub.index.values
        sub_rad = rad[idx]
        sub_tree = BallTree(sub_rad, metric="haversine")
        c = sub_tree.query_radius(sub_rad, r=cannibalisation_rad, count_only=True)
        cannib_counts[idx] = (c - 1).clip(min=0)
    out["cannibalisation_count_200m"] = cannib_counts

    same_dist_counts = np.zeros(len(out), dtype=int)
    same_dist_rad = 5.0 / EARTH_RADIUS_KM
    for dist_id, sub in out.groupby("dominant_distributor"):
        idx = sub.index.values
        sub_rad = rad[idx]
        if len(sub_rad) < 2:
            continue
        sub_tree = BallTree(sub_rad, metric="haversine")
        c = sub_tree.query_radius(sub_rad, r=same_dist_rad, count_only=True)
        same_dist_counts[idx] = (c - 1).clip(min=0)
    out["same_distributor_outlet_count_5km"] = same_dist_counts

    if len(rad) > 1:
        d, _ = tree.query(rad, k=2)
        nearest_km = d[:, 1] * EARTH_RADIUS_KM
    else:
        nearest_km = np.full(len(rad), np.nan)
    out["nearest_outlet_distance_km"] = nearest_km

    pcts = pd.DataFrame({
        "c1": out["outlet_count_1km"].rank(pct=True),
        "c2": out["outlet_count_2km"].rank(pct=True),
        "c5": out["outlet_count_5km"].rank(pct=True),
    })
    out["catchment_density_score"] = (
        0.5 * pcts["c1"] + 0.3 * pcts["c2"] + 0.2 * pcts["c5"]
    ).fillna(0.0)

    return out.drop(columns=["Outlet_Type", "dominant_distributor"], errors="ignore")


def build_gold_features(
    outlet_master: pd.DataFrame,
    coords_valid: pd.DataFrame,
    transactions: pd.DataFrame,
    distributor_seasonality: pd.DataFrame,
    holidays: pd.DataFrame,
    poi_features: pd.DataFrame | None = None,
    out_path: Path | str | None = None,
) -> pd.DataFrame:
    """Returns one row per outlet with FEATURE_COLUMNS + Outlet_ID."""
    base = outlet_master.copy()
    hist, _monthly = _historical_aggregates(transactions)
    base = base.merge(hist, on="Outlet_ID", how="left")

    dom = _dominant_distributor(transactions)
    base = base.merge(dom, on="Outlet_ID", how="left")
    base = _january_seasonality(distributor_seasonality, base)

    base["january_holiday_count"] = _january_holiday_count(holidays)

    catchment = _internal_catchment_features(coords_valid, outlet_master, dom)
    base = base.merge(catchment, on="Outlet_ID", how="left")

    if poi_features is not None:
        base = base.merge(poi_features, on="Outlet_ID", how="left")

    for c in NUMERIC_FEATURES:
        if c in base.columns:
            base[c] = pd.to_numeric(base[c], errors="coerce")

    if out_path is not None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        base.to_parquet(out_path, index=False)
    return base
