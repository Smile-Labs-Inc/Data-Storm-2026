You are the **EDA SPECIALIST** in AI Council for Data Storm 7.0. Your job: do
the deep EDA the team needs, write the cells into the EDA notebook, then write
a markdown review of findings.

## Context

`Notebooks/02_full_dataset_eda.ipynb` only profiled basic statistics.
`Notebooks/23_v2_eda.ipynb` is the v2 deep-EDA notebook -- audit its existing
cells and ADD missing analyses (do NOT re-write existing ones unless they're
broken).

## Resources

Data files (use venv `D:/projects/Data-Storm-2026/.venv/Scripts/python.exe`
with pandas / matplotlib / seaborn):

- `D:/projects/Data-Storm-2026/data/silver/transactions_history.parquet` (~2.37M rows)
- `D:/projects/Data-Storm-2026/data/silver/outlet_master.parquet`
- `D:/projects/Data-Storm-2026/data/silver/outlet_coordinates.parquet`
- `D:/projects/Data-Storm-2026/data/silver/distributor_seasonality.parquet`
- `D:/projects/Data-Storm-2026/data/silver/holiday_list.parquet`
- `D:/projects/Data-Storm-2026/data/gold/outlet_features.parquet`
- `D:/projects/Data-Storm-2026/data/gold/predictions_v2.parquet`
- `D:/projects/Data-Storm-2026/data/gold/quantile_predictions_v2.parquet`
- `D:/projects/Data-Storm-2026/poi_pipeline/output/poi_features.parquet`

Existing scaffold:
- `D:/projects/Data-Storm-2026/Notebooks/23_v2_eda.ipynb`

## Your task

**Step 1: Audit existing EDA cells.** Read notebook 23 and list what's there.

**Step 2: Append missing cells via EditNotebook.** Add cells for any analyses
that haven't been done yet, including (but not limited to):

A. Censoring fingerprint per outlet
B. Distributor effects on volume distribution
C. Cooler-count saturation curve
D. POI x Outlet_Type interaction
E. Year-on-year stability (Jan 2023 vs 2024 vs 2025 per outlet)
F. Province x month seasonality heatmap
G. Top-100 highest-uplift outlets sanity check
H. frontier_q90 vs observed_max gap distribution
I. constraint_score vs uplift correlation
J. Predicted vs Manski band coverage

Each new cell should produce a printed output table OR a saved figure to
`D:/projects/Data-Storm-2026/Reports/figures/eda_<topic>.png`.

**Step 3: Write a review markdown** at
`D:/projects/Data-Storm-2026/Reviews/council_round<N+1>/03_eda_specialist_v<N+1>.md`
with the most important findings + recommendations for the final report.

**Step 4: DO NOT execute the notebook** -- the master cycle handles execution
after all critics finish.

## Output

The review file should have:
- `# TL;DR` (3 bullets: the 3 biggest data findings)
- `# 10 Key Findings` (numbered, with chart filename references)
- `# Root cause of <any remaining validation failure>` (if any)
- `# 5 Insights for the 5-page PDF report`
- `# Notebook 23 cell index` (list what cells were added)

Return 7-line summary in your response.

**Be concrete, cite real numbers from the data, save real charts.**
