# TL;DR

- **Submission blocker:** `Results/teamname_predictions.csv` has 914 rows and uses `row_id`; the official brief requires `Outlet_ID, Maximum_Monthly_Liters` for the 20,000-outlet scope. Use `Results/teamname_predictions_full_20000.csv`, rename `row_id` to `Outlet_ID`, then re-check row count and uniqueness.
- **DE rubric blocker:** `src/**/*.py` is empty and `data/**/*.csv` is absent in the current tree. The notebook can generate Silver rejected files, but the submitted codebase does not visibly prove a reusable Bronze -> Silver -> Gold pipeline or rejected records store.
- **Forensics risk:** DQ checks exist inside `Notebooks/01_latent_potential_pipeline.ipynb`, but the rubric asks for reusable, parameterizable checks. Move these functions into `src/quality/quality.py` and call them from the notebook or a small pipeline script.

# Verdict

**D+ today, B- after a minimal DE refactor.** The team has strong forensic findings and working outputs, but the current submission CSV format and empty `src/` folders are high-risk against the 40% Data Engineering & Forensics rubric.

# Submission CSV Audit

Official expected columns are stated in `Docs/challenge_brief.md:65-72`. The current README contradicts this by documenting `row_id` and a 914-row validator fallback in `README.md:74-79`.

| check | expected | actual | fix |
| --- | --- | --- | --- |
| Deliverable file | `Results/teamname_predictions.csv` | Exists, but only 914 rows | Replace it with the 20,000-row output unless an official template proves otherwise. |
| Column names | `Outlet_ID`, `Maximum_Monthly_Liters` | `row_id`, `Maximum_Monthly_Liters` in both `Results/teamname_predictions.csv:1` and `Results/teamname_predictions_full_20000.csv:1` | Rename `row_id` to `Outlet_ID` before final export. |
| Row count | 20,000 outlets per `Docs/challenge_brief.md:15-18`; research brief says the 914-row assumption is unverified in `research/research_brief.md:37-40` | `teamname_predictions.csv`: 914 rows. `teamname_predictions_full_20000.csv`: 20,000 rows | Make the 20,000-row file the official deliverable. Keep any 914-row file only if an official competition template is provided. |
| Unique row keys | 20,000 unique `Outlet_ID` values | 914 unique keys in deliverable; 20,000 unique keys in full file | Re-run uniqueness after the column rename. |
| NaN values | No NaN in either column | 0 NaN in both files | Good. Keep pre-flight check. |
| Negative values | No negative `Maximum_Monthly_Liters` | 0 negatives in both files; current full-file min is 84.153 | Good. Keep pre-flight check. |
| Numeric prediction dtype | Parseable numeric liters | Parseable numeric values in the sampled heads | Good. Add an explicit `pd.to_numeric(..., errors="raise")` check before writing. |

Notebook source of the bug: `Notebooks/01_latent_potential_pipeline.ipynb:603-629` renames `Outlet_ID` to `row_id`, writes the full file with that name, then falls back to the first 914 sorted IDs when no template exists.

# Codebase Refactor Plan

Current structure problem: `Docs/folder_structure.md:117-184` says `src/` is reserved for future reusable code, and Glob found **0 Python files** under `src/**/*.py`. That is a direct rubric risk because `Docs/challenge_brief.md:74-80` asks for a reproducible codebase with cleaning, POI acquisition, feature engineering, modeling, and final prediction code.

Minimal refactor target:

```text
src/
  ingestion/
    bronze.py
  quality/
    quality.py
  cleaning/
    silver.py
  features/
    outlet_features.py
    catchment_features.py
  poi/
    osm_poi.py
  modeling/
    latent_potential.py
    submission.py
  reporting/
    data_quality_report.py
```

Move notebook cells as follows:

