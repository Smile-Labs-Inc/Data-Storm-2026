# Safety + DE Review v3 - Reproducibility + Rubric Readiness

## TL;DR

1. **No, the v2 notebooks are not fresh-clone runnable today.**
2. `D:/projects/Data-Storm-2026/Notebooks/20_v2_data_pipeline.ipynb` cell **2** falls back to a private local `ALT_RAW_DIR`; `D:/projects/Data-Storm-2026/Datasets/` does not exist here.
3. `D:/projects/Data-Storm-2026/requirements.txt` is still v1-thin; it misses Parquet, SFA, XGBoost/LightGBM, notebook, and POI deps.
4. Notebook 22 writes `Results/smile_labs_predictions_v2.csv`, but the visible old upload file remains `Results/smile_labs_predictions.csv`.
5. The current upload-looking CSV head is `row_id,Maximum_Monthly_Liters`, so the team can upload the wrong file by habit.
6. Notebook 20 is close to DQ-rubric-ready in code, but no generated evidence exists yet: no Bronze output, no Gold output, no rejected CSVs, no POI output.
7. **Final grade today: B- design, C+ reproducibility.** After one clean fresh-clone run, fixed deps, and a one-file submission package, this can be B+/A-.

## Will v2 Run?

**Verdict: not reliably, and not on a fresh team machine without manual fixes.**

Notebook 20 cell **2** is the first blocker:

```python
RAW_DIR = ROOT / "Datasets"          # try here first
ALT_RAW_DIR = ROOT.parent / "Logical" / "logical-context" / "autokaggle" / "datastorm-7-0-rotaract"  # local alt
```

That fallback is one developer's local path. It will not exist on a normal teammate or judge machine. In this checkout, `D:/projects/Data-Storm-2026/Datasets/` also does not exist, so notebook 20 cell **4** fails on the first missing raw file:

```python
if not src.exists():
    raise FileNotFoundError(f"raw file missing: {src} -- check RAW_DIR")
```

Other path and run risks:

- `D:/projects/Data-Storm-2026/README.md` still documents the v1 flow: `Notebooks/01_latent_potential_pipeline.ipynb`, `Results/smile_labs_predictions.csv`, `row_id`, and a 914-row fallback. It does not tell the team to run notebooks **20 -> 21 -> 22**.
- `D:/projects/Data-Storm-2026/.gitignore` ignores `Datasets/`, Bronze/Silver/Gold outputs, and rejected CSVs. Good for repo size, bad for fresh-clone evidence.
- Notebook 21 cell **1** reads `data/gold/outlet_features.parquet` and `data/silver/transactions_history.parquet`; those only exist after notebook 20.
- Notebook 22 cell **1** reads `predictions_v2.parquet`, `quantile_predictions_v2.parquet`, `cap_table_v2.csv`, Gold features, and Silver parquet files; those only exist after notebooks 20 and 21.
- Notebook 20 cell **15** treats `poi_pipeline/output/poi_features.parquet` as optional. That avoids a crash, but the report must not claim POI was used unless that file exists.

Current filesystem evidence from requested globs:

```text
D:/projects/Data-Storm-2026/data/silver_rejected/*.csv -> 0 files
D:/projects/Data-Storm-2026/data/bronze/* -> only .gitkeep
D:/projects/Data-Storm-2026/data/gold/* -> only .gitkeep
D:/projects/Data-Storm-2026/poi_pipeline/output/* -> 0 files
D:/projects/Data-Storm-2026/Datasets/* -> path does not exist
```

## Reproducibility Audit

`D:/projects/Data-Storm-2026/requirements.txt` currently contains only:

```text
pandas==2.3.3
numpy==2.2.6
scikit-learn==1.7.2
openpyxl==3.1.5
requests==2.34.2
reportlab==4.5.1
```

This cannot run v2 end to end.

