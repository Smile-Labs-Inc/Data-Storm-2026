# Data Engineer Critic — Round 4

**Data Storm 7.0 · DE Rubric (40% of total) · Audit date: 2026-05-16**

---

# TL;DR

- **v1 artifacts are still polluting `data/gold/`** (`outlet_features.csv`, `validation_top_100_potential.csv`, `validation_top_100_uplift.csv`) and `Results/smile_labs_predictions.csv` is still in root — a judge who grabs the wrong file submits 914 rows with `row_id` headers.
- **Silver layer carries ~200 MB of stale CSVs** alongside every parquet; they serve no rubric purpose and silently mislead anyone inspecting the silver directory.
- **Two fixes away from a strong DE grade:** delete 5 v1 files + call `write_summary_md` from checks.py (already written, just not called). Everything else is good.

---

# DE Rubric Scorecard

| Criterion                                       | Score /10 | Evidence                                                                                                                                                                                                                                                                                      | Cheapest Fix                                                                                                                                                                                                                                                         |
| ----------------------------------------------- | :-------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **DQ checks — reusable & parameterizable**      |   **8**   | `src/quality/checks.py`: 6 typed functions (`duplicate_check`, `null_check`, `range_check`, `domain_check`, `referential_integrity_check`, `geospatial_bounds_check`), `QualityResult` dataclass, `summarise_checks`. `quality_summary.csv` on disk (27 rows). Applied to all 5 raw datasets. | Call `write_summary_md()` (already in checks.py line 192) in notebook 20 cell → produces `data/silver_rejected/quality_summary.md` for judges who prefer readable docs.                                                                                              |
| **Cleaning / Silver**                           |   **7**   | `src/cleaning/silver.py`: typo maps (`Grocry→Grocery`, `Bakry→Bakery`), case normalisation, coordinate bounds drop (240 rows), holiday dedup (93 rows), seasonality scoring. Coordinate teleport bug fixed (was R1 critical).                                                                 | Delete 5 stale silver CSVs (`distributor_seasonality.csv`, `holiday_list.csv`, `outlet_coordinates.csv`, `outlet_master.csv`, `transactions_history.csv`) — parquets are canonical. Remove `data/bronze/_ingestion_audit.csv` (superseded by `ingestion_audit.csv`). |
| **Feature engineering / Gold**                  |  **8.5**  | `src/features/gold.py`: 23 features — 15 numeric (p90, p95, jan-specific, recent-3-mo, BallTree multi-radius, cannibalisation 200 m, same-distributor 5 km), 3 categorical, optional POI merge. Graceful degradation when `poi_pipeline/output/poi_features.parquet` absent.                  | Delete `data/gold/outlet_features.csv` (v1 CSV). The `.parquet` is the v2 output; both coexisting is confusing.                                                                                                                                                      |
| **Reproducibility — fresh clone → notebook 20** |  **5.5**  | `RAW_DIR` error message fixed (R3). `requirements_v2.txt` has 16 packages. ROOT detection present.                                                                                                                                                                                            | (a) Add Windows install note for `geopandas`/`pyrosm` (conda-forge or binary wheel). (b) Add `run_manifest.json` write at end of notebook 20. (c) Move `Results/smile_labs_predictions.csv` → `_legacy/`.                                                            |
| **Governance / Provenance**                     |   **7**   | `data/bronze/ingestion_audit.csv`: SHA-256 per dataset, row counts, UTC timestamp. `data/silver_rejected/*_rejected.csv`: 6 files populated with `failure_reason` column. `quality_summary.csv` exists.                                                                                       | Delete `data/bronze/_ingestion_audit.csv` (truncated SHA-12 version, superseded). Clarify `smile_labs_predictions_full_20000.csv` in Results/ (no `_v2` suffix — is this v1 or v2?).                                                                                 |

**Weighted total (all criteria equal at 8%): ~7.2 / 10**

---

