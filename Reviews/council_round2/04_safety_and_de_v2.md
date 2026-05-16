# TL;DR

- Refactor fixed the biggest submission blocker: `Results/teamname_predictions.csv` now has `Outlet_ID,Maximum_Monthly_Liters`, 20,000 rows, 20,000 unique outlet IDs, 0 NaN, and 0 negative predictions.
- Code organisation is much better, but the visible data evidence is still weak on a fresh tree: `data/bronze/` has only `.gitkeep`, and `data/silver_rejected/*.csv` is empty until `python run_pipeline.py` is run.
- Updated grade: **B today, B+ after one clean full rerun and zipped audit artifacts**. The main day-of-submission risk is not methodology now; it is reproducibility under time pressure.

# Verification of Round-1 Blockers

| Round-1 blocker | Evidence checked | Status | Fix / command |
| --- | --- | --- | --- |
| CSV format: `Outlet_ID`, 20k rows | `Results/teamname_predictions.csv` head is `Outlet_ID,Maximum_Monthly_Liters`; inspection found 20,000 rows, 20,000 unique IDs, 0 NaN, 0 negatives, min 84.153, max 10457.941. | **PASS** | Keep this exact file as the submission artifact. Recheck with `python -c "import pandas as pd; df=pd.read_csv('Results/teamname_predictions.csv'); print(len(df), df.columns.tolist(), df['Outlet_ID'].nunique(), df.isna().sum().to_dict())"`. |
| `src/` module skeleton | Glob over `autokaggle/competition/src/**/*.py` found **23 Python files** under the main `src/` tree, including `src/quality/checks.py`, `src/cleaning/silver.py`, `src/features/gold.py`, `src/modeling/*.py`, and `src/reporting/*.py`. A broader `competition/**/src/**/*.py` glob finds 29 files because it also includes `poi_pipeline/src/*.py`. | **PASS** | Keep the modules in the zip. Do not submit notebook-only code. |
| Rejected records visible | Glob over `data/silver_rejected/*.csv` found **0 CSV files**. `run_pipeline.py` writes them through `write_rejected(...)` and `write_silver(...)`, but they are ignored by `.gitignore`. | **PARTIAL / CRITICAL MUST-RUN** | Before submit: run `python run_pipeline.py`, then confirm `Get-ChildItem data/silver_rejected/*.csv`. If the competition accepts a zip, force-include these CSVs or attach them as audit evidence. |
| Bronze layer visible | Glob over `data/bronze/*` found only `data/bronze/.gitkeep`. `run_pipeline.py` creates raw copies and `_ingestion_audit.csv`, but not yet visible. | **PARTIAL / MUST-RUN** | Run `python run_pipeline.py`; then check `Get-ChildItem data/bronze` and confirm `_ingestion_audit.csv` exists. |
| Reusable DQ checks | `src/quality/checks.py` has parameterized `duplicate_check(key_columns)`, `null_check(columns)`, `range_check(column, min_value, max_value, inclusive)`, `domain_check(allowed_values)`, `referential_integrity_check(reference_values)`, and `geospatial_bounds_check(lat_col, lon_col, ranges)`. | **PASS** | Add one smoke test if time: call each check on a 3-row toy DataFrame. |
| GenAI log discipline | `Docs/ai_transparency_log.md` is still a static area table. It is not a per-phase running log with timestamp, prompt, accepted output, rejected output, and validation result. | **FAIL** | Convert to phase entries before final report: challenge parse, DQ design, pipeline refactor, POI build, model refactor, validation, final report. |

# Reproducibility Audit

## Dependency Coverage

The core `src/` imports are covered by `requirements.txt`:

| Import family | Where used | Covered? | Note |
| --- | --- | --- | --- |
| `pandas`, `numpy` | Most `src/` modules and POI scripts | Yes | `pandas==2.3.3`, `numpy==2.2.6`. |
| `scikit-learn` | `src/features/gold.py`, `src/modeling/constraint_score.py`, `src/modeling/censored_qr.py`, `src/modeling/conformal.py`, `poi_pipeline/src/spatial.py` | Yes | `scikit-learn==1.7.2`. |
| `scipy` | `src/modeling/sfa.py` | Yes | `scipy>=1.13.0`. |
| `xgboost`, `lightgbm` | `src/modeling/frontier.py` | Yes | `xgboost>=2.0.3`, `lightgbm>=4.5.0`. |
| `pyarrow` | Parquet writes/reads in `run_pipeline.py`, `src/cleaning/silver.py`, POI pipeline | Yes | `pyarrow>=18.0.0`. |
| `graphviz` | `src/reporting/dag.py` | Python package yes | Missing system Graphviz binary will not crash; code writes Mermaid fallback. |
| `requests` | `poi_pipeline/01_download_pbf.py` | Yes | Good. |
| `pyrosm`, `geopandas`, `shapely` | `poi_pipeline/src/pbf_loader.py` via `pyrosm` | Listed | **Risk:** `pyrosm` can be painful on Windows / Python 3.13. Test install early. |

