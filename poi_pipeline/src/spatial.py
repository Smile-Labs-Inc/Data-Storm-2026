"""BallTree haversine helpers."""

from __future__ import annotations

import numpy as np
from sklearn.neighbors import BallTree

EARTH_RADIUS_KM = 6371.0
EARTH_RADIUS_M = EARTH_RADIUS_KM * 1000


def to_radians(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    return np.deg2rad(np.column_stack([np.asarray(lat, dtype=float), np.asarray(lon, dtype=float)]))


def build_balltree(lat: np.ndarray, lon: np.ndarray) -> BallTree:
    rad = to_radians(lat, lon)
    return BallTree(rad, metric="haversine")


def query_radius_counts(tree: BallTree, query_lat: np.ndarray, query_lon: np.ndarray, radius_m: float) -> np.ndarray:
    rad = to_radians(query_lat, query_lon)
    radius_rad = radius_m / EARTH_RADIUS_M
    return tree.query_radius(rad, r=radius_rad, count_only=True)


def query_radius_indices(tree: BallTree, query_lat: np.ndarray, query_lon: np.ndarray, radius_m: float) -> list:
    rad = to_radians(query_lat, query_lon)
    radius_rad = radius_m / EARTH_RADIUS_M
    return tree.query_radius(rad, r=radius_rad, return_distance=False)


def query_nearest_distance(tree: BallTree, query_lat: np.ndarray, query_lon: np.ndarray) -> np.ndarray:
    """Returns nearest distance in METERS for each query point."""
    rad = to_radians(query_lat, query_lon)
    d, _ = tree.query(rad, k=1)
    return (d.ravel() * EARTH_RADIUS_M).astype(float)