# v1 vs v2 File Mix Audit

## `data/gold/` — full classification

| File                                  | Size    | Version                                                       | Action                                                            |
| ------------------------------------- | ------- | ------------------------------------------------------------- | ----------------------------------------------------------------- |
| `outlet_features.csv`                 | 7.6 MB  | **v1** — no `_v2` suffix, CSV format, written by old notebook | **DELETE** — `outlet_features.parquet` is the v2 canonical output |
| `outlet_features.parquet`             | 2.6 MB  | **v2**                                                        | KEEP — primary gold feature table for notebooks 21+22             |
| `outlet_monthly_sales.csv`            | 39 MB   | **intermediate / shared** — no versioned name                 | EXCLUDE from zip; keep locally for debugging only                 |
| `outlet_poi_features_full.csv`        | 10 MB   | **v2** — POI enrichment output                                | EXCLUDE from zip (intermediate); keep for audit                   |
| `poi_coverage_summary_full.png`       | 64 KB   | **v2** diagnostic                                             | KEEP for Docs/ or presentation                                    |
| `cap_table_v2.csv`                    | 1.3 KB  | **v2**                                                        | KEEP                                                              |
| `predictions_v2.parquet`              | 1.3 MB  | **v2**                                                        | KEEP                                                              |
| `quantile_predictions_v2.parquet`     | 602 KB  | **v2**                                                        | KEEP                                                              |
| `prediction_diagnostics.csv`          | 4.2 MB  | **intermediate**                                              | EXCLUDE from zip                                                  |
| `validation_top_100_potential.csv`    | 11 KB   | **v1** — no `_v2` suffix                                      | **DELETE** — `_v2.csv` version exists                             |
| `validation_top_100_potential_v2.csv` | 13 KB   | **v2**                                                        | KEEP                                                              |
| `validation_top_100_uplift.csv`       | 11 KB   | **v1** — no `_v2` suffix                                      | **DELETE** — `_v2.csv` version exists                             |
| `validation_top_100_uplift_v2.csv`    | 13.7 KB | **v2**                                                        | KEEP                                                              |

**Delete count: 3 files (outlet_features.csv + 2 v1 validation CSVs). Total savings: ~18 MB.**

## `data/silver/` — CSV + parquet doubles

| File pair                                  | Size               | Issue                                        | Action                             |
| ------------------------------------------ | ------------------ | -------------------------------------------- | ---------------------------------- |
| `outlet_master.csv` + `.parquet`           | 529 KB + 164 KB    | CSV is v1/intermediate; parquet is canonical | Delete CSV                         |
| `outlet_coordinates.csv` + `.parquet`      | 588 KB + 526 KB    | Same                                         | Delete CSV                         |
| `transactions_history.csv` + `.parquet`    | **197 MB** + 50 MB | CSV is 4× larger for same data               | **Delete CSV** — biggest space win |
| `distributor_seasonality.csv` + `.parquet` | 11 KB + 4 KB       | Same                                         | Delete CSV                         |
| `holiday_list.csv` + `.parquet`            | 19 KB + 5.5 KB     | Same                                         | Delete CSV                         |

**Total silver CSV bloat: ~198 MB. Delete all 5 silver CSVs — parquets are `write_silver()` outputs.**

## `data/bronze/` — dual audit files

| File                   | Size   | Issue                                                       | Action     |
| ---------------------- | ------ | ----------------------------------------------------------- | ---------- |
| `ingestion_audit.csv`  | 1040 B | Full SHA-256, UTC timestamp, row counts — **authoritative** | KEEP       |
| `_ingestion_audit.csv` | 257 B  | Truncated SHA-12, no timestamp — older format               | **DELETE** |

## `Results/` — v1 still in root

