"""Step 3: outlet x POI feature engineering.

For each outlet (with a valid Sri Lanka coordinate) and each POI category:
  - count within {250, 500, 1000, 2000} metres (4 columns)
  - Gaussian-decay weighted score (1 column)
  - distance to nearest POI in metres (1 column, default 2 * max_radius if none)
  - binary has_within_500m (1 column)

Plus a composite poi_catchment_score across all 9 categories.

Outlets with no valid coordinate get NaN for ALL POI features (NOT teleport).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    CATEGORIES,
    DATA_POIS,
    GAUSSIAN_SIGMA_URBAN_KM,
    GAUSSIAN_SIGMA_RURAL_KM,
    LAT_RANGE,
    LON_RANGE,
    OUTLET_COORDINATES_CSV,
    POI_FEATURES_PARQUET,
    RADII_M,
    URBAN_DENSITY_THRESHOLD,
    ensure_dirs,
)
from src.features import per_category_features
from src.spatial import build_balltree


def load_valid_coords() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(OUTLET_COORDINATES_CSV)
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    valid_mask = (
        df["Latitude"].between(*LAT_RANGE)
        & df["Longitude"].between(*LON_RANGE)
    )
    return df[valid_mask].reset_index(drop=True), df[~valid_mask].reset_index(drop=True)


def main() -> None:
    ensure_dirs()
    valid, invalid = load_valid_coords()
    print(f"[poi] outlets: {len(valid)} valid + {len(invalid)} invalid (NaN coords or out-of-bounds)")

    outlet_tree = build_balltree(valid["Latitude"].values, valid["Longitude"].values)

    feature_frames: list[pd.DataFrame] = [valid[["Outlet_ID"]].copy()]
    for cat_name in CATEGORIES.keys():
        path = DATA_POIS / f"{cat_name}.parquet"
        if not path.exists():
            print(f"[poi] WARN: {path} missing -- run 02_extract_pois.py first")
            continue

        pois = pd.read_parquet(path)
        if pois.empty:
            print(f"[poi]   {cat_name}: 0 POIs in PBF -- writing zero-fill features")
            zero_frame = _zero_frame(valid["Outlet_ID"], cat_name)
            feature_frames.append(zero_frame)
            continue

        t0 = time.time()
        feats = per_category_features(
            outlet_lat=valid["Latitude"].values,
            outlet_lon=valid["Longitude"].values,
            poi_lat=pois["Latitude"].values,
            poi_lon=pois["Longitude"].values,
            category=cat_name,
            radii_m=RADII_M,
            urban_sigma_km=GAUSSIAN_SIGMA_URBAN_KM,
            rural_sigma_km=GAUSSIAN_SIGMA_RURAL_KM,
            urban_density_threshold=URBAN_DENSITY_THRESHOLD,
            outlet_tree=outlet_tree,
        )
        feats.insert(0, "Outlet_ID", valid["Outlet_ID"].values)
        feature_frames.append(feats)
        print(f"[poi]   {cat_name}: {len(pois)} POIs, {feats.shape[1] - 1} features in {time.time() - t0:.1f}s")

    merged = feature_frames[0]
    for f in feature_frames[1:]:
        merged = merged.merge(f, on="Outlet_ID", how="left")

    if not invalid.empty:
        invalid_outlet_ids = invalid[["Outlet_ID"]].copy()
        for c in merged.columns:
            if c == "Outlet_ID":
                continue
            invalid_outlet_ids[c] = np.nan
        merged = pd.concat([merged, invalid_outlet_ids], ignore_index=True)

    merged["poi_catchment_score"] = _composite_score(merged)

    merged.to_parquet(POI_FEATURES_PARQUET, index=False)
    print(f"\n[poi] wrote {POI_FEATURES_PARQUET}  shape={merged.shape}")


def _zero_frame(outlet_ids: pd.Series, cat_name: str) -> pd.DataFrame:
    df = pd.DataFrame({"Outlet_ID": outlet_ids.values})
    for r in RADII_M:
        df[f"{cat_name}_count_{r}m"] = 0
    df[f"{cat_name}_decay_score"] = 0.0
    df[f"{cat_name}_dist_nearest_m"] = float(2 * max(RADII_M))
    df[f"{cat_name}_has_within_500m"] = 0
    return df


def _composite_score(df: pd.DataFrame) -> pd.Series:
    decay_cols = [c for c in df.columns if c.endswith("_decay_score")]
    if not decay_cols:
        return pd.Series(0.0, index=df.index)
    z = df[decay_cols].apply(lambda s: (s - s.mean()) / (s.std() or 1.0), axis=0)
    return z.mean(axis=1).fillna(0.0)


if __name__ == "__main__":
    main()
