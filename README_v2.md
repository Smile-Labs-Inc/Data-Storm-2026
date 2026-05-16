# Data Storm 7.0 — Latent Outlet Potential (Sri Lanka)

End-to-end pipeline that estimates the **maximum monthly purchase potential (liters)** for 20,000 traditional retail outlets across Sri Lanka for January 2026.

The target is a **latent variable** — observed sales are the `min(true demand, operational constraint)`, so we frame this as a right-censored estimation problem and solve it with a stack of econometric and ML methods.

## Repository layout (Bronze / Silver / Gold lakehouse)

```
competition/
  datastorm-7-0-rotaract/        # raw competition data (gitignored when sized > 100 MB)
  data/
    bronze/                      # raw copies + ingestion audit hashes
    silver/                      # cleaned parquet per dataset
    silver_rejected/             # one CSV per dataset with failed records + reason
    gold/                        # outlet x feature parquet, predictions, cap table, SFA fit
  src/
    quality/                     # reusable, parameterizable DQ checks
    cleaning/                    # silver normalisation + dedup + scoring
    features/                    # gold feature engineering
    modeling/                    # lower_bound, constraint_score, frontier, sfa, conformal, censored_qr, caps, predict
    reporting/                   # manski, dag, sensitivity, validation
  poi_pipeline/                  # OSM POI fetch + feature build (separate folder)
  Notebooks/                     # legacy EDA + pipeline notebooks (kept for reference)
  Reports/
    figures/                     # DAG, sensitivity table, plots for the PDF
    final_report.md              # 5-page PDF source
  Reviews/                       # AI council audits (round 1 + round 2)
  research/                      # 10-channel research swarm outputs + brief
  Docs/                          # team docs (auto-generated DQ report etc.)
  Results/                       # final submission CSV + manski bands + validation
  run_pipeline.py                # one-shot orchestrator (no CLI flags)
  requirements.txt               # pinned deps
```

## How to run end-to-end

```powershell
cd autokaggle/competition

# 1. Set up venv + deps
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. (Optional but recommended) Fetch external POI data first
cd poi_pipeline
python 01_download_pbf.py     # downloads ~136 MB Sri Lanka OSM PBF, idempotent
python 02_extract_pois.py     # parses 9 categories, writes per-category parquets
python 03_build_features.py   # outlet x POI features -> output/poi_features.parquet
python 04_quality_audit.py    # writes Sri Lanka coverage caveats for the report
cd ..

# 3. Run the main pipeline
python run_pipeline.py
```

Final submission lands at `Results/teamname_predictions.csv` with columns `Outlet_ID, Maximum_Monthly_Liters`.

## Methodology (one-paragraph)

The estimand `E[true_demand_i | X_i]` is **not point-identified** from observational data alone (Manski, 2003). We disclose this honestly and report a `[lower, point, upper]` band.

The **point estimate** combines:

- a **robust lower bound** = the outlet's 3rd-highest observed month (defends against single-month spikes);
- a **frontier** that ensembles two independent methods:
  1. **XGBoost 2.0 multi-quantile regression** (`reg:quantileerror` with `quantile_alpha=[0.5, 0.75, 0.9, 0.95]`, monotone constraints on cooler / SKU / catchment / cannibalisation);
  2. **Stochastic Frontier Analysis** (Aigner-Lovell-Schmidt, 1977) with truncated-normal inefficiency `u`, fit by direct MLE (`scipy.optimize`); we use `TE = exp(-u)` as a second constraint signal;
- a **constraint score** in `[0, 1]` from three orthogonal signals (frontier residual z-score, plateau gate, PCA-decorrelated capacity), composed via sigmoid;
- **Chernozhukov-Hong (2002) 3-step censoring correction** so the q90 model is fit on uncensored rows only;
- **bootstrap size x type uplift caps** estimated from peer top-decile uplift (replaces hardcoded multipliers);
- final formula: `potential = lower_bound + constraint_score * (frontier - lower_bound)`, clipped to the bootstrap cap.

The **interval** is built with **Conformalized Quantile Regression** (Romano et al., NeurIPS 2019) on an outlet-level holdout, plus **Manski worst-case bounds** for honest disclosure.

See `Reports/final_report.md` for the full 5-page narrative.

## Validation (no ground truth -> 6-item auto-checklist)

`run_pipeline.py` ends by running 6 automatic checks and writing `Results/validation_report.md`:

1. Schema + 20,000 row count + correct column names.
2. No NaN, no negatives, unique `Outlet_ID`.
3. Every `Outlet_ID` exists in `outlet_master`.
4. `predicted >= historical_max` for >= 99% of outlets.
5. Median uplift in `[1.05, 2.5]` range.
6. Cap-binding rate < 25%.

## What was fixed since v1

- `row_id` -> `Outlet_ID` and 914-row -> 20,000-row submission file.
- `data/silver_rejected/` actually populated (480 coordinate + 9,606 transaction rows quarantined with documented reasons).
- `same_type_outlet_count_2km` sign flipped (cannibalisation, not catchment).
- `valid_coordinate_rank` removed from constraint_score (it was a DQ flag, not a demand signal).
- Quadruple throttle (`^1.25` + `clip(0, 0.65)` + size cap + peer-p98 cap) replaced with a single, evidence-derived bootstrap cap.
- POI scraping pipeline added (Geofabrik PBF + pyrosm).
- Constraint score rebuilt as PCA + frontier-residual + plateau-gate composite.
- SFA + Conformalised QR + Censored QR added as report-grade methodology.

See `Reviews/council_review.md` (round 1) and `Reviews/council_review_v2.md` (round 2) for the full audit trail.

## GenAI transparency

See `Docs/ai_transparency_log.md` for the per-phase log of how Generative AI was used (prompts, validations, decisions) during the 36-hour build.
