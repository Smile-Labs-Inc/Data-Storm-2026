"""pyrosm wrapper: read the PBF once per category and return a flat DataFrame
with Latitude, Longitude, name, plus the matched OSM tags for traceability.

All POIs are returned with WGS84 (EPSG:4326) coordinates. For polygons (e.g.
hospital buildings, university campuses), we use the polygon centroid.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _flatten_geometry(gdf) -> pd.DataFrame:
    """Convert a GeoDataFrame to a flat DataFrame with Lat/Lon centroid columns."""
    if gdf is None or len(gdf) == 0:
        return pd.DataFrame(columns=["Latitude", "Longitude", "name"])

    gdf = gdf.copy()
    if gdf.geometry.crs is None:
        gdf = gdf.set_crs(epsg=4326, allow_override=True)
    elif gdf.geometry.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    centroid = gdf.geometry.centroid
    out = pd.DataFrame({
        "Latitude": centroid.y.values,
        "Longitude": centroid.x.values,
    })
    out["name"] = gdf.get("name", pd.Series([None] * len(gdf))).astype(object).values
    return out.dropna(subset=["Latitude", "Longitude"]).reset_index(drop=True)


def iter_category_pois(pbf_path: Path, tag_filter: dict[str, object]) -> pd.DataFrame:
    """Returns a flat DataFrame for one category. May call pyrosm multiple times if
    the filter combines multiple OSM keys.
    """
    from pyrosm import OSM

    osm = OSM(str(pbf_path))
    parts: list[pd.DataFrame] = []

    for key, value in tag_filter.items():
        custom_filter: dict[str, object]
        if value is True:
            custom_filter = {key: True}
        else:
            custom_filter = {key: list(value)}

        try:
            gdf = osm.get_pois(custom_filter=custom_filter)
        except Exception:
            gdf = None

        flat = _flatten_geometry(gdf)
        if not flat.empty:
            parts.append(flat)

    if not parts:
        return pd.DataFrame(columns=["Latitude", "Longitude", "name"])
    return pd.concat(parts, ignore_index=True).drop_duplicates().reset_index(drop=True)
