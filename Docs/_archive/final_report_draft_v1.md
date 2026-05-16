# Smil Labs - Data Storm 2026 Final Technical Report

## Cover

**Team:** Smil Labs  
**Challenge:** Latent Maximum Monthly Outlet Potential Estimation  
**Target Month:** January 2026  
**Final Platform Output:** `Results/smil_labs_predictions.csv`  
**Full Business Output:** `Results/smil_labs_predictions_full_20000.csv`

## 1. Problem Framing

The challenge is to estimate maximum monthly purchase potential for traditional trade outlets, not merely forecast observed sales. Historical volume is treated as censored demand:

```text
Observed Volume = min(True Consumer Demand, Operational Constraint Ceiling)
```

This means historical sales are a demonstrated lower bound, while latent potential must be inferred from outlet capacity, peer performance, geospatial catchment strength, POI footfall signals, and constraint evidence.

## 2. Lakehouse Pipeline and Data Hygiene

The solution follows a local Bronze, Silver, and Gold architecture.

| Layer | Implementation |
| --- | --- |
| Bronze | Raw source files are copied as-is into `data/bronze/` with ingestion audit metadata. |
| Silver | Reusable data quality checks clean and validate datasets. Failed rows are quarantined. |
| Gold | Clean data is joined into outlet-level modeling features, predictions, and diagnostics. |

Reusable checks include duplicate checks, mandatory null checks, referential integrity checks, numeric range checks, and categorical domain checks.

Main data forensics findings:

- 20,000 outlet records and 2,376,389 transaction rows.
- 196 missing outlet size values.
- 600 lowercase `small` outlet size values.
- 390 `Grocry` and 395 `Bakry` outlet-type artifacts.
- 240 coordinate rows outside plausible Sri Lankan bounds.
- 4,853 rows with non-positive volume and 4,753 rows with non-positive bill value.
- 9,606 rejected transaction records and 480 rejected coordinate records were stored in `data/silver_rejected/`.

## 3. EDA and Feature Engineering

EDA showed that all 20,000 outlets appear in transaction history across 36 months. The median outlet maximum observed monthly volume is 164.0 liters, while the 95th percentile is 1,307.9 liters. This large spread supports a peer-frontier methodology rather than an average-sales forecast.

Feature groups:

- outlet structure: size, type, cooler count.
- sales history: mean, median, max, January max, recent three-month max.
- SKU and transaction breadth.
- distributor seasonality and holiday counts.
- internal geospatial catchment features from outlet coordinates.
- external OpenStreetMap POI features from Overpass API.

Internal catchment features include nearby outlet counts within 1 km, 2 km, and 5 km, same-type outlet density, same-distributor footprint, nearest outlet distance, and a catchment density score.

POI enrichment was run for the current 914-row platform target set. It parsed 9,581 OpenStreetMap POIs and generated 902 valid-coordinate outlet-level POI feature rows. Targeted POI categories include education, transport, market/retail, healthcare, food service, office/finance, religious, and tourism/hotel locations.

## 4. Latent Potential Methodology

The model uses a guarded uncap framework.

First, the lower bound is the strongest observed outlet capability:

```text
lower_bound = max(historical_max, january_max, recent_3_month_max)
```

Second, gradient boosting estimates observed demand behavior, while a 90th-percentile quantile model estimates the demand frontier.

Third, peer frontiers are computed using high-performing comparable outlets by type and size.

Fourth, a constraint score blends:

- structural capacity rank.
- cooler count rank.
- SKU breadth rank.
- catchment density rank.
- POI demand score.
- coordinate availability.
- plateau behavior.

Final potential moves from the lower bound toward the peer frontier based on constraint strength:

```text
raw_potential = lower_bound + uncap_weight * max(peer_frontier - lower_bound, 0)
```

Guardrails ensure predictions are non-negative, never below demonstrated capability, and capped by outlet-size uplift limits and peer 98th percentile limits.

## 5. Validation, Outputs, and AI Transparency

Validation results:

| Metric | Value |
| --- | ---: |
| Platform output rows | 914 |
| Full output rows | 20,000 |
| Missing prediction values | 0 |
| Mean potential | 445.34 L |
| Median potential | 259.77 L |
| Mean uplift vs observed max | 1.36x |
| Median uplift vs observed max | 1.18x |
| Maximum uplift vs observed max | 2.97x |

The final platform file is `Results/smil_labs_predictions.csv` with columns `row_id` and `Maximum_Monthly_Liters`. A full 20,000-row business output is preserved as `Results/smil_labs_predictions_full_20000.csv`.

Generative AI was used as an engineering accelerator for documentation structure, data quality boilerplate, modeling alternatives, Overpass workflow design, debugging, validation summaries, and report drafting. All AI-assisted code and assumptions were validated through notebook execution, row-count checks, schema checks, rejected-record summaries, uplift diagnostics, and manual review artifacts.

Remaining caveat: the challenge brief asks for all outlets, but the platform validator expects 914 rows. The current platform file uses the 914-row fallback. If the official sample/test template becomes available, rerun `Notebooks/03_poi_enrichment.ipynb` and `Notebooks/01_latent_potential_pipeline.ipynb` to filter to the exact official `row_id`s.