Concrete check:

```powershell
cd autokaggle/competition
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "import pandas,numpy,sklearn,scipy,xgboost,lightgbm,pyarrow,requests,graphviz; print('core deps ok')"
python -c "import pyrosm,geopandas,shapely; print('poi deps ok')"
```

## Fresh Clone Path Risks

- `run_pipeline.py` uses `RAW_DIR = ROOT.parent / "datastorm-7-0-rotaract"`. From `autokaggle/competition/run_pipeline.py`, this means raw files must live at `autokaggle/datastorm-7-0-rotaract/`, not inside `autokaggle/competition/`.
- `README.md` layout says `competition/datastorm-7-0-rotaract/`, which conflicts with the actual code path.
- `poi_pipeline/config.py` also points to `ROOT.parent.parent / "datastorm-7-0-rotaract" / "outlet_coordinates.csv"`, which is the same sibling folder under `autokaggle/`.

Fix:

```powershell
cd autokaggle
Test-Path datastorm-7-0-rotaract\outlet_master.csv
Test-Path datastorm-7-0-rotaract\outlet_coordinates.csv
Test-Path datastorm-7-0-rotaract\transactions_history_final.csv
```

Update `README.md` to say the raw data folder must sit at `autokaggle/datastorm-7-0-rotaract/`.

## Missing POI Feature File

`run_pipeline.py` survives a missing `poi_pipeline/output/poi_features.parquet`. In `gold_features(...)`, it checks `POI_FEATURES_PARQUET.exists()` and proceeds without external POI when missing.

This is good for robustness, but it creates a rubric risk: the README says POI is recommended, while the main pipeline can silently submit a non-POI model.

Fix:

```powershell
cd autokaggle/competition
python run_pipeline.py
Select-String -Path Results/validation_report.md -Pattern "PASS|FAIL"
```

If POI was skipped, write that clearly in `Reports/final_report.md` and `Docs/ai_transparency_log.md`.

## SFA Failure / Non-Convergence

`run_pipeline.py` catches hard SFA exceptions and continues:

- exception: prints `SFA failed: ... -- continuing without SFA`
- non-convergence: `fit_sfa(...)` returns `converged=False`, but the pipeline still uses `sfa_frontier` in the blended frontier

That means a crash is unlikely, but a bad non-converged SFA can still affect predictions.

Fix:

```python
if sfa_fit.converged:
    use sfa_frontier
else:
    print("SFA did not converge -- using XGBoost q90 only")
    sfa_out = None
```

This should be changed in `run_pipeline.py` before final submission.

# Submission Preflight (12 items)

| # | What to check | How to check | Failure mode |
| ---: | --- | --- | --- |
| 1 | Raw files are in the path used by code | `cd autokaggle; Test-Path datastorm-7-0-rotaract\outlet_master.csv` | Pipeline fails immediately with `FileNotFoundError`. |
| 2 | Dependencies install in a clean venv | `cd autokaggle/competition; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt` | Submission-day laptop cannot run pipeline. |
| 3 | POI dependency stack works if POI is claimed | `python -c "import pyrosm,geopandas,shapely; print('ok')"` | POI scripts fail after the report claims POI features. |
| 4 | POI features exist or are explicitly skipped | `Test-Path poi_pipeline\output\poi_features.parquet` | Main pipeline silently runs without external POI evidence. |
| 5 | Full pipeline runs from clean state | `Remove-Item data\bronze\*.csv,data\silver\*.parquet,data\gold\*.parquet -ErrorAction SilentlyContinue; python run_pipeline.py` | Hidden notebook state was required. |
| 6 | Bronze audit exists | `Get-ChildItem data\bronze; Import-Csv data\bronze\_ingestion_audit.csv` | No forensic proof of raw ingestion. |
| 7 | Rejected records are populated | `Get-ChildItem data\silver_rejected\*.csv` | DE rubric claim is not visible. |
| 8 | Submission schema is exact | `python -c "import pandas as pd; df=pd.read_csv('Results/teamname_predictions.csv'); print(df.columns.tolist(), len(df))"` | Kaggle/portal rejects file or scores wrong column. |
| 9 | Outlet IDs are complete and unique | `python -c "import pandas as pd; df=pd.read_csv('Results/teamname_predictions.csv'); print(df['Outlet_ID'].nunique(), df['Outlet_ID'].duplicated().sum())"` | Duplicate/missing outlets fail validation. |
| 10 | Predictions have no NaN or negatives | `python -c "import pandas as pd; s=pd.read_csv('Results/teamname_predictions.csv')['Maximum_Monthly_Liters']; print(s.isna().sum(), (s<0).sum(), s.min(), s.max())"` | Portal accepts bad file but score/credibility collapses. |
| 11 | Auto validation is all PASS | `Get-Content Results\validation_report.md` | A known guardrail failure is submitted. |
| 12 | Final zip includes audit evidence | Check zip contents for `src/`, `run_pipeline.py`, `Results/teamname_predictions.csv`, `Docs/ai_transparency_log.md`, `data/silver_rejected/*.csv` if allowed | Judges see claims but not reproducible evidence. |