| notebook logic | move to | reason |
| --- | --- | --- |
| Path constants, source file map, valid domains | `src/config.py` | One source of truth for file names, valid distributors, domains, random seed. |
| Bronze copy and checksum functions | `src/ingestion/bronze.py` | Satisfies exact raw-copy Bronze layer from `Docs/challenge_brief.md:39-47`. |
| `QualityResult`, `duplicate_check`, `null_check`, `range_check`, `domain_check`, `referential_integrity_check`, `collect_rejections`, `write_layer` | `src/quality/quality.py` | Turns inline checks into reusable, parameterizable functions. |
| Dataset-specific cleaning for outlets, coordinates, transactions, seasonality, holidays | `src/cleaning/silver.py` | Makes Silver rules auditable and repeatable. |
| Monthly sales aggregation and internal catchment features | `src/features/outlet_features.py` and `src/features/catchment_features.py` | Keeps Gold feature engineering separate from modeling. |
| Geofabrik/Overpass POI extraction and BallTree catchment features | `src/poi/osm_poi.py` | Directly addresses the external POI rubric item in `Docs/challenge_brief.md:103-112`. |
| Frontier model, constraint score, caps, diagnostics | `src/modeling/latent_potential.py` | Makes the latent-potential method testable. |
| Final CSV writing and validation | `src/modeling/submission.py` | Prevents repeat of `row_id` / 914-row submission bugs. |
| Markdown DQ report generation | `src/reporting/data_quality_report.py` | Keeps docs generated from reusable outputs, not hidden notebook state. |

Keep the notebook as an orchestration and narrative layer, but make it import and call `src/` functions. A judge should be able to inspect `src/` and see Bronze -> Silver -> Gold separation without opening notebook JSON.

# DQ Checks Reusability Plan

The current DQ report says it is generated from the notebook in `Docs/data_quality_report.md:1-3`, and the check results are useful. The implementation should be lifted from `Notebooks/01_latent_potential_pipeline.ipynb:150-224` into a real module, with a small check-spec interface per dataset. This preserves current behavior while satisfying "reusable, parameterizable, consistently applied" from `Docs/challenge_brief.md:49-61`.

```python
# src/quality/quality.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class QualityResult:
    name: str
    valid_mask: pd.Series
    failure_reason: str


def duplicate_check(df: pd.DataFrame, key_columns: list[str]) -> QualityResult:
    mask = ~df.duplicated(subset=key_columns, keep="first")
    return QualityResult("duplicate_check", mask, f"Duplicate key on {', '.join(key_columns)}")


def null_check(df: pd.DataFrame, columns: list[str]) -> QualityResult:
    mask = pd.Series(True, index=df.index)
    for column in columns:
        values = df[column]
        if pd.api.types.is_string_dtype(values) or values.dtype == object:
            mask &= values.astype("string").str.strip().ne("").fillna(False)
        else:
            mask &= values.notna()
    return QualityResult("null_check", mask, f"Null or empty mandatory field in {', '.join(columns)}")


def range_check(
    df: pd.DataFrame,
    column: str,
    min_value: float | None = None,
    max_value: float | None = None,
    inclusive: bool = True,
) -> QualityResult:
    values = pd.to_numeric(df[column], errors="coerce")
    mask = values.notna()
    if min_value is not None:
        mask &= values.ge(min_value) if inclusive else values.gt(min_value)
    if max_value is not None:
        mask &= values.le(max_value) if inclusive else values.lt(max_value)
    return QualityResult("range_check", mask, f"{column} outside expected range")


def domain_check(df: pd.DataFrame, column: str, allowed_values: set[str]) -> QualityResult:
    mask = df[column].astype("string").str.strip().isin(allowed_values)
    return QualityResult("domain_check", mask, f"{column} contains a value outside the allowed domain")


def referential_integrity_check(
    df: pd.DataFrame,
    column: str,
    reference_values: Iterable[str],
) -> QualityResult:
    mask = df[column].astype("string").isin(set(reference_values))
    return QualityResult("referential_integrity_check", mask, f"{column} does not exist in reference dataset")


def collect_rejections(
    df: pd.DataFrame,
    dataset_name: str,
    checks: list[QualityResult],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    combined_valid = pd.Series(True, index=df.index)
    rejected_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []

    for check in checks:
        valid = check.valid_mask.reindex(df.index).fillna(False).astype(bool)
        failed = ~valid
        combined_valid &= valid
        summary_rows.append(
            {
                "dataset_name": dataset_name,
                "check_name": check.name,
                "failed_records": int(failed.sum()),
                "failure_reason": check.failure_reason,
            }
        )
        if failed.any():
            rejected = df.loc[failed].copy()
            rejected.insert(0, "failure_reason", check.failure_reason)
            rejected.insert(0, "failed_check", check.name)
            rejected.insert(0, "dataset_name", dataset_name)
            rejected_frames.append(rejected)

    rejected_df = pd.concat(rejected_frames, ignore_index=True, sort=False) if rejected_frames else pd.DataFrame()
    return df.loc[combined_valid].copy(), rejected_df, pd.DataFrame(summary_rows)
```

