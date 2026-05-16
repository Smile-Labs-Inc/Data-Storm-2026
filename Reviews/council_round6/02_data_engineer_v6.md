# Data Engineer Critic — Council Round 6
**Data Storm 7.0 · DE Rubric (40% of total) · Audit date: 2026-05-16**

---

# TL;DR

- **R5 plumbing fixes landed.** `run_pipeline.py` now has `TEAM_NAME="smil_labs"`, full SHA-256, `np.ceil` rounding, and `ingestion_audit.csv`. The canonical entry point is clean.
- **File hygiene regressed.** `data/gold/` has 13 stale CSV files (~73 MB). `Results/` has 4 duplicate prediction CSVs. `Docs/smil_labs_final_report.md` (stale v1) still present. These were all flagged in R4/R5 and not actioned.
- **Reproducibility is one `pip install` away from clean.** The `requirements_v2.txt` covers all deps. The `RAW_DIR` at `run_pipeline.py:78` points to `ROOT.parent / "datastorm-7-0-rotaract"` — a team-specific path that won't exist on a judge's machine. This needs a fallback or clear error message.

---

# DE Rubric Scorecard (R6 State)

| Criterion | Score /10 | Evidence | Fix |
|---|:---:|---|---|
| **DQ checks — reusable & parameterizable** | **9** | `src/quality/checks.py` 6 functions correct. `write_summary_md` called from `run_pipeline.py:168`. `Docs/data_quality_report.md` on disk. | No action needed. |
| **Cleaning / Silver** | **8.5** | `src/cleaning/silver.py` clean. Silver parquets written. `data/silver_rejected/` populated. CSV doubles in silver/ are gitignored. | Optional: delete silver CSVs. |
| **Feature engineering / Gold** | **8.0** | `src/features/gold.py`: 23 features + optional POI merge. `data/gold/outlet_features.parquet` produced. **BUT** 13 stale CSV files in gold/ (~73 MB) — v1 artifacts + diagnostics. | Delete all CSVs in gold/ except .gitkeep. |
| **Reproducibility — fresh clone → run** | **7.0** | `run_pipeline.py` clean. **BUT** `RAW_DIR` hardcoded to `ROOT.parent / "datastorm-7-0-rotaract"` — judge's machine won't have this. `requirements_v2.txt` complete but no conda-forge note for geopandas/pyrosm on Windows. | Add clear error if RAW_DIR missing. Add conda-forge note. |
| **Governance / Provenance** | **7.5** | SHA-256 full hash in `ingestion_audit.csv`. **BUT** 4 duplicate prediction CSVs in Results/, stale smil_labs_final_report.md visible, no `run_manifest.json`. | Clean Results/, archive stale doc, add manifest. |

**Weighted total: 8.0 / 10** (up from 7.3 in R5)
**Post-R6-fix total: 9.0 / 10**

---

# v1 vs v2 File Mix Audit

## `data/gold/` — 13 files, only 1 is canonical

| File | Type | Size | Action |
|---|---|---|---|
| `outlet_features.parquet` | **v2 canonical** | — | **KEEP** |
| `outlet_features.csv` | v1 duplicate | 6.2 MB | DELETE |
| `outlet_features_v2.csv` | v2 duplicate | 9.6 MB | DELETE |
| `outlet_monthly_sales.csv` | v1 intermediate | 39.1 MB | DELETE |
| `outlet_poi_features.csv` | v1 POI | 220 KB | DELETE |
| `outlet_poi_features_full.csv` | v1 POI full | 10.1 MB | DELETE |
| `poi_cleaned.csv` | v1 POI cleaned | 605 KB | DELETE |
| `prediction_diagnostics.csv` | diagnostic dump | 4.7 MB | DELETE |
| `validation_extreme_uplift.csv` | diagnostic | 137 B | DELETE |
| `validation_missed_opportunity.csv` | diagnostic | 4.8 KB | DELETE |
| `validation_top_100_potential.csv` | v1 validation | 9.6 KB | DELETE |
| `validation_top_100_uplift.csv` | v1 validation | 9.2 KB | DELETE |
| `poi_coverage_summary_full.png` | POI coverage chart | 64 KB | KEEP |
| `.gitkeep` | placeholder | 1 B | KEEP |

**Total to delete: ~73 MB. This alone could push the repo zip over 100 MB.**

## `Results/` — 4 prediction CSVs, only 1 should exist

