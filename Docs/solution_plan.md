# Solution Plan: Latent Outlet Potential Estimation

## Objective

Build a reproducible analytical pipeline to estimate the maximum monthly purchase potential, in liters, for each traditional trade outlet for January 2026.

The key challenge is that historical sales are censored. Observed volume is not equal to true demand; it is the lower value between consumer demand and operational constraints such as credit limits, delivery caps, stockouts, cooler limitations, or poor execution.

The solution must therefore estimate an uncapped latent ceiling, not simply forecast historical sales.

## Available Data

| Dataset | Expected Role |
| --- | --- |
| `Datasets/outlet_master.csv` | Outlet attributes such as size, cooler count, and outlet type. |
| `Datasets/outlet_coordinates.csv` | Outlet latitude and longitude for geospatial enrichment. |
| `Datasets/transactions_history_final.csv` | Historical outlet, distributor, SKU, month, volume, and bill value data. |
| `Datasets/distributor_seasonality_details.csv` | Distributor-level monthly seasonality signals. |
| `Datasets/holiday_list.csv` | Holiday calendar for month-level demand signals. |
| `Datasets/1. dataset_description.xlsx` | Data dictionary and field interpretation reference. |

## Target Output

Create a CSV file named `smil_labs_predictions.csv` with:

| Column | Description |
| --- | --- |
| `row_id` | Outlet identifier required by the submission validator. |
| `Maximum_Monthly_Liters` | Estimated uncapped purchase potential for January 2026. |

## Repository Structure

Use a clear lakehouse-style layout.

```text
Data-Storm-2026/
  Datasets/
    raw source files
  data/
    bronze/
    silver/
    silver_rejected/
    gold/
  src/
    ingestion/
    quality/
    cleaning/
    features/
    poi/
    modeling/
    reporting/
  Notebooks/
    01_eda.ipynb
    02_model_experiments.ipynb
  Docs/
    challenge_brief.md
    solution_plan.md
    ai_transparency_log.md
  Results/
    smil_labs_predictions.csv
```

## Phase 1: Bronze Layer

Ingest all source files exactly as provided.

Actions:

- Copy or read each file from `Datasets/` into `data/bronze/`.
- Preserve original columns, values, row counts, and file names.
- Store ingestion metadata such as source file name, ingestion timestamp, row count, and checksum.
- Do not clean, rename, deduplicate, or filter records in Bronze.

Expected output:

- One Bronze copy per raw dataset.
- A Bronze ingestion audit table.

## Phase 2: Reusable Data Quality Framework

Create reusable, parameterized checks that can run against any dataset.

Core checks:

| Check | Purpose |
| --- | --- |
| Duplicate check | Identify duplicate records using configurable primary keys. |
| Null check | Flag missing mandatory values. |
| Referential integrity check | Ensure foreign keys exist in reference tables. |
| Range check | Validate numeric values such as volume, bill value, latitude, longitude, and cooler count. |
| Type and format check | Validate dates, IDs, numeric columns, and categorical values. |
| Categorical domain check | Detect misspellings and unexpected outlet types, seasonality values, or distributor IDs. |
| Geospatial bounds check | Ensure coordinates fall within plausible Sri Lankan latitude and longitude ranges. |

Rejected record handling:

- Every failed record must be written to `data/silver_rejected/`.
- Each rejected record must include `dataset_name`, `failed_check`, `failure_reason`, and original row values.
- Records should not be silently dropped.

## Phase 3: Silver Layer

Clean and standardize the data after applying quality checks.

Dataset-specific cleaning:

- `outlet_master.csv`
  - Standardize `Outlet_Type` spelling, for example mapping `Grocry` to `Grocery`.
  - Validate `Outlet_Size` categories.
  - Validate `Cooler_Count` as a non-negative integer.

- `outlet_coordinates.csv`
  - Validate one coordinate pair per `Outlet_ID`.
  - Remove or quarantine impossible latitude and longitude values.
  - Check that every coordinate belongs to a known outlet.

