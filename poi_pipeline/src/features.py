"""Per-category POI feature engineering."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .spatial import (
    EARTH_RADIUS_M,
    build_balltree,
    query_nearest_distance,
    query_radius_counts,
    query_radius_indices,
    to_radians,
)


def gaussian_decay_score(distances_m: np.ndarray, sigma_km: float) -> float:
    if len(distances_m) == 0:
        return 0.0
    sigma_m = sigma_km * 1000.0
    weights = np.exp(-0.5 * (distances_m / sigma_m) ** 2)
    return float(np.sum(weights))


def per_category_features(
    outlet_lat: np.ndarray,
    outlet_lon: np.ndarray,
    poi_lat: np.ndarray,
    poi_lon: np.ndarray,
    category: str,
    radii_m: tuple[int, ...],
    urban_sigma_km: float,
    rural_sigma_km: float,
    urban_density_threshold: int,
    outlet_tree=None,
) -> pd.DataFrame:
    n = len(outlet_lat)
    cols: dict[str, np.ndarray] = {}

    if len(poi_lat) == 0:
        for r in radii_m:
            cols[f"{category}_count_{r}m"] = np.zeros(n, dtype=int)
        cols[f"{category}_decay_score"] = np.zeros(n, dtype=float)
        cols[f"{category}_dist_nearest_m"] = np.full(n, float(2 * max(radii_m)))
        cols[f"{category}_has_within_500m"] = np.zeros(n, dtype=int)
        return pd.DataFrame(cols)

    poi_tree = build_balltree(poi_lat, poi_lon)

    for r in radii_m:
        cols[f"{category}_count_{r}m"] = query_radius_counts(poi_tree, outlet_lat, outlet_lon, r)
    cols[f"{category}_dist_nearest_m"] = query_nearest_distance(poi_tree, outlet_lat, outlet_lon)
    cols[f"{category}_has_within_500m"] = (cols[f"{category}_count_500m"] > 0).astype(int)

    if outlet_tree is not None:
        urban_counts = query_radius_counts(outlet_tree, outlet_lat, outlet_lon, 1000)
        sigmas_km = np.where(urban_counts >= urban_density_threshold, urban_sigma_km, rural_sigma_km)
    else:
        sigmas_km = np.full(n, rural_sigma_km)

    big_radius_m = max(2000, max(radii_m))
    poi_idx_per_outlet = query_radius_indices(poi_tree, outlet_lat, outlet_lon, big_radius_m)
    poi_rad = to_radians(poi_lat, poi_lon)
    outlet_rad = to_radians(outlet_lat, outlet_lon)

    decay_scores = np.zeros(n, dtype=float)
    for i, idxs in enumerate(poi_idx_per_outlet):
        if len(idxs) == 0:
            continue
        diff = poi_rad[idxs] - outlet_rad[i]
        # haversine -> approximate distance in meters
        a = np.sin(diff[:, 0] / 2.0) ** 2 + np.cos(outlet_rad[i, 0]) * np.cos(poi_rad[idxs, 0]) * np.sin(diff[:, 1] / 2.0) ** 2
        d_m = 2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
        decay_scores[i] = gaussian_decay_score(d_m, sigmas_km[i])
    cols[f"{category}_decay_score"] = decay_scores

    return pd.DataFrame(cols)