# Rejected Records Store Verification

`Docs/data_quality_report.md:35-43` claims rejected files exist, including `outlet_coordinates_rejected.csv` with 480 rows and `transactions_history_rejected.csv` with 9,606 rows. In the current repository tree, Glob found **0 CSV files** under `data/**/*.csv`, so `data/silver_rejected/` is not present as evidence in the submitted codebase.

The notebook **will write** rejected files when it runs: `Notebooks/01_latent_potential_pipeline.ipynb:220-224` writes each `{dataset_name}_rejected.csv`, and `Notebooks/01_latent_potential_pipeline.ipynb:340-371` writes `quality_summary.csv` and reports counts from the rejected folder.

Two safety issues remain:

- The generated rejected files are ignored by `.gitignore` in `data/silver_rejected/*.csv` at `.gitignore:17-20`. If the final zip/GitHub repo excludes them, judges only see claims, not the rejected records store.
- The report counts rejected rows per failed check, not necessarily unique source records. `Docs/eda_summary.md:79-91` says there are 240 invalid coordinate rows, but `Docs/data_quality_report.md:41` reports 480 coordinate rejects because latitude and longitude checks each add rows. `Docs/eda_summary.md:101-104` says 4,853 transaction rows fail the positive volume or bill check, while `Docs/data_quality_report.md:43` reports 9,606 rejected rows. Add `source_row_id` and a `failed_checks` list so one bad source record is quarantined once with all reasons.

Recommendation: keep rejected CSVs generated, but force-include the small `data/silver_rejected/*_rejected.csv` files in the final submission zip, or update `.gitignore` to allow these audit artifacts while still ignoring large Bronze/Silver/Gold data.

# Submission Pre-flight Checklist

| item | yes/no today | required action |
| --- | --- | --- |
| `Results/teamname_predictions.csv` exists | Yes | Replace contents with official 20,000-row output. |
| Deliverable uses `Outlet_ID` | No | Rename `row_id` to `Outlet_ID`. |
| Deliverable has `Maximum_Monthly_Liters` | Yes | Keep exact spelling. |
| Deliverable has 20,000 rows | No | Use `teamname_predictions_full_20000.csv` as source. |
| Row keys are unique | Yes for both current files | Re-check after final export. |
| No NaN values | Yes | Add automated assertion before write. |
| No negative predictions | Yes | Add automated assertion before write. |
| `src/` contains runnable modules | No | Add minimal modules listed in the refactor plan. |
| Rejected records are written to `data/silver_rejected/` | Yes when notebook runs; No in current tree | Generate and include audit files or document exact regeneration command. |
| README explains raw data reproduction | Partial | Add exact source filenames, expected path, run command, and expected output files. |
| Requirements cover current notebook imports | Mostly | Current imports are covered, but POI/model upgrades need more packages. |
| GenAI log is per-session and validation-backed | No | Convert static table into running log entries. |

# GenAI Log Discipline

The current log in `Docs/ai_transparency_log.md:5-16` is a static area summary. It is helpful, but the 20% GenAI rubric will be stronger if it becomes a phase-by-phase audit trail.

Use one entry per AI session or major phase:

```markdown
## YYYY-MM-DD HH:MM - Phase name

- Goal:
- Prompt / AI request:
- Files or data used:
- AI output accepted:
- AI output rejected or changed:
- Human validation run:
- Resulting artifact paths:
- Remaining risk:
```

Minimum phases to log:

- Challenge parsing and rubric extraction.
- Bronze/Silver/Gold pipeline design.
- DQ check design and validation.
- EDA and anomaly interpretation.
- POI acquisition design.
- Model method selection.
- Submission CSV validation.
- Final PDF/report drafting.

# Reproducibility Score