| Missing dependency                                     | Needed by                                                                                                        | Risk                                                         |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `pyarrow` or `fastparquet`                             | Notebook 20 writes Parquet; notebooks 21/22 read Parquet; `src/cleaning/silver.py` writes Parquet                | **Blocker**                                                  |
| `scipy`                                                | `src/modeling/sfa.py` imports `scipy.optimize.minimize` and `scipy.stats.norm`; notebook 21 cell **11** fits SFA | **Blocker**                                                  |
| `xgboost>=2.0.3`                                       | `src/modeling/frontier.py`; notebook 21 cell **9** claims XGBoost 2.0 multi-quantile                             | **Blocker**                                                  |
| `lightgbm`                                             | `src/modeling/frontier.py` fallback if XGBoost 2.0 is absent                                                     | Required if fallback remains                                 |
| `graphviz` Python package                              | `src/reporting/dag.py`; notebook 22 DAG output                                                                   | Optional because Mermaid fallback exists                     |
| `jupyter` / `ipykernel`                                | Running notebooks in a clean venv                                                                                | Usability blocker                                            |
| `pyrosm`                                               | `poi_pipeline/src/pbf_loader.py` imports `pyrosm.OSM`                                                            | Required if POI is claimed; high Windows install risk        |
| `geopandas`, `shapely`, `pyproj`, `pyogrio` or `fiona` | Practical GeoPandas/pyrosm stack                                                                                 | Required in practice for POI                                 |
| `matplotlib`, `seaborn`, `statsmodels`, `h3`, `tqdm`   | Present in `requirements_v2.txt` / likely report or POI support                                                  | Add if the v2 env is standardized from `requirements_v2.txt` |

`mapie` is mentioned in the v2 dependency story and appears in `requirements_v2.txt`, but the inspected v2 notebooks do **not** import it. Notebook 21 cell **21** uses custom `src.modeling.conformal.conformalised_qr`, not MAPIE. Add `mapie` only if the report/README still claims a MAPIE implementation.

Also verify `requests==2.34.2`; if that exact pin is unavailable on the team's index, even the v1-thin install fails.

## Submission CSV Mitigation

Current risk is high because both names can exist:

- Existing v1-looking file: `D:/projects/Data-Storm-2026/Results/smile_labs_predictions.csv`
- New v2 file from notebook 22 cell **3**: `D:/projects/Data-Storm-2026/Results/smile_labs_predictions_v2.csv`

Head of the existing file:

```text
row_id,Maximum_Monthly_Liters
OUT_00001,1941.47
OUT_00002,1668.42
OUT_00003,1790.852
OUT_00004,1682.09
OUT_00005,1815.721
```

That file still looks upload-ready, but it uses `row_id`, not `Outlet_ID`. Notebook 22 fixes this only in the `_v2.csv` path:

- Cell **0** says the policy is non-destructive and does not overwrite `smile_labs_predictions.csv`.
- Cell **3** writes `Results/smile_labs_predictions_v2.csv` and `Results/smile_labs_predictions_full_20000_v2.csv`.
- Cell **16** says to copy v2 over the normal name, but that is a markdown footnote, not an enforced step.

Mitigation without touching v1:

1. Leave `Results/smile_labs_predictions.csv` unchanged.
2. Create `D:/projects/Data-Storm-2026/submission_package/`.
3. Put exactly one CSV in it: `submission_package/smile_labs_predictions.csv`, copied from `Results/smile_labs_predictions_v2.csv`.
4. Add `submission_package/README_UPLOAD.txt` with source path, timestamp, expected schema, and expected row count.
5. Add `submission_package/smile_labs_predictions.sha256`.
6. Run a final check that the first line is exactly `Outlet_ID,Maximum_Monthly_Liters`.
7. Use two-person signoff: one reads the filename, one verifies header + row count before upload.

## DQ Rubric Compliance

**Verdict: mostly yes in code design, not yet in artifact evidence.**

