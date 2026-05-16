# Data-Storm-2026

End-to-end pipeline for estimating latent maximum monthly outlet purchase potential for January 2026.

**Note (v2):** the canonical pipeline is now the v2 stack (`Notebooks/20_v2_*`, `21_v2_*`, `22_v2_*`) which incorporates all 3 rounds of AI council fixes. The v1 notebooks (`01_`, `03_`, `04_`, `10_`, `11_`) are retained for reference but produce the broken submission (`row_id` column + 914 rows + miscalibrated constraint score). The v1 CSVs have been moved to `Results/_legacy/`.

## Project Layout (v2 canonical)

```
Notebooks/
  20_v2_data_pipeline.ipynb              Bronze -> Silver -> Gold
  21_v2_modeling.ipynb                   frontier + SFA + censored QR + CQR + Manski
  22_v2_validation_and_submission.ipynb  6-item validation + submission CSV (Outlet_ID + 20,000 rows)
  01_latent_potential_pipeline.ipynb     v1 (kept for reference, do not use)
  02_full_dataset_eda.ipynb              full-dataset EDA
  03_poi_enrichment.ipynb                v1 POI work (kept; v2 uses poi_pipeline/ instead)
  04_model_validation.ipynb              v1 validation
  10_poi_enrichment_full.ipynb           v1 POI full
  11_constraint_score_improvements.ipynb v1 constraint experiments
src/
  quality/         reusable DQ check functions
  cleaning/        Silver normalisation
  features/        Gold feature engineering
  modeling/        lower_bound, constraint_score, frontier, sfa, conformal, censored_qr, caps, predict
  reporting/       manski, dag, sensitivity, validation
poi_pipeline/      Geofabrik PBF + pyrosm POI fetcher (separate folder)
Reviews/           council R1 + R2 + R3 audits
Reports/           5-page PDF source + builder
research/          10-channel research swarm + brief
Docs/              team docs (challenge brief, EDA summary, methodology, etc.)
Results/           current v2 submission goes here; v1 CSVs in Results/_legacy/
data/              Bronze/Silver/Gold/silver_rejected (gitignored runtime artifacts)
```

## Key files

- `Notebooks/20_v2_data_pipeline.ipynb` — v2 Bronze/Silver/Gold pipeline.
- `Notebooks/21_v2_modeling.ipynb` — v2 modeling stack.
- `Notebooks/22_v2_validation_and_submission.ipynb` — v2 validation + submission CSV writer.
- `Docs/challenge_brief.md` — cleaned challenge statement.
- `Docs/solution_plan.md` — planned solution approach.
- `Docs/modeling_methodology.md` — methodology explanation.
- `Docs/poi_enrichment.md` — external POI enrichment workflow.
- `Docs/ai_transparency_log.md` (+ `_v2.md`) — Generative AI usage log.
- `Reviews/council_review.md` + `council_round2/council_review_v2.md` + `council_round3/council_review_v3.md` — 3-round AI council audit trail.
- `Reports/final_report.md` — 5-page PDF source.
- `SUBMISSION_CHECKLIST.md` — preflight checklist for submission day.
- `Results/smil_labs_predictions_v2.csv` — current submission file (written by notebook 22).
- `Results/_legacy/` — v1 CSVs kept for audit only, NOT for upload.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies. Use **`requirements_v2.txt`** for the v2 pipeline (the original `requirements.txt` is missing xgboost>=2.0, mapie, statsmodels, pyrosm, geopandas, h3, etc.):

```powershell
pip install -r requirements_v2.txt
```

(If you only intend to run the v1 notebooks, `pip install -r requirements.txt` is enough.)

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

## Run Pipeline (v2 canonical)

```powershell
# Optional: external POI enrichment (~25 min)
cd poi_pipeline
python 01_download_pbf.py
python 02_extract_pois.py
python 03_build_features.py
python 04_quality_audit.py
cd ..

# v2 pipeline: run notebooks 20 -> 21 -> 22 in order
jupyter notebook Notebooks/20_v2_data_pipeline.ipynb
jupyter notebook Notebooks/21_v2_modeling.ipynb
jupyter notebook Notebooks/22_v2_validation_and_submission.ipynb
```

The v2 notebooks create:

- raw Bronze copies + sha-256 audit in `data/bronze/`
- cleaned Silver parquets in `data/silver/`
- 480 coord + 9,606 transaction rejected records in `data/silver_rejected/`
- outlet x feature matrix in `data/gold/outlet_features.parquet`
- quantile + SFA predictions in `data/gold/`
- final submission CSV in `Results/smil_labs_predictions_v2.csv`
- conformal interval bands in `Results/conformal_intervals_v2.csv`
- Manski bounds in `Results/manski_bands_v2.csv`
- 6-item validation report in `Results/validation_report.md`

**Submission columns** (per official Data Storm 7.0 PDF):

- `Outlet_ID` — outlet identifier (NOT `row_id` — the v1 column name is wrong)
- `Maximum_Monthly_Liters` — predicted uncapped monthly purchase potential

The submission file has **20,000 rows** (one per outlet in scope). The "platform validator expects 914 rows" claim from the v1 pipeline is unverified by the official PDF; the v2 file follows the brief's wording. If the portal actually requires 914 rows on submission day, filter `smil_labs_predictions_v2.csv` to the official row_id list at upload time.

## Current Method (v2)

Observed sales are right-censored: `y = min(true_demand, constraint)`. The estimand `E[true_demand_i | X_i]` is **not point-identified** from observational data alone (Manski 2003); we therefore report `[manski_lower, point, manski_upper]` per outlet.

**Method stack** (the council-recommended minimal-but-impressive set):

1. **Robust lower bound** — 3rd-highest month or own p95 (defends against single-month spikes).
2. **Frontier ensemble** — XGBoost 2.0 multi-quantile (`reg:quantileerror`, monotone constraints, isotonic post-sort) blended 60/40 with Aigner-Lovell-Schmidt 1977 SFA fit by direct MLE.
3. **Chernozhukov-Hong (2002) 3-step** censoring correction — q90 refit on the uncensored sub-population.
4. **Constraint score** in [0,1] — PCA + frontier-residual z-score + plateau gate (no DQ flag, no rank-sum).
5. **Bootstrap-derived size×type uplift caps** — replaces hardcoded multipliers with peer top-decile evidence.
6. **Conformalised QR** (Romano et al. NeurIPS 2019) — calibrated [q05, q95] interval on a disjoint outlet-level holdout.
7. **Manski worst-case bounds** for honest non-identification disclosure.

See `Docs/modeling_methodology.md` for the v1 narrative and `Reports/final_report.md` for the v2 5-page report.

## AI Council Audit Trail

The v2 stack was built and audited across 5 rounds of parallel premium-model critics:

- `Reviews/council_review.md` — Round 1 master (v1 grade D+).
- `Reviews/council_round2/council_review_v2.md` — Round 2 after src/ refactor (grade B/B+).
- `Reviews/council_round3/council_review_v3.md` — Round 3 after v2 notebook build (grade B today).
- `Reviews/council_round4/council_review_v4.md` — Round 4: ROOT CAUSE of V3b+V4 (rounding bug + uplift floor). Post-fix: 6/6 PASS.
- `Reviews/council_round5/council_review_v5.md` — Round 5: `run_pipeline.py` bugs (rounding, team name, SHA-12), report placeholders, stale doc audit. Grade ~77 → 83.

Every code fix cites the council finding it addresses (`FIX R4`, `FIX R5 N5.x`, `FIX M1`, etc.).
