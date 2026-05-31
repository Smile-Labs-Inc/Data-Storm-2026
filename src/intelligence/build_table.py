"""Build the decision-ready Outlet Intelligence table.

Output (one row per Outlet_ID), written to Results/outlet_intelligence.csv:

  Identity / structure
    Outlet_ID, Outlet_Type, Outlet_Size, Cooler_Count, Latitude, Longitude
    dominant_distributor, province

  Demand baseline & potential
    observed_mean_monthly_liters   "normal" historical month (baseline)
    observed_max_monthly_liters    best historical month
    active_months                  # distinct months with sales
    predicted_potential_liters     final latent potential (Maximum_Monthly_Liters)
    headroom_liters                max(potential - normal baseline, 0)
    uplift_ratio                   potential / observed_max

  Economics
    bill_per_liter                 revenue per litre (LKR)
    baseline_revenue_lkr           normal monthly revenue at baseline volume

  Local market
    competitor_count_500m          # other outlets within 500 m (catchment density)
    competitive_intensity          competitors normalised to [0,1] across the panel

These columns are what the spend optimizer and the XAI layer consume.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "Datasets"
RESULTS = ROOT / "Results"

# Distributor-ID prefix -> province. Encoded as DIST_<PREFIX>_NN.
PROVINCE_BY_PREFIX: dict[str, str] = {
    "W": "Western",
    "C": "Central",
    "NW": "North-Western",
    "S": "Southern",
}

# Canonical Outlet_Type spellings (master data is intentionally "dirty").
_TYPE_CANONICAL = {
    "grocry": "Grocery",
    "grocery": "Grocery",
    "grocerry": "Grocery",
    "kade": "Kade",
    "kades": "Kade",
    "eatery": "Eatery",
    "eaterie": "Eatery",
    "eateries": "Eatery",
    "pharmacy": "Pharmacy",
    "pharmacies": "Pharmacy",
    "supermarket": "Supermarket",
    "super market": "Supermarket",
}

EARTH_RADIUS_M = 6_371_000.0

# Sri Lanka geographic bounds (used to validate / repair outlet coordinates).
LAT_RANGE = (5.5, 10.0)
LON_RANGE = (79.0, 82.5)


def province_of_distributor(distributor_id: str) -> str:
    """'DIST_NW_02' -> 'North-Western'. Unknown prefixes return 'Unknown'."""
    if not isinstance(distributor_id, str) or not distributor_id.startswith("DIST_"):
        return "Unknown"
    parts = distributor_id.split("_")
    if len(parts) < 3:
        return "Unknown"
    prefix = parts[1].upper()
    return PROVINCE_BY_PREFIX.get(prefix, "Unknown")


def _canonical_type(raw: object) -> str:
    if not isinstance(raw, str):
        return "Unknown"
    key = raw.strip().lower()
    return _TYPE_CANONICAL.get(key, raw.strip().title())


def _sanitize_coords(lat: pd.Series, lon: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Repair / null outlet coordinates to Sri Lanka bounds.

    The raw coordinate file carries system artifacts: (0, 0) null-island rows and
    rows where Latitude/Longitude are swapped (latitude ~80, a longitude value).
    We recover obvious swaps, then null anything still outside the country box so
    the map only plots real in-country points. Row count is preserved.
    """
    lat = pd.to_numeric(lat, errors="coerce")
    lon = pd.to_numeric(lon, errors="coerce")

    in_lat = lat.between(*LAT_RANGE)
    in_lon = lon.between(*LON_RANGE)
    # swapped: latitude falls in the longitude band and vice-versa
    swap = (~in_lat) & (~in_lon) & lat.between(*LON_RANGE) & lon.between(*LAT_RANGE)
    lat2 = lat.copy()
    lon2 = lon.copy()
    lat2[swap], lon2[swap] = lon[swap], lat[swap]

    valid = lat2.between(*LAT_RANGE) & lon2.between(*LON_RANGE)
    lat2 = lat2.where(valid, np.nan)
    lon2 = lon2.where(valid, np.nan)
    return lat2, lon2


def _competitor_counts(lat: np.ndarray, lon: np.ndarray, radius_m: float = 500.0) -> np.ndarray:
    """Number of *other* outlets within radius_m of each outlet (self excluded)."""
    try:
        from sklearn.neighbors import BallTree
    except Exception:  # pragma: no cover - sklearn optional
        return np.zeros(len(lat), dtype=float)

    valid = np.isfinite(lat) & np.isfinite(lon)
    counts = np.zeros(len(lat), dtype=float)
    if valid.sum() == 0:
        return counts
    coords = np.deg2rad(np.column_stack([lat[valid], lon[valid]]))
    tree = BallTree(coords, metric="haversine")
    within = tree.query_radius(coords, r=radius_m / EARTH_RADIUS_M, count_only=True)
    counts[valid] = np.maximum(within - 1, 0)  # exclude self
    return counts


