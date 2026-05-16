# POI Pipeline (separate folder by user request)

Builds external geospatial catchment features from OpenStreetMap (OSM) for all 19,760 outlets with valid Sri Lankan coordinates.

## Why a separate folder?

Per the team's design preference, the POI pipeline is isolated from the main `src/` modules so that:

- The PBF download + heavy spatial joins don't slow down imports.
- A POI re-fetch can be triggered independently.
- The PBF + per-category parquet caches are easy to gitignore.

## Approach (per `competition/research/04_osm_overpass_for_sri_lanka.md`)

We do NOT make 720,000 live Overpass calls. Instead:

1. Download the Geofabrik Sri Lanka country dump (`sri-lanka-latest.osm.pbf`, ~136 MB) once.
2. Parse it locally with `pyrosm` (single-pass, ~1 minute).
3. Per-outlet features via `sklearn.neighbors.BallTree(metric="haversine")` over POI coordinates.
4. Write to `output/poi_features.parquet` (~63 columns x 19,760 outlets).

Total wall-clock: 25-45 minutes end-to-end.

## How to run

```powershell
cd autokaggle/competition/poi_pipeline
python 01_download_pbf.py
python 02_extract_pois.py
python 03_build_features.py
python 04_quality_audit.py
```

Each script has a `CONFIG` block at the top -- edit there. No CLI flags.

## Outputs

| Path | Contents |
| --- | --- |
| `data/raw/sri-lanka-latest.osm.pbf` | downloaded PBF (gitignored) |
| `data/pois/<category>.parquet` | per-category extracted POIs |
| `output/poi_features.parquet` | final outlet x feature table |
| `output/poi_coverage_report.md` | honest LK coverage caveats for the 5-page PDF |

## Categories (9)

```
schools, transport_hubs, hospitals, restaurants, supermarkets,
religious_places, hotels, offices, banks
```

Per category we compute:

- count within 250m / 500m / 1km / 2km
- Gaussian-decay weighted score (sigma = 0.75 km urban, 2 km rural)
- distance to nearest (default `2 * max_radius` if no POI in range)
- binary `has_within_500m` flag

Plus a composite POI-driven catchment score.

## Sri Lanka coverage caveat (must go in PDF report)

Schools, hospitals, banks and hotels are well-mapped in OSM Sri Lanka. Small kades (corner shops) and independent grocers are sparsely mapped. We flag this honestly in `output/poi_coverage_report.md` and discuss in the methodology section.
