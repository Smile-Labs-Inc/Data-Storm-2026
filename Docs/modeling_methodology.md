# Modeling Methodology

## Problem Framing

The challenge is not a standard supervised prediction problem because the target variable, true maximum outlet potential, is unobserved.

Observed historical volume is treated as a censored measurement:

```text
Observed Volume = min(True Consumer Demand, Operational Constraint Ceiling)
```

Therefore, the final output should not simply forecast historical sales. It should estimate an uncapped ceiling that is at least as high as demonstrated historical capability and higher where there is evidence that the outlet may have been constrained.

## Current Notebook

Primary implementation:

```text
Notebooks/01_latent_potential_pipeline.ipynb
```

The notebook runs the full local pipeline:

- Bronze ingestion.
- reusable data quality checks.
- Silver cleaning and rejected records.
- Gold feature engineering.
- baseline and frontier modeling.
- final prediction output.

## Data Forensics Used

The current pipeline catches and documents several system artifacts:

- misspelled outlet types such as `Grocry` and `Bakry`.
- lowercase outlet sizes such as `small`.
- missing outlet size values, standardized to `Unknown`.
- invalid Sri Lankan coordinates.
- negative transaction volume.
- negative bill value.

Rejected records are written to:

```text
data/silver_rejected/
```

The generated summary is written to:

```text
Docs/data_quality_report.md
```

## Feature Logic

The first modeling version uses internal data only.

Feature groups:

- outlet structure: outlet type, outlet size, cooler count.
- historical sales: mean, median, maximum, January maximum, recent three-month maximum.
- SKU and transaction breadth: SKU count and transaction line count.
- price or mix proxy: bill value per liter.
- distributor context: dominant distributor and January seasonality.
- calendar context: January holiday count.
- geospatial hygiene proxy: whether valid coordinates exist.
- geospatial catchment proxy: outlet density, same-type outlet density, same-distributor footprint, nearest outlet distance, and catchment density score.
- optional external POI proxy: POI totals within 1km and 2km plus `poi_demand_score` from OpenStreetMap enrichment.

## Latent Potential Logic

The current method uses a conservative lower bound and an uncapping frontier.

### 1. Lower Bound

The lower bound is the strongest observed evidence of what the outlet can already achieve:

```text
lower_bound = max(
  historical_max_monthly_liters,
  january_max_liters,
  recent_3_month_max_liters
)
```

The final prediction is never allowed to fall below this lower bound.

### 2. Observed Baseline Model

A gradient boosting model estimates normal observed monthly liters from outlet and historical features.

Purpose:

- learn the central tendency of observed behavior.
- support diagnostics.
- avoid relying only on raw historical averages.

### 3. Demand Frontier Model

A 90th percentile quantile gradient boosting model estimates the high-performing frontier of comparable outlet-month behavior.

Purpose:

- represent what strong comparable outlets can achieve.
- provide evidence for an uncapped ceiling.

### 4. Peer Frontier

The final ceiling uses comparable peer performance:

- 90th percentile historical maximum by outlet type and size.
- 85th percentile fallback by outlet type.
- 85th percentile fallback by outlet size.
- model-estimated 90th percentile demand frontier.

This creates a frontier using high-performing but comparable outlets.

### 5. Constraint Score

The constraint score estimates how likely an outlet is to be under-realizing its demand.

Signals:

- structural capacity score.
- cooler count.
- SKU breadth.
- catchment density score.
- optional POI demand score.
- coordinate availability.
- gap between demand proxy rank and observed performance rank.
- low volatility or plateau behavior.

The score ranges from 0 to 1.

### 6. Final Potential Formula

The prediction moves from the lower bound toward the peer frontier based on the constraint score:

```text
frontier_gap = max(peer_frontier - lower_bound, 0)
uncap_weight = constraint_score ^ 1.25
raw_potential = lower_bound + uncap_weight * frontier_gap
```

Then guardrails are applied:

- prediction cannot be below the lower bound.
- prediction cannot exceed a peer-group 98th percentile soft cap.
- prediction cannot exceed a size-based uplift cap.

Current maximum uplift caps:

| Outlet Size | Maximum Uplift Ratio |
| ----------- | -------------------: |
| Unknown     |                 2.0x |
| Small       |                 3.0x |
| Medium      |                 3.5x |
| Large       |                 4.0x |
| Extra Large |                 4.5x |

## Current Result Assessment

The latest generated output is structurally valid:

- 20,000 prediction rows in the full business output.
- 914 rows in the platform upload file when no official template is available.
- unique outlet IDs in the `row_id` column.
- no missing predictions.
- no negative predictions.

The output is now meaningfully uncapped:

- median uplift vs historical maximum is about 1.20x.
- average uplift vs historical maximum is about 1.37x.
- maximum uplift is below 3.0x.

This is more defensible than a pure historical maximum baseline because it estimates latent upside, while still using guardrails to avoid unrealistic jumps.

## Implemented Catchment Enrichment

The model now includes internal geospatial catchment features derived from outlet coordinates:

- nearby outlet counts within 1 km, 2 km, and 5 km.
- same-type outlet count within 2 km.
- same-distributor outlet count within 5 km.
- nearest outlet distance.
- catchment density score.

These features help distinguish low-selling outlets in dense trade catchments from low-selling outlets in sparse catchments.

## Implemented POI Enrichment

The solution now includes an OpenStreetMap POI enrichment notebook:

```text
Notebooks/03_poi_enrichment.ipynb
```

The latest run enriched 902 valid-coordinate outlets from the 914-row platform fallback file and parsed 9,581 POIs from Overpass.

The main model uses three POI summary features when available:

- `poi_total_count_1km`
- `poi_total_count_2km`
- `poi_demand_score`

The POI demand score is included in the constraint score so dense external-footfall areas can increase the probability that an outlet is under-realizing latent demand.

## Known Limitation

The current implementation uses POI features for the current 914-row platform fallback. Once the official template is available, rerun the POI notebook so the exact official `row_id`s receive POI features.

Recommended next step:

- use OpenStreetMap or another allowed source to collect POIs around each outlet.
- create POI counts and nearest-distance features.
- add those features to the Gold table.
- include POI density in the constraint score and frontier model.

## Submission Template Note

The written challenge brief says to submit predictions for all outlets, but the platform validator expects 914 rows with a `row_id` column. The notebook therefore writes two files:

- `Results/smile_labs_predictions_full_20000.csv` for the full all-outlet business deliverable.
- `Results/smile_labs_predictions.csv` for the platform upload.

If the official 914-row template is available, place it in `Datasets/` as `sample_submission.csv`, `submission_template.csv`, or `test.csv` and rerun the notebook. The platform upload file will then be filtered to the exact official `row_id`s.
