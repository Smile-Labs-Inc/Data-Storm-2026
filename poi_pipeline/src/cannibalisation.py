"""Cannibalisation: same-type / supermarket competition within tight radius."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .spatial import build_balltree, query_radius_counts


def supermarket_competition_count(
    outlet_lat: np.ndarray,
    outlet_lon: np.ndarray,
    supermarket_pois: pd.DataFrame,
    radius_m: int = 500,
) -> np.ndarray:
    if supermarket_pois.empty:
        return np.zeros(len(outlet_lat), dtype=int)
    tree = build_balltree(supermarket_pois["Latitude"].values, supermarket_pois["Longitude"].values)
    return query_radius_counts(tree, outlet_lat, outlet_lon, radius_m)