| dimension | grade | fix |
| --- | --- | --- |
| Dependency pinning | B | `requirements.txt` is pinned (`pandas==2.3.3`, `numpy==2.2.6`, `scikit-learn==1.7.2`, `openpyxl==3.1.5`). Add any POI/model packages once used. |
| Current notebook import coverage | B | `Notebooks/01_latent_potential_pipeline.ipynb:41-47` imports pandas, numpy, and sklearn modules covered by requirements. `Notebooks/02_full_dataset_eda.ipynb:18-21` also uses only pandas/numpy. |
| Future POI coverage | D | Research recommends Geofabrik PBF + `pyrosm`, `geopandas`, and BallTree in `research/research_brief.md:90-121`. Add `pyrosm`, `geopandas`, `shapely`, `pyproj`, `rtree` or `pyogrio`, and document the PBF snapshot URL/date. |
| Future model coverage | C | If adding XGBoost, MAPIE, SFA, LightGBM, or geopy, pin them. Do not import them in notebooks before updating requirements. |
| Raw data availability | C | `.gitignore:28-29` excludes `Datasets/`, which is reasonable for size, but README must state exact filenames, expected row counts, and checksums if possible. |
| Generated layer reproducibility | C | README says the notebook creates Bronze/Silver/Gold outputs in `README.md:65-72`, but no command-line script exists. Add `src/run_pipeline.py` or clear notebook execution instructions with expected outputs. |
| Bronze integrity | B- | Notebook copies raw files with `shutil.copy2` and SHA-256 audit, but `row_count = len(pd.read_csv(target))` reads full files and can be slow. Use a chunked row counter or record metadata after copy. |
| Encoding and dtype hygiene | C- | Reads use default `pd.read_csv(...)` in `Notebooks/01_latent_potential_pipeline.ipynb:243-321` and `Notebooks/02_full_dataset_eda.ipynb:46-50`. Add `encoding="utf-8-sig"`, explicit dtypes for IDs/categories, and numeric downcasts for the 2.37M-row transaction table. |
| Memory/scale safety | C | `Docs/eda_summary.md:16-24` reports 514.9 MB for raw transactions alone. Multiple pandas copies, joins, groupbys, and rejected-frame concatenation can multiply this into several GB. Fine on many 16 GB laptops, but risky if notebooks keep old cells in memory. Use categorical dtypes, selected columns, `float32`, chunked reads for audit, and Parquet for Silver/Gold. Use Polars for transaction aggregation if memory spikes. |

# POI Pipeline Safety Requirements

The research brief correctly prefers offline Geofabrik PBF over live Overpass calls in `research/research_brief.md:27` and `research/research_brief.md:90-121`. The `src/poi/osm_poi.py` module should include:

- Idempotent download/extract paths, with existing snapshot reuse unless `FORCE_REFRESH = True`.
- Snapshot date, source URL, file size, and checksum logged to `data/bronze/poi_snapshot_audit.csv`.
- Offline-first Geofabrik PBF flow; Overpass only as a small fallback, never 20,000 outlets times many categories.
- Rate-limit, retry with backoff, timeout, and user-agent if Overpass fallback is used.
- POI dedup by OSM ID, category, latitude, longitude, and name.
- Category mapping kept in one config dict, with report-friendly labels.
- Sri Lanka bounding-box validation and CRS handling.
- NaN-safe output for outlets with invalid coordinates or empty catchments: counts = 0, weighted scores = 0, nearest distance = `2 * max_radius_km`, and a `poi_coverage_flag`.
- Separate cannibalisation features from demand features. Same-type nearby outlets should not be blindly treated as positive catchment demand.
- Output to `data/silver/poi_features.parquet` or `data/gold/poi_features.parquet` with one row per `Outlet_ID`.

# Strengths

- The challenge brief is clean and aligned with the official rubric; `Docs/challenge_brief.md:39-61` captures Bronze/Silver/Gold, reusable DQ checks, and rejected records clearly.
- The EDA is strong: it profiles all 20,000 outlets and 2,376,389 transactions, and it identifies real legacy artifacts such as `small`, `Grocry`, `Bakry`, invalid coordinates, and non-positive transaction values in `Docs/eda_summary.md:5-14`.
- The notebook already has the core reusable DQ functions in one place; moving them into `src/quality/quality.py` is a small refactor, not a rewrite.
- Bronze ingestion uses raw copies and SHA-256 audit logic, which is a good forensic control once documented and exposed through `src/ingestion/bronze.py`.
- The research brief gives a practical POI path: Geofabrik PBF + local spatial features, which is safer and more scalable than live Overpass scraping.