| File | Type | Action |
|---|---|---|
| `smil_labs_predictions.csv` | **canonical** | **KEEP** |
| `smil_labs_predictions_full_20000.csv` | duplicate (run_pipeline.py writes it) | MOVE to _legacy/ or delete |
| `smil_labs_predictions_full_20000_v2.csv` | duplicate (notebook 22) | MOVE to _legacy/ |
| `smil_labs_predictions_v2.csv` | duplicate (notebook 22) | MOVE to _legacy/ |

---

# Reproducibility Audit

## Paths that will break on a judge's machine

| Path | File:Line | Issue | Fix |
|---|---|---|---|
| `RAW_DIR = ROOT.parent / "datastorm-7-0-rotaract"` | `run_pipeline.py:78` | Team-specific Kaggle path. Judge won't have it. | Add `if not RAW_DIR.exists(): raise FileNotFoundError(f"Place raw CSVs in {RAW_DIR}")` with clear instructions. |
| `POI_FEATURES_PARQUET` | `run_pipeline.py:86` | Optional — handled with `if exists` check. OK. | No fix needed. |
| `geopandas` / `pyrosm` on Windows | `requirements_v2.txt` | These need conda-forge on Windows, not pip. | Add comment in requirements_v2.txt. |

## Fresh clone test (simulated)

```
1. git clone <repo>
2. python -m venv .venv && source .venv/bin/activate
3. pip install -r requirements_v2.txt  ← passes (macOS); Windows needs conda-forge note
4. Place raw CSVs in datastorm-7-0-rotaract/  ← unclear; needs better error
5. python run_pipeline.py  ← runs if CSVs present
```

---

# 30-Minute Cleanup Plan

```
[ ] 2 min  — Archive Docs/smil_labs_final_report.md -> Docs/_archive/
[ ] 5 min  — Delete 12 stale CSVs from data/gold/
[ ] 3 min  — Move 3 duplicate CSVs from Results/ to Results/_legacy/
[ ] 5 min  — Add clear FileNotFoundError to run_pipeline.py:78-79 for missing RAW_DIR
[ ] 5 min  — Add conda-forge comment to requirements_v2.txt for Windows geopandas
[ ] 5 min  — Remove duplicate write in write_submission() (write only canonical filename)
[ ] 5 min  — Add run_manifest.json write in main() with timestamp + git SHA + file hashes
[ ] Total: ~30 minutes
```

---

# Final Repo Zip Inclusions/Exclusions

**INCLUDE:**
- `src/` (all .py files)
- `Notebooks/` (20/21/22/23 v2 notebooks + v1 reference notebooks)
- `poi_pipeline/` (scripts + output/)
- `Reviews/` (all council rounds)
- `Reports/` (final_report.md + figures/)
- `Docs/` (challenge_brief, methodology, transparency logs — NOT smil_labs_final_report.md)
- `research/` (research brief + channels)
- `Results/` (smil_labs_predictions.csv + validation_report.md + manski_bands_v2.csv + conformal_intervals_v2.csv)
- `requirements_v2.txt`, `requirements.txt`, `README.md`, `SUBMISSION_CHECKLIST.md`
- `run_pipeline.py`

**EXCLUDE:**
- `data/` (runtime artifacts, regenerated by pipeline)
- `venv/` (virtual environment)
- `Datasets/` (raw CSVs, >100 MB)
- `.git/`
- `Results/_legacy/` (v1 backups)
- `Docs/_archive/` (stale docs)
- `__pycache__/`, `.pyc` files

---

# Strengths

- **B/S/G separation is real and on-disk.** Bronze copies + SHA-256 audit, Silver parquets + rejected CSVs, Gold feature parquet. All produced by `run_pipeline.py`.
- **DQ checks are genuinely reusable.** 6 functions with parameterized signatures, applied to 5 datasets, producing `QualityResult` dataclasses with `failure_reason`.
- **POI pipeline is idempotent and offline.** Geofabrik PBF download → pyrosm parse → BallTree search. No live API calls. ~25 min wall-clock.
- **The constraint score rebuild is methodologically sound.** PCA + frontier-residual + plateau gate — no DQ flags, no rank-sum double-counting.
- **SHA-256 provenance is now correct.** Full 64-char hash in `ingestion_audit.csv`.

---

# Grade vs DE Rubric

| | Now | After 30-min cleanup |
|---|:---:|:---:|
| DE rubric /10 | **8.0** | **9.0** |
| File hygiene | 13 stale CSVs in gold/ | CLEAN |
| Reproducibility | RAW_DIR hardcoded | Clear error message |
| Prediction CSV count | 4 files | 1 canonical |
