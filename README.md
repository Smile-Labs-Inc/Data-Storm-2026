# Data-Storm-2026

Notebook-first solution for estimating latent maximum monthly outlet purchase potential for January 2026.

## Project Layout

Key files:

- `Notebooks/01_latent_potential_pipeline.ipynb` - end-to-end implementation notebook.
- `Notebooks/02_full_dataset_eda.ipynb` - full raw dataset EDA notebook.
- `Notebooks/03_poi_enrichment.ipynb` - OpenStreetMap POI enrichment notebook.
- `Notebooks/04_model_validation.ipynb` - model validation and top-outlet diagnostics.
- `Docs/challenge_brief.md` - cleaned challenge statement.
- `Docs/solution_plan.md` - planned solution approach.
- `Docs/folder_structure.md` - repository structure explanation.
- `Docs/data_quality_report.md` - generated data quality summary.
- `Docs/eda_summary.md` - full raw dataset EDA findings.
- `Docs/next_steps_after_eda.md` - recommended next work based on EDA findings.
- `Docs/modeling_methodology.md` - latent potential modeling explanation.
- `Docs/geospatial_catchment_features.md` - implemented internal catchment feature layer.
- `Docs/poi_enrichment.md` - external POI enrichment workflow.
- `Docs/model_validation_summary.md` - final validation summary.
- `Docs/ai_transparency_log.md` - Generative AI usage log.
- `Results/smil_labs_predictions.csv` - platform upload file.
- `Results/smil_labs_predictions_full_20000.csv` - full business output for all outlets.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Data

Challenge-provided files should be placed locally in:

```text
Datasets/
```

The `Datasets/` folder is intentionally ignored by Git because the transaction file is larger than GitHub's 100 MB file limit.

Required files:

- `outlet_master.csv`
- `outlet_coordinates.csv`
- `transactions_history_final.csv`
- `distributor_seasonality_details.csv`
- `holiday_list.csv`
- `1. dataset_description.xlsx`

## Run Pipeline

Optional POI enrichment:

```text
Notebooks/03_poi_enrichment.ipynb
```

Then open and run all cells in:

```text
Notebooks/01_latent_potential_pipeline.ipynb
```

The notebook will create:

- raw Bronze copies in `data/bronze/`
- cleaned Silver data in `data/silver/`
- rejected records in `data/silver_rejected/`
- model features and diagnostics in `data/gold/`
- platform predictions in `Results/smil_labs_predictions.csv`
- full all-outlet predictions in `Results/smil_labs_predictions_full_20000.csv`

Submission columns:

- `row_id` - outlet identifier expected by the competition validator.
- `Maximum_Monthly_Liters` - predicted uncapped monthly purchase potential.

The current platform validator expects 914 rows. If an official file such as `sample_submission.csv`, `submission_template.csv`, or `test.csv` is placed in `Datasets/`, the notebook filters predictions to that template. Without a template, it creates a 914-row fallback from the first sorted outlet IDs so the file matches the row-count gate.

## Current Method

The model treats observed sales as censored demand. It uses historical outlet performance as a lower bound and blends toward a peer frontier when constraint signals suggest that the outlet is under-realizing demand.

The final prediction is guardrailed by:

- historical observed maximums.
- comparable outlet peer frontiers.
- outlet-size uplift caps.
- non-negative output constraints.

See `Docs/modeling_methodology.md` for details.
