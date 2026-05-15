# Next Steps After Full Dataset EDA

The full EDA shows that the solution should now move from a clean internal-data baseline toward stronger demand-signal enrichment and better validation.

## 1. Lock Down Data Hygiene

Use the EDA findings to keep the Silver layer strict:

- standardize `Grocry` to `Grocery`.
- standardize `Bakry` to `Bakery`.
- standardize lowercase `small` to `Small`.
- convert missing outlet sizes to `Unknown`.
- quarantine 240 invalid coordinate rows.
- quarantine non-positive transaction volume or bill-value rows.
- aggregate holiday data before feature engineering because duplicate holiday rows exist.

## 2. Strengthen Outlet-Level Features

The EDA shows a large gap between median observed outlet maximum and the 95th percentile. This supports a peer-frontier approach, but the model needs richer features to explain why some outlets can reach the frontier.

Recommended internal features:

- outlet age or active-month count.
- January-specific historical mean and max.
- recent three-month volume trend.
- SKU breadth and SKU consistency.
- average value per liter.
- distributor-level monthly strength.
- outlet-size and outlet-type peer percentile features.
- cooler adequacy relative to peer group.
- volatility and plateau indicators.

## 3. Add POI and Catchment Features

The biggest missing competitive improvement is external geospatial demand data.

Recommended POI categories:

- schools and universities.
- bus stops, railway stations, and transport hubs.
- markets and shopping areas.
- offices and banks.
- hospitals and clinics.
- restaurants, cafes, bakeries, and eateries.
- supermarkets and groceries.
- religious places.
- hotels and tourist attractions.

Recommended features:

- POI counts within 250m, 500m, 1km, and 2km.
- nearest distance to each major POI category.
- total catchment density score.
- retail competition score.
- urban versus rural cluster label.

## 4. Improve Latent Potential Methodology

Current logic uses:

- historical maximum as the lower bound.
- constraint score as the uncapping signal.
- peer frontier as the potential ceiling.
- size-based uplift caps as guardrails.

Next improvement:

- add POI density into the constraint score.
- estimate frontier separately by outlet segment.
- compare quantile regression, peer percentile frontier, and stochastic frontier logic.
- add diagnostic tables for top uplift outlets.

## 5. Fix Submission Template Risk

The written brief asks for 20,000 rows, but the platform validator expects 914 rows.

Current workaround:

- `Results/teamname_predictions.csv` contains 914 rows for platform upload.
- `Results/teamname_predictions_full_20000.csv` preserves the full outlet deliverable.

Best next action:

- download the official `sample_submission.csv`, `submission_template.csv`, or `test.csv`.
- place it inside `Datasets/`.
- rerun `Notebooks/01_latent_potential_pipeline.ipynb`.
- the notebook will filter predictions to the exact official `row_id` values.

## 6. Prepare Final Report

Use the EDA and methodology docs to build the final 5-page PDF.

Suggested report structure:

1. Problem framing and latent demand logic.
2. Data lakehouse pipeline and rejected-record handling.
3. EDA and data forensics findings.
4. Feature engineering and POI acquisition plan.
5. Modeling method, validation, and AI transparency.
