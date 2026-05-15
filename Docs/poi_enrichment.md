# POI Enrichment

This document describes the external point-of-interest enrichment workflow implemented in `Notebooks/03_poi_enrichment.ipynb`.

## Purpose

The challenge asks teams to acquire external geospatial signals that explain outlet catchment demand. Internal outlet density is useful, but it does not directly identify the places that create footfall.

The POI enrichment notebook adds OpenStreetMap signals from the Overpass API.

## Target POI Categories

| Category | OSM Tags |
| --- | --- |
| `education` | schools, colleges, universities, kindergartens |
| `transport` | bus stops, bus stations, railway stations, railway halts |
| `market_retail` | supermarkets, convenience shops, malls, marketplaces |
| `healthcare` | hospitals, clinics, pharmacies |
| `food_service` | restaurants, cafes, fast food, bakeries |
| `office_finance` | banks, ATMs, company offices, government offices |
| `religious` | places of worship |
| `tourism_hotel` | hotels, guest houses, attractions, museums |

## How It Works

The notebook:

1. Selects target outlets from the official submission/template file if available.
2. Falls back to the current `Results/smil_labs_predictions.csv` row IDs.
3. Builds one bounding-box Overpass query for the target outlet area.
4. Caches the raw Overpass response in `data/bronze/poi_overpass_raw.json`.
5. Parses POIs into `data/gold/poi_cleaned.csv`.
6. Creates outlet-level POI features in `data/gold/outlet_poi_features.csv`.

## Output Features

For each POI category, the notebook creates:

- counts within 250m.
- counts within 500m.
- counts within 1km.
- counts within 2km.
- nearest POI distance in kilometers.

It also creates summary features:

- `poi_total_count_1km`
- `poi_total_count_2km`
- `poi_demand_score`

## Model Integration

`Notebooks/01_latent_potential_pipeline.ipynb` now automatically looks for:

```text
data/gold/outlet_poi_features.csv
```

If the file exists, the model uses:

- `poi_total_count_1km`
- `poi_total_count_2km`
- `poi_demand_score`

If the file does not exist, the model fills those features with zero so the pipeline remains reproducible.

## Recommended Run Order

1. Add the official 914-row submission/template file to `Datasets/` if available.
2. Run `Notebooks/03_poi_enrichment.ipynb`.
3. Run `Notebooks/01_latent_potential_pipeline.ipynb`.
4. Upload `Results/smil_labs_predictions.csv`.

## Notes

The Overpass API is a public service. Avoid repeated unnecessary calls. The notebook caches raw API output and reuses it by default.

## Latest Run

The notebook was run against the current 914-row platform fallback submission.

Run results:

- 902 target outlets had valid coordinates.
- 9,581 OpenStreetMap POIs were parsed.
- 902 outlet-level POI feature rows were created.
- `poi_total_count_1km`, `poi_total_count_2km`, and `poi_demand_score` were merged into the main model.

POI feature distribution:

| Metric | `poi_total_count_1km` | `poi_total_count_2km` | `poi_demand_score` |
| --- | ---: | ---: | ---: |
| Mean | 15.24 | 59.82 | 0.50 |
| Median | 3.00 | 22.00 | 0.51 |
| 90th percentile | 37.00 | 138.00 | 0.88 |
| Max | 336.00 | 1,064.00 | 1.00 |