The rubric asks for reusable, parameterizable DQ checks applied to all datasets.

What notebook 20 gets right:

- Cell **1** imports reusable checks from `src.quality`.
- `D:/projects/Data-Storm-2026/src/quality/checks.py` defines `duplicate_check`, `null_check`, `range_check`, `domain_check`, `referential_integrity_check`, `geospatial_bounds_check`, `summarise_checks`, and `write_rejected`.
- The checks are parameterizable: examples include `range_check(..., min_value=..., max_value=..., inclusive=...)`, `domain_check(..., allowed_values=...)`, and `geospatial_bounds_check(..., lat_range=..., lon_range=...)`.
- Cell **6** applies checks across all five raw datasets: `outlet_master`, `outlet_coordinates`, `transactions_history`, `distributor_seasonality`, and `holiday_list`.
- Cell **7** writes `Docs/data_quality_report.md` and rejected rows via `write_rejected(...)`.

Weak spots:

- The check plan is hardcoded in notebook 20 cell **6**, not driven by a single reusable dataset-spec table.
- `VALID_DISTRIBUTORS` is hardcoded in notebook 20 cell **2**.
- The current tree has no generated v2 DQ report or rejected CSV evidence because notebook 20 has not run.

Rubric answer: **yes for source-code structure; no for final artifact readiness until notebook 20 is executed and its generated DQ evidence is included or cited.**

## Rejected Records Status

Current status: **no rejected-record CSVs exist.**

```text
D:/projects/Data-Storm-2026/data/silver_rejected/*.csv -> 0 files
```

After notebook 20 runs, the folder should be populated:

- Cell **7** calls `write_rejected(qc, SILVER_REJECTED_DIR)`.
- `src/quality/checks.py` writes `<dataset>_rejected.csv` files when failures exist.
- If no failures exist, `write_rejected(...)` writes `_no_rejections.csv`, so the folder should not stay empty.
- Cell **11** calls `write_silver(..., SILVER_REJECTED_DIR, rejected)` for cleaned coordinates, transactions, and holidays.

Expected after a real run: `outlet_coordinates_rejected.csv`, `transactions_history_rejected.csv`, `holiday_list_rejected.csv`, or at minimum `_no_rejections.csv`. Today it is still placeholder-only.

## v2 Preflight

1. Confirm `D:/projects/Data-Storm-2026/Datasets/` exists.
2. Confirm raw files exist: `outlet_master.csv`, `outlet_coordinates.csv`, `transactions_history_final.csv`, `distributor_seasonality_details.csv`, `holiday_list.csv`, and `1. dataset_description.xlsx`.
3. Remove or disable the private `ALT_RAW_DIR` fallback in notebook 20 cell **2**.
4. Replace/merge `requirements.txt` with the v2 dependency set.
5. Create a clean venv and install only from `requirements.txt`.
6. Smoke-test imports: `pandas`, `numpy`, `sklearn`, `pyarrow`, `scipy`, `xgboost`, `lightgbm`.
7. If POI is claimed, smoke-test `pyrosm`, `geopandas`, `shapely`, `pyproj`, and the PBF download path.
8. Run notebooks in order: `20_v2_data_pipeline.ipynb` -> `21_v2_modeling.ipynb` -> `22_v2_validation_and_submission.ipynb`.
9. After notebook 20 cell **4**, confirm `data/bronze/_ingestion_audit.csv` exists.
10. After notebook 20 cell **7**, confirm `Docs/data_quality_report.md` exists.
11. After notebook 20 cells **7** and **11**, confirm `data/silver_rejected/*.csv` exists.
12. After notebook 20 cell **11**, confirm `data/silver/*.parquet` exists.
13. After notebook 20 cell **16**, confirm `data/gold/outlet_features.parquet` exists.
14. If POI is claimed, confirm `poi_pipeline/output/poi_features.parquet` exists before relying on notebook 20 cell **15**.
15. After notebook 21 cell **17**, confirm `data/gold/cap_table_v2.csv` exists.
16. After notebook 21 cell **21**, confirm `Results/conformal_intervals_v2.csv` exists.
17. After notebook 21 cell **23**, confirm `Results/manski_bands_v2.csv` exists.
18. After notebook 21 cell **24**, confirm `data/gold/predictions_v2.parquet` and `data/gold/quantile_predictions_v2.parquet` exist.
19. After notebook 22 cell **3**, confirm `Results/smile_labs_predictions_v2.csv` exists.
20. Confirm final upload columns are exactly `Outlet_ID,Maximum_Monthly_Liters`.
21. Confirm row count matches the official portal requirement.
22. Confirm no duplicate `Outlet_ID`, no missing predictions, and no negative predictions.
23. Confirm notebook 22 cell **5** validation output passes.
24. Confirm final report claims only artifacts that exist.
25. Put exactly one CSV in `submission_package/` and upload only that file.