# 5 Things That Will Likely Break + Mitigations

| Risk | Why it will break | Prevention |
| --- | --- | --- |
| Raw data path mismatch | `README.md` implies `competition/datastorm-7-0-rotaract/`, but `run_pipeline.py` expects `autokaggle/datastorm-7-0-rotaract/`. | Fix README path now. Add `Test-Path` checks to preflight. |
| `pyrosm` install failure | Windows + modern Python can fail on geospatial wheels. This is the riskiest dependency. | Install once in a clean venv today. If it fails, run POI on WSL/Linux or submit with POI explicitly disabled. |
| Rejected CSVs missing from final evidence | `.gitignore` ignores `data/silver_rejected/*.csv`; current Glob found none. | Run `python run_pipeline.py` before packaging. If rules allow, force-include generated rejected CSVs in the final zip. |
| SFA non-converges but still influences predictions | Code catches exceptions but not `converged=False`. | Gate SFA blending on `sfa_fit.converged`; otherwise use only XGBoost q90. |
| Report claims exceed actual run | Pipeline can proceed without POI, Graphviz can fall back, SFA can fail, sensitivity can fail and only warn. | After the final run, update `Reports/final_report.md` and `Docs/ai_transparency_log.md` with what actually ran. |

# Codebase B-S-G Mapping Audit

| Layer / rubric demand | Files | Audit |
| --- | --- | --- |
| Bronze ingestion | `run_pipeline.py` `bronze_ingest()` | Exists and copies raw files to `data/bronze/` with `_ingestion_audit.csv`. Gap: no dedicated `src/ingestion/bronze.py`; `src/ingestion/__init__.py` exists but ingestion logic is still in orchestrator. |
| Silver cleaning | `src/cleaning/silver.py` | Clear Silver module. Handles outlet type/size fixes, coordinate rejection, transaction rejection, holiday dedupe, seasonality scoring, and writes Parquet. |
| Silver DQ / rejected store | `src/quality/checks.py` | Strong. Checks are reusable and parameterizable. Gap: rejected CSVs are generated only after run and ignored by `.gitignore`. |
| Gold feature engineering | `src/features/gold.py` | Clear Gold module. Builds outlet-level historical, catchment, seasonality, holiday, cannibalisation, and optional POI features. |
| External POI feature build | `poi_pipeline/*.py`, `poi_pipeline/src/*.py` | Good separate pipeline. Gap: main run can skip it silently, and POI output is ignored. |
| Modeling | `src/modeling/*.py` | Strong separation: lower bound, frontier, SFA, censored QR, conformal, caps, constraint score, prediction. Gap: SFA convergence flag is not enforced. |
| Reporting / validation | `src/reporting/*.py` | Good. Validation writes markdown/json. Graphviz fallback is robust. Gap: `src/reporting/sensitivity.py` failure is caught and only warned by `run_pipeline.py`, so final report can be stale if not checked. |
| Overall B-S-G clarity | `README.md`, `run_pipeline.py`, `src/` | Much improved. The code now reflects Bronze -> Silver -> Gold, but Bronze is less modular than Silver/Gold because it lives inside `run_pipeline.py`. |

# Strengths

- The submission CSV blocker is fixed. This is the biggest operational improvement from round 1.
- `src/quality/checks.py` is genuinely reusable and parameterized. This now matches the DE rubric language.
- `run_pipeline.py` is a real one-shot orchestrator with no CLI flags, consistent with the project convention.
- The pipeline has practical robustness: missing POI features do not crash, Graphviz failure does not crash, SFA exception does not crash, and sensitivity sweep failure does not crash.
- The codebase now has a visible lakehouse shape: `quality`, `cleaning`, `features`, `modeling`, and `reporting` are separate and inspectable.
- The validation suite in `src/reporting/validation.py` is concrete and submission-oriented.

# Updated Grade

**Grade now: B.**

Round 1 was **D+ today / B- after refactor**. The refactor has happened and it fixed the severe CSV and empty-`src/` blockers. I would not give B+ yet because the pipeline has not been proven from a clean run in this audit, `data/silver_rejected/*.csv` is empty on disk, Bronze has only `.gitkeep`, the GenAI log is still static, and SFA non-convergence can still leak into predictions.

**B+ unlock condition:** one clean `python run_pipeline.py` from a fresh venv, visible Bronze audit, visible rejected CSVs, final `Results/validation_report.md` all PASS, README raw path fixed, and SFA blending gated on `sfa_fit.converged`.
