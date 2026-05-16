"""osmium-based PBF reader: replaces pyrosm (broken on Python 3.13).

Reads the PBF once per category and returns a flat DataFrame with
Latitude, Longitude, name columns. Polygon/closed-way centroids are
computed as the mean of member node coordinates.
"""

from __future__ import annotations

from pathlib import Path

import osmium
import pandas as pd


def iter_category_pois(pbf_path: Path, tag_filter: dict[str, object]) -> pd.DataFrame:
    """Return a flat DataFrame of POIs matching tag_filter from pbf_path.

    tag_filter: dict mapping OSM key -> True (any value) or list[str] of accepted values.
    """

    class _Handler(osmium.SimpleHandler):
        def __init__(self, filter_dict: dict[str, object]) -> None:
            super().__init__()
            self._filter = filter_dict
            self.rows: list[dict] = []

        def _matches(self, tags) -> bool:
            for k, v in self._filter.items():
                if k in tags:
                    if v is True or tags[k] in v:
                        return True
            return False

        def node(self, n) -> None:
            if self._matches(n.tags) and n.location.valid():
                self.rows.append({
                    "Latitude": n.location.lat,
                    "Longitude": n.location.lon,
                    "name": n.tags.get("name"),
                })

        def way(self, w) -> None:
            if not self._matches(w.tags):
                return
            lats, lons = [], []
            for nd in w.nodes:
                if nd.location.valid():
                    lats.append(nd.location.lat)
                    lons.append(nd.location.lon)
            if lats:
                self.rows.append({
                    "Latitude": sum(lats) / len(lats),
                    "Longitude": sum(lons) / len(lons),
                    "name": w.tags.get("name"),
                })

    h = _Handler(tag_filter)
    h.apply_file(str(pbf_path), locations=True)

    if not h.rows:
        return pd.DataFrame(columns=["Latitude", "Longitude", "name"])
    return (
        pd.DataFrame(h.rows)
        .dropna(subset=["Latitude", "Longitude"])
        .drop_duplicates(subset=["Latitude", "Longitude"])
        .reset_index(drop=True)
    )