## 5 Things That Will Break

1. **Raw data path breaks.** Cause: `Datasets/` is absent and notebook 20 cell **2** falls back to a private local path. Mitigation: remove `ALT_RAW_DIR`; require `ROOT / "Datasets"`; add a first-cell raw-file checklist.

2. **Parquet breaks.** Cause: `requirements.txt` lacks `pyarrow` or `fastparquet`. Mitigation: add `pyarrow>=18.0.0`; run a `to_parquet` / `read_parquet` smoke test before notebooks.

3. **Modeling imports break.** Cause: `requirements.txt` lacks `scipy`, `xgboost>=2.0`, and `lightgbm`. Mitigation: add the deps, or remove fallback paths and fail loudly with a clear install message.

4. **Wrong CSV gets uploaded.** Cause: old `Results/smile_labs_predictions.csv` remains beside new `Results/smile_labs_predictions_v2.csv`. Mitigation: create `submission_package/` with one CSV only; use two-person filename/schema signoff.

5. **POI claim fails under audit.** Cause: `poi_pipeline/output/*` is empty, but the report may claim external POI enrichment. Mitigation: run the POI pipeline and show `poi_features.parquet`, or clearly state that the submitted v2 run excludes external POI.

## Strengths

- The notebook split is much safer than the old monolith: data pipeline, modeling, and validation/submission are separate.
- Notebook 20 cell **6** applies DQ checks across all five raw datasets.
- `src/quality/checks.py` is a real reusable DQ module with parameterized checks.
- `write_rejected(...)` writes real rejected files, or `_no_rejections.csv` as a sentinel.
- Notebook 20 cell **16** writes a Gold feature table for downstream modeling.
- Notebook 21 cell **9** moves the frontier to an XGBoost 2.0 multi-quantile path.
- Notebook 21 cell **11** has an SFA path and avoids the round-2 leaky observed aggregate columns in the notebook feature list.
- Notebook 21 cell **21** writes conformal interval output.
- Notebook 21 cell **23** writes a Manski-band artifact.
- Notebook 22 cell **3** writes the corrected `Outlet_ID` schema in the v2 output.
- Notebook 22 cell **5** adds an explicit validation suite before handoff.
- The non-destructive `_v2.csv` policy protects v1 while the team compares results; it just needs packaging discipline.

## Final Grade

**Design grade: B-.** The v2 structure is credible: reusable DQ checks, rejected-store logic, separated notebooks, validation, v2 submission, CQR/SFA/Manski paths.

**Reproducibility grade: C+.** It is not ready for a fresh clone. `requirements.txt` is incomplete, README still points to v1, generated folders are empty, `Datasets/` is absent, and notebook 20 contains a non-portable fallback path.

**Rubric readiness after fixes: B+/A-.** To earn it, the team must run notebooks 20 -> 21 -> 22 in a clean venv, fix `requirements.txt`, remove the local fallback, produce rejected CSVs, and package only the validated v2 upload file.
