# Generative AI Transparency Log

This document records how Generative AI was used as an engineering accelerator during the solution build.

## Usage Log

| Area | AI Assistance | Human Validation |
| --- | --- | --- |
| Challenge understanding | Summarized the business problem and converted the prompt into structured documentation. | Reviewed against the original problem statement and saved as `Docs/challenge_brief.md`. |
| Solution planning | Drafted a Bronze, Silver, Gold execution plan and latent potential methodology. | Adapted to the actual repository and available datasets. |
| Repository structure | Proposed lakehouse folders and documentation layout. | Created tracked folders with `.gitkeep` and documented them in `Docs/folder_structure.md`. |
| Notebook implementation | Helped draft notebook cells for ingestion, quality checks, cleaning, feature engineering, and modeling. | Ran the notebook end to end in a local virtual environment and inspected generated outputs. |
| Data quality logic | Suggested reusable duplicate, null, range, domain, and referential integrity checks. | Verified checks against real data anomalies such as invalid coordinates and negative transactions. |
| Modeling logic | Suggested a lower-bound plus peer-frontier approach for latent demand uncapping. | Evaluated prediction distributions and revised the method after the first result was too conservative. |
| Guardrail tuning | Helped identify excessive uplift outliers and add size-based caps. | Re-ran predictions and checked uplift ratios, row counts, and missing values. |
| Git workflow | Helped diagnose a GitHub push rejection caused by a file over 100 MB. | Removed challenge datasets from Git history, kept them local, and added `Datasets/` to `.gitignore`. |
| POI enrichment | Helped scaffold an OpenStreetMap Overpass workflow and integrate POI demand features into the model. | Ran the notebook, handled an Overpass query rejection by splitting requests by category, and validated POI feature counts before regenerating predictions. |

## Validation Principles

AI-generated code and assumptions were not accepted blindly.

Validation actions included:

- running the notebook end to end.
- checking prediction row counts and uniqueness.
- checking missing and negative predictions.
- comparing potential predictions against historical maxima.
- reviewing rejected record counts.
- revising the model when results were too conservative.
- adding guardrails when uplift became too aggressive.

## Current AI-Accelerated Artifacts

- `Docs/challenge_brief.md`
- `Docs/solution_plan.md`
- `Docs/folder_structure.md`
- `Docs/data_quality_report.md`
- `Docs/modeling_methodology.md`
- `Docs/ai_transparency_log.md`
- `Notebooks/01_latent_potential_pipeline.ipynb`

## Remaining Human Review Needed

Before final submission, the team should manually review:

- the highest potential outlets.
- the highest uplift outlets.
- peer frontier assumptions.
- final POI categories once external geospatial features are added.
- the final PDF report narrative.
