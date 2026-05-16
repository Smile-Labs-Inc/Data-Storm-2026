# Data Engineer Critic — Council Round 5
**Data Storm 7.0 · DE Rubric (40% of total) · Audit date: 2026-05-16**

---

# TL;DR

- **The canonical entry point is broken.** `run_pipeline.py` (README's "run this") produces a file named `teamname_predictions.csv` with V3b rounding failure. The notebook-22 fix exists in isolation — the orchestrator was never updated.
- **Provenance story has a hole.** The PDF claims "SHA-256 audit log"; the actual audit CSV column is `sha256_12` with 12 hex chars. This is discoverable in 10 seconds.
- **Five new ambiguous files added to `Results/` today** — the directory that was supposed to be cleaned up in R4. The research pipeline output landed here without documentation.
- **Two fixes and 15 minutes separate the team from a clean reproductible-from-scratch demo.** Nothing architectural is broken. Everything is plumbing.

---

# DE Rubric Scorecard (R5 State)

| Criterion | Score /10 | Evidence | Fix |
|---|:---:|---|---|
| **DQ checks — reusable & parameterizable** | **9** | `src/quality/checks.py` 6 functions unchanged and correct. `write_summary_md` now called from `run_pipeline.py:168`. `quality_summary.csv` on disk. | No action needed. |
| **Cleaning / Silver** | **8** | `src/cleaning/silver.py` clean. Silver parquets written correctly. CSV doubles still on disk (gitignored, won't be in zip). | Optional: delete 5 silver CSVs to tidy local env. |
| **Feature engineering / Gold** | **8.5** | `src/features/gold.py`: 23 features + optional POI merge, BallTree correct. `data/gold/outlet_features.parquet` produced correctly. Stale `outlet_features.csv` (v1) still on disk but gitignored. | Optional: delete stale gold CSVs. |
| **Reproducibility — fresh clone → run** | **4.5** | **N5.1**: `run_pipeline.py:363` has `.round(3)` not `np.ceil`. **N5.2**: `TEAM_NAME = "teamname"`. Fresh clone + `python run_pipeline.py` = wrong file, V3b fail. | Fix both in `run_pipeline.py`. |
| **Governance / Provenance** | **6.5** | **N5.3**: `sha256_12` column (12 chars) contradicts SHA-256 claim. `_ingestion_audit.csv` written by pipeline; authoritative `ingestion_audit.csv` also on disk — two audit files with conflicting formats. | Fix `[:12]` slice + column name + filename. |

**Weighted total: 7.3 / 10** (up from 7.2 in R4; Gold and DQ improved)
**Post-R5-fix total: 8.8 / 10**

---

# File Audit (R5 Delta)

## New files in `Results/` since R4

| File | Size | Created | Issue | Action |
|---|---|---|---|---|
| `smil_labs_predictions_research.csv` | 17 KB | today 20:07 | ~570 rows — NOT the 20k submission | Move to `Results/_research/` |
| `smil_labs_predictions_research_full.csv` | 2.6 MB | today 20:07 | ~145k rows — multi-scenario research output | Move to `Results/_research/` |

These were presumably written by `Notebooks_Research/05_research_pipeline.ipynb`. They are in the canonical submission directory, untagged, at a different row count. This is the same "5 prediction files" footgun that R3 flagged as a disqualification risk.

## `data/gold/` — new stale files since R4

| File | Status |
|---|---|
| `outlet_features_v2.csv` | NEW since R4 — duplicate of `outlet_features.parquet` in CSV form. Gitignored but on-disk clutter. |
| `outlet_poi_features.csv` | NEW since R4 — same issue. Gitignored. |
| `validation_extreme_uplift.csv` | NEW since R4 — diagnostic output, not rubric-relevant. |
| `validation_missed_opportunity.csv` | NEW since R4 — same. |

## `run_pipeline.py` bugs

### Bug 1 — Line 363: `.round(3)` not ceil-rounded

```python
# CURRENT (broken):
sub["Maximum_Monthly_Liters"] = sub["Maximum_Monthly_Liters"].round(3)

# REQUIRED (R4 fix applied to nb22, but not here):
sub["Maximum_Monthly_Liters"] = np.ceil(sub["Maximum_Monthly_Liters"] * 1000) / 1000
```

The V3b validation check compares the rounded output against the un-rounded historical max. The 55%+ of outlets pinned exactly at `observed_max` (float64 with many decimals) get pushed BELOW `observed_max` by banker's rounding. Result: 27.92% V3b fail when run from `python run_pipeline.py`.

### Bug 2 — Line 90: Wrong team name

```python
# CURRENT:
TEAM_NAME = "teamname"
# Produces: Results/teamname_predictions.csv  Results/teamname_predictions_full_20000.csv

# REQUIRED:
TEAM_NAME = "smil_labs"
# Produces: Results/smil_labs_predictions.csv  Results/smil_labs_predictions_full_20000.csv
```

The README, submission checklist, and every prior council review reference `smil_labs_predictions.csv`. Fresh pipeline run = wrong name.

### Bug 3 — Lines 124-129: SHA-12 + wrong audit filename

```python
# CURRENT:
sha = hashlib.sha256(dst.read_bytes()).hexdigest()[:12]
audit.append({"file": name, "size_bytes": dst.stat().st_size, "sha256_12": sha})
pd.DataFrame(audit).to_csv(BRONZE_DIR / "_ingestion_audit.csv", index=False)

# REQUIRED:
sha = hashlib.sha256(dst.read_bytes()).hexdigest()   # full 64-char hash
audit.append({"file": name, "size_bytes": dst.stat().st_size, "sha256": sha})
pd.DataFrame(audit).to_csv(BRONZE_DIR / "ingestion_audit.csv", index=False)
```

The PDF says "SHA-256 audit log". The code produces a 12-char SHA. The column is labelled `sha256_12`, making the truncation visible to any judge who opens the file. The filename also writes `_ingestion_audit.csv` (with leading underscore) while the authoritative full-SHA file from a previous run is `ingestion_audit.csv` — two audit files with different contents.

---

# Reproducibility Risk Matrix

| Risk | Severity | Fix |
|---|---|---|
| `python run_pipeline.py` → V3b FAIL + wrong filename | **CRITICAL** | N5.1 + N5.2 |
| SHA-12 exposed in audit CSV (contradicts PDF) | **HIGH** | N5.3 |
| Windows geopandas/pyrosm no pip install note | MEDIUM | Add conda-forge comment to `requirements_v2.txt` (optional) |
| Two audit CSV files (`ingestion_audit.csv` + `_ingestion_audit.csv`) | MEDIUM | Fix N5.3 to write one canonical file |
| Research CSVs in `Results/` (wrong row count, no doc) | MEDIUM | Move to `_research/` subfolder |
| No `run_manifest.json` | LOW | Add 10-line write in `run_pipeline.py` (optional) |

---

# 30-Minute Fix Plan

```
[ ] 1 min  — run_pipeline.py:363: replace .round(3) with np.ceil fix
[ ] 1 min  — run_pipeline.py:90:  TEAM_NAME = "smil_labs"
[ ] 5 min  — run_pipeline.py:124-129: SHA-256 full + column rename + filename
[ ] 2 min  — mkdir Results/_research/; mv smil_labs_predictions_research*.csv there
[ ] 5 min  — add one comment line to requirements_v2.txt re: conda-forge
[ ] Total: ~14 minutes
```

After these fixes: `python run_pipeline.py` produces `Results/smil_labs_predictions.csv` with V3b-safe rounding, full SHA-256 in `data/bronze/ingestion_audit.csv`, and no ambiguous files in `Results/`.

---

# Final Grade

| | Now | After 14-min cleanup |
|---|:---:|:---:|
| DE rubric /10 | **7.3** | **8.8** |
| Reproducibility concern | CRITICAL (run_pipeline.py) | CLEAN |
| SHA-256 claim | CONTRADICTED | VERIFIED |