- `transactions_history_final.csv`
  - Validate positive `Volume_Liters` and `Total_Bill_Value`.
  - Validate `Year` and `Month`.
  - Check `Outlet_ID` exists in outlet master.
  - Check `Distributor_ID` belongs to the 10 challenge distributors.
  - Create transaction date or month key.

- `distributor_seasonality_details.csv`
  - Validate distributor IDs, year, month, and seasonality labels.
  - Convert seasonality labels into ordered numeric scores.

- `holiday_list.csv`
  - Parse dates.
  - Create year-month holiday counts.
  - Separate public, religious, and other holiday types where useful.

Expected output:

- Cleaned Silver datasets.
- Rejected records with documented failure reasons.
- Data quality summary report.

## Phase 4: External POI Data Acquisition

Use external geospatial data to estimate local catchment demand around each outlet.

Recommended source options:

- OpenStreetMap through Overpass API.
- Geocoding or places APIs if allowed by competition rules.
- Public administrative or population-density datasets if available.

Target POI categories:

| Category | Demand Logic |
| --- | --- |
| Schools and universities | Student and commuter traffic. |
| Bus stops, railway stations, and transport hubs | High footfall and impulse purchase potential. |
| Markets and shopping areas | Retail density and consumer movement. |
| Offices and banks | Daytime working population. |
| Hospitals and clinics | Visitor and worker traffic. |
| Restaurants, cafes, bakeries, and eateries | Beverage consumption zones. |
| Supermarkets and groceries | Competitive and retail intensity. |
| Religious places | Event and gathering density. |
| Tourist sites and hotels | Visitor-driven consumption. |

Mapping approach:

- Use outlet coordinates as anchor points.
- Count POIs within multiple radii, such as 250m, 500m, 1km, and 2km.
- Compute nearest distance to important POI categories.
- Create density features normalized by radius area.
- Optionally cluster outlets into urban, semi-urban, and rural catchment types.

Expected output:

- POI raw extract in Bronze.
- Cleaned POI table in Silver.
- Outlet-level POI features in Gold.

## Phase 5: Gold Feature Engineering

Build model-ready outlet-month features.

Historical sales features:

- Monthly total liters by outlet.
- Average, median, maximum, and recent 3-month rolling volume.
- SKU diversity per outlet.
- Transaction frequency per outlet.
- Bill value per liter as a price or mix proxy.
- Distributor-level volume trend.
- January-specific historical performance.

Constraint proxy features:

- Cooler count and cooler availability.
- Outlet size.
- Sudden volume plateaus.
- Low observed volume despite strong POI catchment.
- High bill value but low volume, suggesting premium mix or price effects.
- Distributor delivery or seasonality patterns.

Seasonality and calendar features:

- Month number.
- Distributor seasonality score.
- Number of holidays in the month.
- Holiday type counts.
- January indicator.

Geospatial and catchment features:

- POI counts by category and radius.
- Weighted footfall score.
- Urban density proxy.
- Distance to nearest high-traffic POI.
- Nearby retail competition intensity.

Final Gold dataset:

- One row per `Outlet_ID`.
- Feature columns needed to estimate January 2026 potential.
- Historical observed-volume aggregates.
- Demand proxy score.
- Constraint proxy score.

## Phase 6: Latent Potential Methodology

Use a transparent two-part approach that separates observed sales from estimated demand ceiling.

### Step 1: Estimate Observed Baseline

Build a baseline model that predicts expected January 2026 observed liters using historical data.

Candidate models:

- Robust linear regression or generalized linear model.
- Random forest or gradient boosting model.
- Quantile regression model.

Purpose:

- Capture normal observed sales behavior.
- Establish a conservative lower bound for each outlet.

### Step 2: Identify Likely Constrained Outlets

Create a constraint-likelihood score using business logic and model residuals.

Signals of constraint:

- Strong POI catchment but low historical volume.
- Medium or large outlet with low volume.
- Cooler count mismatch relative to catchment demand.
- High seasonality area but weak outlet sales.
- Historical volume plateaus or repeated low maximums.
- Similar nearby outlets selling much more.