def build_intelligence_table(
    datasets_dir: Path = DATASETS,
    predictions_path: Path | None = None,
    write_to: Path | None = None,
) -> pd.DataFrame:
    """Assemble the per-outlet intelligence table from raw CSVs + predictions."""
    datasets_dir = Path(datasets_dir)
    if predictions_path is None:
        predictions_path = _find_predictions(RESULTS)
    predictions_path = Path(predictions_path)

    master = pd.read_csv(datasets_dir / "outlet_master.csv")
    coords = pd.read_csv(datasets_dir / "outlet_coordinates.csv")
    txns = pd.read_csv(datasets_dir / "transactions_history_final.csv")
    preds = pd.read_csv(predictions_path)

    master["Outlet_Type"] = master["Outlet_Type"].map(_canonical_type)

    # --- monthly aggregates -> per-outlet demand & economics ---------------
    monthly = (
        txns.groupby(["Outlet_ID", "Year", "Month"], as_index=False)
        .agg(monthly_volume=("Volume_Liters", "sum"), monthly_bill=("Total_Bill_Value", "sum"))
    )
    demand = (
        monthly.groupby("Outlet_ID")
        .agg(
            observed_mean_monthly_liters=("monthly_volume", "mean"),
            observed_max_monthly_liters=("monthly_volume", "max"),
            active_months=("monthly_volume", "size"),
            total_volume=("monthly_volume", "sum"),
            total_bill=("monthly_bill", "sum"),
        )
        .reset_index()
    )
    demand["bill_per_liter"] = (
        demand["total_bill"] / demand["total_volume"].replace(0, np.nan)
    ).fillna(0.0)

    # dominant distributor = the one supplying the most volume to the outlet
    dist_vol = (
        txns.groupby(["Outlet_ID", "Distributor_ID"], as_index=False)["Volume_Liters"].sum()
    )
    dominant = (
        dist_vol.sort_values("Volume_Liters", ascending=False)
        .drop_duplicates("Outlet_ID")[["Outlet_ID", "Distributor_ID"]]
        .rename(columns={"Distributor_ID": "dominant_distributor"})
    )

    # --- predictions -------------------------------------------------------
    pred_col = "Maximum_Monthly_Liters"
    if pred_col not in preds.columns:
        # tolerate alternative naming
        cand = [c for c in preds.columns if c != "Outlet_ID"]
        pred_col = cand[0]
    preds = preds[["Outlet_ID", pred_col]].rename(
        columns={pred_col: "predicted_potential_liters"}
    )

    # --- assemble ----------------------------------------------------------
    df = (
        master.merge(coords, on="Outlet_ID", how="left")
        .merge(demand, on="Outlet_ID", how="left")
        .merge(dominant, on="Outlet_ID", how="left")
        .merge(preds, on="Outlet_ID", how="left")
    )

    df["Latitude"], df["Longitude"] = _sanitize_coords(df["Latitude"], df["Longitude"])
    df["province"] = df["dominant_distributor"].map(province_of_distributor)

    for c in [
        "observed_mean_monthly_liters",
        "observed_max_monthly_liters",
        "predicted_potential_liters",
        "bill_per_liter",
    ]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["active_months"] = pd.to_numeric(df["active_months"], errors="coerce").fillna(0).astype(int)

    # potential should never sit below the best observed month
    df["predicted_potential_liters"] = np.maximum(
        df["predicted_potential_liters"], df["observed_max_monthly_liters"]
    )
    # headroom over the *normal* (mean) month -- the realistic uplift opportunity
    df["headroom_liters"] = np.maximum(
        df["predicted_potential_liters"] - df["observed_mean_monthly_liters"], 0.0
    )
    df["uplift_ratio"] = (
        df["predicted_potential_liters"]
        / df["observed_max_monthly_liters"].replace(0, np.nan)
    ).fillna(1.0)
    df["baseline_revenue_lkr"] = df["observed_mean_monthly_liters"] * df["bill_per_liter"]

    # --- competitive catchment density ------------------------------------
    df["competitor_count_500m"] = _competitor_counts(
        df["Latitude"].to_numpy(dtype=float), df["Longitude"].to_numpy(dtype=float)
    )
    cmax = df["competitor_count_500m"].quantile(0.99)
    cmax = cmax if cmax and cmax > 0 else 1.0
    df["competitive_intensity"] = (df["competitor_count_500m"] / cmax).clip(0, 1)

    cols = [
        "Outlet_ID", "Outlet_Type", "Outlet_Size", "Cooler_Count",
        "Latitude", "Longitude", "dominant_distributor", "province",
        "observed_mean_monthly_liters", "observed_max_monthly_liters", "active_months",
        "predicted_potential_liters", "headroom_liters", "uplift_ratio",
        "bill_per_liter", "baseline_revenue_lkr",
        "competitor_count_500m", "competitive_intensity",
    ]
    df = df[cols].sort_values("Outlet_ID").reset_index(drop=True)

    if write_to is not None:
        write_to = Path(write_to)
        write_to.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(write_to, index=False)
    return df


def _find_predictions(results_dir: Path) -> Path:
    """Locate the latest *predictions.csv (Outlet_ID + Maximum_Monthly_Liters)."""
    results_dir = Path(results_dir)
    candidates = sorted(results_dir.glob("*predictions.csv"))
    if not candidates:
        raise FileNotFoundError(
            f"No *predictions.csv found in {results_dir}. Run the modeling pipeline first."
        )
    # prefer one that actually carries the canonical column
    for p in candidates:
        try:
            head = pd.read_csv(p, nrows=1)
        except Exception:
            continue
        if "Maximum_Monthly_Liters" in head.columns:
            return p
    return candidates[0]


def load_intelligence_table(
    path: Path | None = None, rebuild: bool = False
) -> pd.DataFrame:
    """Load the cached table, building it on first use (or when rebuild=True)."""
    path = Path(path) if path is not None else RESULTS / "outlet_intelligence.csv"
    if rebuild or not path.exists():
        return build_intelligence_table(write_to=path)
    return pd.read_csv(path)


if __name__ == "__main__":
    out = RESULTS / "outlet_intelligence.csv"
    table = build_intelligence_table(write_to=out)
    print(f"Wrote {len(table):,} outlets -> {out}")
    print(table["province"].value_counts().to_string())