| File                                       | Issue                                                                      | Action                                         |
| ------------------------------------------ | -------------------------------------------------------------------------- | ---------------------------------------------- |
| `smile_labs_predictions.csv`               | v1 — `row_id` column + 914 rows, still in root (R3 flagged as NOT TOUCHED) | Move to `Results/_legacy/` NOW                 |
| `smile_labs_predictions_full_20000.csv`    | No `_v1` or `_v2` suffix — ambiguous                                       | Rename to `_v1` or confirm it is a v2 artifact |
| `smile_labs_predictions_v2.csv`            | v2 canonical                                                               | KEEP                                           |
| `smile_labs_predictions_full_20000_v2.csv` | v2                                                                         | KEEP — includes full 20,000 rows               |

---

# Reproducibility Audit

**Scenario: fresh clone → `pip install -r requirements_v2.txt` → run `20_v2_data_pipeline.ipynb`**

| #   | Risk                                                                                                                                   | Severity        | Fix                                                                                                                                            |
| --- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `Datasets/` absent → `FileNotFoundError` with clear message                                                                            | INFO — expected | Fine as-is                                                                                                                                     |
| 2   | `geopandas` on Windows requires Fiona/GDAL binary; pure `pip install` often fails                                                      | **HIGH**        | Add conda-forge note: `conda install -c conda-forge geopandas pyrosm h3-py`                                                                    |
| 3   | `pyrosm` on Windows has C-extension build issues                                                                                       | **HIGH**        | Same conda-forge note; or mark as optional (POI is already graceful-skip)                                                                      |
| 4   | `requirements_v2.txt` pins pandas/numpy/sklearn exactly but uses `>=` for geopandas, pyrosm, h3 — version drift risk                   | MEDIUM          | Add upper bounds or freeze post-run with `pip freeze > requirements_frozen.txt`                                                                |
| 5   | ROOT detection: `Path.cwd().parent if Path.cwd().name == "Notebooks"` — breaks if notebook opened from project root or a different CWD | MEDIUM          | Replace with `Path(__file__).resolve().parents[1]` or an explicit `ROOT = Path("..").resolve()` with an `assert (ROOT / "src").exists()` guard |
| 6   | Silver CSVs on disk may be read by accident before notebook 20 runs; they're stale v1 data                                             | MEDIUM          | Delete them; only keep parquets                                                                                                                |
| 7   | `data/bronze/_ingestion_audit.csv` vs `ingestion_audit.csv` — two audit files, neither is referenced by name in README                 | LOW             | Delete `_ingestion_audit.csv`; add README mention of `ingestion_audit.csv`                                                                     |
| 8   | `poi_pipeline/output/poi_features.parquet` absent → POI skipped silently                                                               | LOW — graceful  | OK; document in README clearly                                                                                                                 |
| 9   | No `run_manifest.json` — no cryptographic proof a particular run produced the gold parquets                                            | LOW             | Add 10-line json write at notebook 20 end: gold sha-256, row count, UTC timestamp                                                              |
| 10  | `src/__pycache__/` committed to git                                                                                                    | LOW             | Add `**/__pycache__/` to `.gitignore`                                                                                                          |

**Verdict:** risks 2–3 (Windows geopandas/pyrosm) are the only hard blockers for a judge on a clean Windows machine. Everything else is either already graceful or a 5-minute fix.

---

# 30-Minute Cleanup Plan

Prioritised. Do these in order; stop when time runs out — each step independently improves the rubric.

## Block 1 — File cleanup (10 min, highest DE rubric impact)

- [ ] **Delete `data/gold/outlet_features.csv`** — v1 artifact next to v2 parquet
- [ ] **Delete `data/gold/validation_top_100_potential.csv`** — v1 superseded by `_v2.csv`
- [ ] **Delete `data/gold/validation_top_100_uplift.csv`** — same
- [ ] **Delete `data/silver/*.csv`** (5 files, 198 MB) — stale doubles; parquets are canonical
- [ ] **Delete `data/bronze/_ingestion_audit.csv`** — superseded by `ingestion_audit.csv`
- [ ] **Move `Results/smile_labs_predictions.csv` → `Results/_legacy/`** — risk of wrong-file upload
- [ ] **Rename or tag `Results/smile_labs_predictions_full_20000.csv`** — clarify v1 vs v2

