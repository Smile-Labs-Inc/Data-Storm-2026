"""Silver layer: normalise text artifacts, dedup holidays, score seasonality.

The team's EDA flagged the following SFA / ERP system artifacts that this module
neutralises:
  - misspelled outlet types: `Grocry` -> `Grocery`, `Bakry` -> `Bakery`
  - lowercase outlet sizes: `small` -> `Small`
  - missing outlet sizes -> `Unknown`
  - 240 outlet coordinates outside Sri Lanka -> dropped to silver_rejected
  - 9606 transactions with non-positive volume or bill -> dropped to silver_rejected
  - 93 holiday rows that are exact duplicates -> dedup
  - distributor seasonality labels {Favorable, Moderate, Un-Favorable} -> ordered
    numeric scores
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

OUTLET_TYPE_FIX = {
    "Grocry": "Grocery",
    "Bakry": "Bakery",
}

OUTLET_SIZE_FIX = {
    "small": "Small",
    "medium": "Medium",
    "large": "Large",
    "extra large": "Extra Large",
    "extralarge": "Extra Large",
    "extra-large": "Extra Large",
}

SEASONALITY_SCORE = {
    "Favorable": 1.0,
    "Moderate": 0.0,
    "Un-Favorable": -1.0,
    "Unfavorable": -1.0,
    "Un Favorable": -1.0,
}


def normalize_outlet_master(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "Outlet_Type" in out.columns:
        out["Outlet_Type"] = (
            out["Outlet_Type"].astype(str).str.strip().replace(OUTLET_TYPE_FIX)
        )
    if "Outlet_Size" in out.columns:
        out["Outlet_Size"] = (
            out["Outlet_Size"].astype(str).str.strip().str.lower()
        )
        out["Outlet_Size"] = out["Outlet_Size"].map(OUTLET_SIZE_FIX).fillna(
            out["Outlet_Size"].str.title()
        )
        out.loc[out["Outlet_Size"].isna() | (out["Outlet_Size"] == "Nan"), "Outlet_Size"] = "Unknown"
    if "Cooler_Count" in out.columns:
        out["Cooler_Count"] = pd.to_numeric(out["Cooler_Count"], errors="coerce").fillna(0).astype(int)
    return out


def clean_outlet_coordinates(
    df: pd.DataFrame,
    lat_range: tuple[float, float] = (5.5, 10.0),
    lon_range: tuple[float, float] = (79.0, 82.5),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (valid, rejected). Sri Lanka bounds applied; ambiguous coords go to rejected."""
    out = df.copy()
    out["Latitude"] = pd.to_numeric(out["Latitude"], errors="coerce")
    out["Longitude"] = pd.to_numeric(out["Longitude"], errors="coerce")
    lat = out["Latitude"]
    lon = out["Longitude"]
    valid_mask = (
        lat.between(*lat_range)
        & lon.between(*lon_range)
        & lat.notna()
        & lon.notna()
    )
    rejected = out.loc[~valid_mask].copy()
    rejected["failure_reason"] = "coordinate outside Sri Lanka bounds or null"
    valid = out.loc[valid_mask].copy()
    return valid, rejected


def clean_transactions(
    df: pd.DataFrame,
    valid_outlet_ids: set[str] | None = None,
    valid_distributor_ids: set[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = df.copy()
    out["Volume_Liters"] = pd.to_numeric(out["Volume_Liters"], errors="coerce")
    out["Total_Bill_Value"] = pd.to_numeric(out["Total_Bill_Value"], errors="coerce")
    out["Year"] = pd.to_numeric(out["Year"], errors="coerce").astype("Int64")
    out["Month"] = pd.to_numeric(out["Month"], errors="coerce").astype("Int64")

    reasons: list[str] = []

    def reason_for(mask: pd.Series, text: str) -> None:
        if mask.any():
            reasons.append(text)

    invalid_volume = (out["Volume_Liters"] <= 0) | out["Volume_Liters"].isna()
    invalid_bill = (out["Total_Bill_Value"] <= 0) | out["Total_Bill_Value"].isna()
    invalid_year = (~out["Year"].between(2023, 2026)).fillna(True)
    invalid_month = (~out["Month"].between(1, 12)).fillna(True)

    rejected_mask = invalid_volume | invalid_bill | invalid_year | invalid_month

    if valid_outlet_ids is not None:
        bad_outlet = ~out["Outlet_ID"].isin(valid_outlet_ids)
        rejected_mask = rejected_mask | bad_outlet
        reason_for(bad_outlet, "Outlet_ID not in outlet_master")

    if valid_distributor_ids is not None:
        bad_dist = ~out["Distributor_ID"].isin(valid_distributor_ids)
        rejected_mask = rejected_mask | bad_dist
        reason_for(bad_dist, "Distributor_ID outside allowed set")

    rejected = out.loc[rejected_mask].copy()
    rejected["failure_reason"] = "non-positive volume/bill or invalid year/month/foreign-key"
    valid = out.loc[~rejected_mask].copy()

    valid = valid.dropna(subset=["Year", "Month"])
    valid["Year"] = valid["Year"].astype("int64")
    valid["Month"] = valid["Month"].astype("int64")
    valid["YearMonth"] = pd.to_datetime(
        dict(year=valid["Year"], month=valid["Month"], day=1)
    )

    return valid, rejected


def dedupe_holidays(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce", utc=True).dt.tz_localize(None)
    dups_mask = out.duplicated(subset=["Date", "Holiday_Name", "Holiday_Type"], keep="first")
    rejected = out.loc[dups_mask].copy()
    rejected["failure_reason"] = "duplicate date+name+type holiday row"
    deduped = out.loc[~dups_mask].copy()
    deduped["Year"] = deduped["Date"].dt.year
    deduped["Month"] = deduped["Date"].dt.month
    return deduped, rejected


def score_seasonality(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Seasonality_Score"] = out["Seasonality_Index"].map(SEASONALITY_SCORE).fillna(0.0)
    return out


def write_silver(
    valid: pd.DataFrame,
    name: str,
    silver_dir: Path | str,
    rejected_dir: Path | str | None = None,
    rejected: pd.DataFrame | None = None,
) -> tuple[Path, Path | None]:
    silver_dir = Path(silver_dir)
    silver_dir.mkdir(parents=True, exist_ok=True)
    silver_path = silver_dir / f"{name}.parquet"
    valid.to_parquet(silver_path, index=False)

    rejected_path: Path | None = None
    if rejected is not None and rejected_dir is not None and len(rejected):
        rejected_dir = Path(rejected_dir)
        rejected_dir.mkdir(parents=True, exist_ok=True)
        rejected_path = rejected_dir / f"{name}_rejected.csv"
        rejected.to_csv(rejected_path, index=False)
    return silver_path, rejected_path
