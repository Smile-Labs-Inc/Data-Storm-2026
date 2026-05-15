# Folder Structure

This repository is organized around a simple local lakehouse workflow for the Data Storm 2026 latent outlet potential challenge.

## Top-Level Layout

```text
Data-Storm-2026/
  Datasets/
  data/
  Docs/
  Notebooks/
  Problem_Statement/
  Results/
  src/
  README.md
```

## Directory Responsibilities

| Path | Purpose |
| --- | --- |
| `Datasets/` | Original challenge-provided files. These should remain unchanged. |
| `data/` | Local pipeline outputs arranged by lakehouse layer. |
| `Docs/` | Planning, methodology, reporting notes, and submission documentation. |
| `Notebooks/` | Primary implementation notebooks for ingestion, cleaning, feature engineering, modeling, and experiments. |
| `Problem_Statement/` | Official challenge statement files. |
| `Results/` | Final submission outputs, including the prediction CSV. |
| `src/` | Reserved folders for future reusable production scripts. The current implementation is notebook-first. |

## Lakehouse Data Layers

### `data/bronze/`

Bronze stores raw ingested copies of the source files.

Rules:

- Preserve source files exactly as provided.
- Do not rename columns, clean values, deduplicate records, or filter rows.
- Add only ingestion metadata when written separately, such as row count, checksum, source file name, and ingestion timestamp.

Expected examples:

- `outlet_master.csv`
- `outlet_coordinates.csv`
- `transactions_history_final.csv`
- `distributor_seasonality_details.csv`
- `holiday_list.csv`

### `data/silver/`

Silver stores cleaned and validated datasets.

Rules:

- Apply reusable data quality checks.
- Standardize formats and categories.
- Keep only records that pass required checks.
- Write rejected records separately instead of silently dropping them.

Expected examples:

- cleaned outlet master data
- cleaned outlet coordinates
- cleaned transaction history
- cleaned distributor seasonality
- cleaned holiday calendar

### `data/silver_rejected/`

This folder stores records that fail Silver-layer checks.

Each rejected output should include:

- `dataset_name`
- `failed_check`
- `failure_reason`
- the original row values

This folder is important because data engineering and forensics make up a large share of the judging criteria.

### `data/gold/`

Gold stores model-ready and enriched datasets.

Rules:

- Join Silver datasets.
- Add outlet-level features.
- Add external POI and catchment features where available.
- Create final modeling tables and prediction-ready inputs.

Expected examples:

- outlet-level historical sales features
- POI density features
- January 2026 modeling matrix
- final feature table used for prediction

## Notebook Layout

### `Notebooks/01_latent_potential_pipeline.ipynb`

Primary end-to-end implementation notebook.

It runs:

- Bronze ingestion.
- reusable data quality checks.
- Silver cleaning and rejected record creation.
- data quality report generation.
- Gold feature engineering.
- latent potential modeling.
- final prediction CSV generation.

## Reserved Source Code Layout

### `src/ingestion/`

Reserved for future code that copies raw files from `Datasets/` into `data/bronze/` and records ingestion metadata.

### `src/quality/`

Reserved for future reusable, parameterized data quality checks.

Examples:

- duplicate checks
- null checks
- range checks
- referential integrity checks
- type and format checks
- categorical domain checks

### `src/cleaning/`

Reserved for future dataset-specific cleaning logic that converts Bronze data into Silver data.

Examples:

- fix outlet type spelling
- validate latitude and longitude
- standardize dates
- validate distributor IDs

### `src/features/`

Reserved for future feature engineering logic that converts Silver data into Gold modeling tables.

Examples:

- historical volume aggregates
- SKU diversity
- bill value per liter
- rolling sales features
- holiday counts
- seasonality scores

### `src/poi/`

Reserved for future external point-of-interest acquisition and geospatial mapping code.

Examples:

- Overpass API query builders
- POI category definitions
- distance-to-nearest-POI features
- POI counts within outlet catchment radii

### `src/modeling/`

Reserved for future model training, latent potential estimation, frontier logic, and prediction generation.

Examples:

- observed baseline model
- constraint score
- peer frontier model
- final potential blending logic

### `src/reporting/`

Reserved for future code that creates data quality summaries, model diagnostics, and report-ready tables.

## Version Control Notes

The `.gitkeep` files exist only so Git can track empty folders.

Generated data files under `data/` are ignored by default because they can be recreated by running the pipeline. Final deliverables that should be submitted belong in `Results/`.
