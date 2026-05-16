"""POI feature & extraction QA helpers."""

from __future__ import annotations

import pandas as pd


def audit_pois(pois: pd.DataFrame, category: str) -> dict:
    """Per-category extraction summary."""
    if pois.empty:
        return {"category": category, "n_pois": 0, "note": "0 POIs found in PBF"}
    note = ""
    if len(pois) < 50:
        note = "very low coverage"
    elif len(pois) < 500:
        note = "moderate coverage"
    else:
        note = "good coverage"
    return {"category": category, "n_pois": int(len(pois)), "note": note}


def audit_features(feats: pd.DataFrame) -> dict:
    """Outlet-side feature audit."""
    n_outlets = int(len(feats))
    feature_cols = [c for c in feats.columns if c != "Outlet_ID"]
    has_any_poi_2km_cols = [c for c in feature_cols if c.endswith("_count_2000m")]

    if has_any_poi_2km_cols:
        any_2km = feats[has_any_poi_2km_cols].fillna(0).sum(axis=1) > 0
        outlets_with_any_poi_2km_pct = float(any_2km.mean() * 100)
    else:
        outlets_with_any_poi_2km_pct = 0.0

    feats_only = feats[feature_cols]
    nan_per_outlet = feats_only.isna().any(axis=1)
    outlets_with_nan_features = int(nan_per_outlet.sum())
    outlets_with_valid_coords = int((~nan_per_outlet).sum())

    return {
        "n_outlets": n_outlets,
        "outlets_with_any_poi_2km_pct": outlets_with_any_poi_2km_pct,
        "outlets_with_valid_coords": outlets_with_valid_coords,
        "outlets_with_nan_features": outlets_with_nan_features,
    }
