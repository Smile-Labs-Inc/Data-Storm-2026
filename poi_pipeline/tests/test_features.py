"""Smoke tests for the POI feature pipeline. Use a tiny synthetic input."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.features import per_category_features
from src.spatial import build_balltree, query_nearest_distance, query_radius_counts


def test_balltree_self_distance_zero() -> None:
    lat = np.array([7.0, 7.01, 7.02])
    lon = np.array([80.0, 80.01, 80.02])
    tree = build_balltree(lat, lon)
    d = query_nearest_distance(tree, lat, lon)
    assert d.shape == (3,)
    assert (d < 1.0).all(), f"self-distances should be ~0 m, got {d}"


def test_count_within_radius_includes_self() -> None:
    lat = np.array([7.0, 7.001, 7.5])  # first two are ~111m apart
    lon = np.array([80.0, 80.0, 80.0])
    tree = build_balltree(lat, lon)
    counts = query_radius_counts(tree, lat, lon, radius_m=500)
    assert counts[0] >= 2, f"first point should see itself + nearby = >=2, got {counts}"
    assert counts[2] == 1, f"isolated point sees only self, got {counts}"


def test_per_category_features_smoke() -> None:
    outlet_lat = np.array([7.0, 7.5, 8.0])
    outlet_lon = np.array([80.0, 80.0, 80.0])
    poi_lat = np.array([7.001, 7.002])
    poi_lon = np.array([80.0, 80.0])

    feats = per_category_features(
        outlet_lat=outlet_lat,
        outlet_lon=outlet_lon,
        poi_lat=poi_lat,
        poi_lon=poi_lon,
        category="schools",
        radii_m=(250, 500, 1000, 2000),
        urban_sigma_km=0.75,
        rural_sigma_km=2.0,
        urban_density_threshold=10,
    )
    assert "schools_count_500m" in feats.columns
    assert "schools_decay_score" in feats.columns
    assert "schools_dist_nearest_m" in feats.columns
    assert "schools_has_within_500m" in feats.columns
    assert len(feats) == 3
    # outlet 0 is right next to both POIs
    assert feats.loc[0, "schools_count_500m"] >= 2
    # outlet 2 is far away
    assert feats.loc[2, "schools_count_500m"] == 0


if __name__ == "__main__":
    test_balltree_self_distance_zero()
    test_count_within_radius_includes_self()
    test_per_category_features_smoke()
    print("OK: all POI smoke tests passed")
