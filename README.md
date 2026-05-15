# Data-Storm-2026

Notebook-first solution for estimating latent maximum monthly outlet purchase potential for January 2026.

## Project Layout

Key files:

- `Notebooks/01_latent_potential_pipeline.ipynb` - end-to-end implementation notebook.
- `Docs/challenge_brief.md` - cleaned challenge statement.
- `Docs/solution_plan.md` - planned solution approach.
- `Docs/folder_structure.md` - repository structure explanation.
- `Docs/data_quality_report.md` - generated data quality summary.
- `Docs/modeling_methodology.md` - latent potential modeling explanation.
- `Docs/ai_transparency_log.md` - Generative AI usage log.
- `Results/teamname_predictions.csv` - final prediction output using the platform schema.

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

Open and run all cells in:

```text
Notebooks/01_latent_potential_pipeline.ipynb
```

The notebook will create:

- raw Bronze copies in `data/bronze/`
- cleaned Silver data in `data/silver/`
- rejected records in `data/silver_rejected/`
- model features and diagnostics in `data/gold/`
- final predictions in `Results/teamname_predictions.csv`

Submission columns:

- `row_id` - outlet identifier expected by the competition validator.
- `Maximum_Monthly_Liters` - predicted uncapped monthly purchase potential.

## Current Method

The model treats observed sales as censored demand. It uses historical outlet performance as a lower bound and blends toward a peer frontier when constraint signals suggest that the outlet is under-realizing demand.

The final prediction is guardrailed by:

- historical observed maximums.
- comparable outlet peer frontiers.
- outlet-size uplift caps.
- non-negative output constraints.

See `Docs/modeling_methodology.md` for details.