## Block 2 — DQ evidence (5 min, direct rubric points)

- [ ] In notebook 20, after `summarise_checks(...)`, call `write_summary_md(summary, SILVER_REJECTED_DIR / "quality_summary.md")` — the function already exists in `checks.py:192`; it just isn't being called
- [ ] Add a notebook cell that prints total unique rejected rows per dataset (not just per check) — judges read notebook outputs

## Block 3 — Reproducibility (10 min)

- [ ] Add to `requirements_v2.txt` a comment block:
  ```
  # Windows users: install geopandas, pyrosm, h3-py via conda-forge
  # conda install -c conda-forge geopandas pyrosm h3-py
  ```
- [ ] Add ROOT guard to notebook 20 cell 1: `assert (ROOT / "src").exists(), f"Bad ROOT: {ROOT}"`
- [ ] Write `run_manifest.json` at end of notebook 20:
  ```python
  import json, hashlib
  manifest = {"run_utc": ..., "gold_sha256": ..., "outlet_features_rows": len(gold_df)}
  (GOLD_DIR / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
  ```

## Block 4 — Governance polish (5 min)

- [ ] Add `**/__pycache__/` to `.gitignore`
- [ ] Add one line to README: "Bronze SHA-256 audit: `data/bronze/ingestion_audit.csv`"
- [ ] Delete `data/gold/prediction_diagnostics.csv` and `data/gold/outlet_monthly_sales.csv` from git tracking (they're intermediate, 43 MB combined)

---

# Final Repo Zip Inclusions/Exclusions

**Target: ≤ 100 MB upload. Data Storm 7.0 portal.**

## Include

| Path                                               | Rationale                |
| -------------------------------------------------- | ------------------------ |
| `src/` (\*.py only, no **pycache**)                | Full pipeline code       |
| `Notebooks/20_v2_data_pipeline.ipynb`              | Bronze→Silver→Gold       |
| `Notebooks/21_v2_modeling.ipynb`                   | Modeling stack           |
| `Notebooks/22_v2_validation_and_submission.ipynb`  | Submission writer        |
| `Notebooks/23_v2_eda.ipynb`                        | EDA (optional but small) |
| `requirements_v2.txt`                              | Dependency spec          |
| `README.md`, `SUBMISSION_CHECKLIST.md`             | Project docs             |
| `Results/smile_labs_predictions_v2.csv`            | **Canonical submission** |
| `Results/smile_labs_predictions_full_20000_v2.csv` | Full 20,000-row version  |
| `Results/conformal_intervals_v2.csv`               | Uncertainty bands        |
| `Results/manski_bands_v2.csv`                      | Manski bounds            |
| `Results/validation_report.md`                     | 6-item validation        |
| `data/gold/outlet_features.parquet`                | Feature table            |
| `data/gold/predictions_v2.parquet`                 | Primary predictions      |
| `data/gold/quantile_predictions_v2.parquet`        | Quantile outputs         |
| `data/gold/cap_table_v2.csv`                       | Uplift caps              |
| `data/gold/validation_top_100_potential_v2.csv`    | Validation sample        |
| `data/gold/validation_top_100_uplift_v2.csv`       | Validation sample        |
| `data/silver_rejected/quality_summary.csv`         | DQ evidence              |
| `data/silver_rejected/*_rejected.csv`              | Rejected-row audit       |
| `data/bronze/ingestion_audit.csv`                  | SHA-256 provenance       |
| `Docs/` (all .md)                                  | Methodology, EDA summary |
| `Reports/final_report.md` + `.pdf`                 | 5-page writeup           |
| `Reviews/` (all council rounds)                    | AI transparency log      |
| `poi_pipeline/*.py` (scripts only, not `output/`)  | POI pipeline code        |
| `.gitignore`                                       |                          |

## Exclude

| Path                                           | Reason                                                                          |
| ---------------------------------------------- | ------------------------------------------------------------------------------- |
| `Datasets/`                                    | Raw CSVs — competition rules + `transactions_history_final.csv` is 169 MB alone |
| `data/silver/*.parquet` + `data/silver/*.csv`  | Reproducible intermediates; derived from Datasets/                              |
| `data/bronze/transactions_history_final.csv`   | 169 MB — exceeds portal limit alone                                             |
| `data/bronze/poi_overpass_full_*.json`         | 10 MB raw API cache — reproducible, not rubric-scored                           |
| `data/gold/outlet_monthly_sales.csv`           | 39 MB intermediate                                                              |
| `data/gold/outlet_poi_features_full.csv`       | 10 MB intermediate                                                              |
| `data/gold/prediction_diagnostics.csv`         | 4.2 MB intermediate                                                             |
| `data/gold/poi_coverage_summary_full.png`      | Optional diagnostic                                                             |
| `Results/_legacy/`                             | v1 files — wrong submission risk                                                |
| `Notebooks/01_*, 03_*, 04_*, 10_*, 11_*.ipynb` | v1 notebooks; README calls them broken                                          |
| `__pycache__/`, `*.pyc`                        | Bytecode                                                                        |
| `.venv/`                                       | Local virtualenv                                                                |
| `research/`                                    | Large research swarm output; not rubric-scored                                  |

**Estimated zip size after exclusions: ~25–35 MB.** Well within 100 MB.

---

# Strengths

- **`src/quality/checks.py` is textbook rubric compliance.** The `QualityResult` dataclass, 6 parameterized check functions, `summarise_checks`, and `write_rejected` match the rubric language ("reusable, parameterizable, applied consistently") almost verbatim. A judge reading this module will tick the DQ box immediately.

- **Rejected records actually exist on disk.** `data/silver_rejected/` has 6 populated CSV files with `failure_reason` columns. The `quality_summary.csv` shows 240 coordinate rejects, 4,853 volume rejects, 4,753 bill-value rejects. This is verifiable evidence, not a claim in a PDF.

- **Coordinate teleport bug was caught and fixed.** The R1 critical bug (invalid coords → median imputation → 240 outlets silently teleported to a central point) is now a clean drop-to-rejected path in `silver.py:63–83`. This is the kind of spatial data integrity detail that separates serious submissions.

- **`ingestion_audit.csv` with full SHA-256.** Five datasets, full hash, row count, UTC timestamp. Judges can verify the bronze files match what the code ran against. Most competition submissions skip provenance entirely.

- **Gold feature engineering is genuinely competition-level.** 23 features, BallTree haversine with three radii (1/2/5 km), 200 m cannibalisation grouping, same-distributor density, optional external POI merge with graceful degradation. The feature set is defensible and grounded in the Sri Lanka FMCG research swarm.

---

# Grade vs DE Rubric

| Criterion               |   Now   | After 30-min cleanup |
| ----------------------- | :-----: | :------------------: |
| DQ checks               |    8    |        **9**         |
| Cleaning / Silver       |    7    |       **8.5**        |
| Feature engineering     |   8.5   |        **9**         |
| Reproducibility         |   5.5   |       **7.5**        |
| Governance / Provenance |    7    |       **8.5**        |
| **Total /10**           | **7.2** |       **8.5**        |

**Current DE grade: 7.2 / 10**
**Post-cleanup DE grade: 8.5 / 10 (achievable in 30 minutes)**

The ceiling is 9.5 — knocked down by the Windows geopandas/pyrosm install risk (hard to fully solve without a conda environment) and the absence of `run_manifest.json` (which is a 10-line fix but requires a re-run to generate the hash).