Output:

- `constraint_score` between 0 and 1.
- Higher score means observed sales are more likely capped below true demand.

### Step 3: Estimate Demand Frontier

Estimate the upper demand frontier using high-performing comparable outlets.

Recommended methods:

- Quantile regression at the 80th, 90th, or 95th percentile.
- Peer benchmarking by outlet type, size, province, distributor, and catchment cluster.
- Frontier model where top-performing outlets define achievable potential.

Logic:

- For each outlet, identify comparable outlets with similar structural and catchment features.
- Estimate what top-quartile or top-decile performance looks like for that peer group.
- Treat this frontier as the candidate uncapped potential.

### Step 4: Blend Baseline and Frontier

Final potential should always be at least observed historical capability, but should increase when constraint evidence is strong.

Suggested formula:

```text
Potential = max(
  Historical_Max_Monthly_Liters,
  Observed_Baseline + constraint_score * (Demand_Frontier - Observed_Baseline)
)
```

Optional guardrails:

- Cap extreme predictions using peer-group percentile limits.
- Ensure potential is non-negative.
- Ensure very small outlets do not receive unrealistic large estimates.
- Smooth predictions within distributor and province groups.

## Phase 7: Model Validation Without Ground Truth

Since true potential is unobserved, validation must be forensic and business-oriented.

Validation checks:

- Potential must be greater than or equal to recent observed sales for most outlets.
- High-potential outlets should have strong demand drivers.
- Low-potential outlets should be small, rural, low-density, or historically saturated.
- Predictions should be stable by province and distributor.
- No distributor or outlet type should show impossible jumps without evidence.
- Top potential outlets should be manually reviewed on a map.

Useful diagnostic outputs:

- Distribution of observed volume vs predicted potential.
- Uplift ratio by outlet type.
- Uplift ratio by province and distributor.
- Top 100 outlets by predicted potential.
- Top 100 outlets by potential uplift.
- Feature importance or SHAP explanation for model interpretability.

## Phase 8: Final Submission Assets

Create the following deliverables:

| Deliverable | Location |
| --- | --- |
| Platform prediction CSV | `Results/smil_labs_predictions.csv` |
| Full all-outlet prediction CSV | `Results/smil_labs_predictions_full_20000.csv` |
| Reproducible pipeline code | `src/` and `Notebooks/` |
| Data quality report | `Docs/data_quality_report.md` |
| AI transparency log | `Docs/ai_transparency_log.md` |
| Final 5-page report | `Docs/final_report.pdf` |
| Run instructions | `README.md` |

## Phase 9: GenAI Transparency Log

Document AI usage throughout the work.

Log entries should include:

- Prompt or task given to the AI tool.
- Why AI was used.
- Output produced by AI.
- Human review performed.
- Validation or correction applied.
- Final decision made by the team.

Examples:

- Brainstorming latent demand frameworks.
- Drafting reusable data quality functions.
- Generating Overpass API query templates.
- Debugging geospatial joins.
- Reviewing model assumptions.
- Drafting report structure.

## Execution Order

1. Read dataset dictionary and confirm field meanings.
2. Implement Bronze ingestion.
3. Build reusable data quality checks.
4. Produce Silver cleaned datasets and rejected records.
5. Run EDA and identify anomalies.
6. Acquire and clean external POI data.
7. Build Gold outlet-level features.
8. Train observed baseline model.
9. Build constraint score.
10. Estimate demand frontier.
11. Produce final potential predictions.
12. Validate outputs with forensic and business checks.
13. Generate final CSV, report, README, and AI log.

## Success Criteria

The solution will be strong if it:

- Preserves raw data faithfully.
- Quarantines bad records with clear reasons.
- Uses reusable and well-documented data quality checks.
- Adds meaningful external catchment features.
- Explains how historical sales are uncapped.
- Produces defensible outlet-level predictions.
- Makes the final methodology understandable to both data scientists and business leaders.
