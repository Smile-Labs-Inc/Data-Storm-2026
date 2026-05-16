# Gap Analyzer — Round 4 (Council R4 / Data Storm 7.0)

**Reviewer:** Competition Gap Analyzer
**Scope:** v2 deliverables vs official 40/40/20 rubric (cover-page-to-PDF, code, CSV)
**Bottom line up front:** the team is sitting at a _low B / mid-70s_ on paper but is **one accidental file pick away from disqualification** and the model is currently **failing two of its own auto-validations (V3b + V4)** — which is the single biggest score leak right now.

---

# TL;DR

- **Expected score today: ~66/100.** Heavy points are bleeding from **Criterion 7 (math/censoring)** because `validation_report.md` shows **V3b FAIL (27.92% predictions below historical_max)** and **V4 FAIL (median uplift = 1.000)** — the model is doing nothing for half the outlets, and the PDF (which claims "ALL PASS") contradicts the on-disk artifact.
- **Highest-ROI fix is not modeling, it's plumbing:** wire the POI features into the model (currently `poi_demand_score = 0` for every row in `model_validation_summary.md`), and fix `predict.py` to actually floor at `observed_max` so V3b + V4 pass. Together ≈ 90 min for ~+10 raw points.
- **The submission-file footgun is still live:** `Results/smile_labs_predictions.csv` still has `row_id` as its column header (instant DQ per the official PDF), `_v2.csv` is the correct one, and there are **five different prediction files** in `Results/`. If the team uploads the wrong one, the score is 0 regardless of everything else.

---

# Point-Deduction Map

Score guide: 10 = perfect / leader-board worthy; 5 = adequate, no critical gap; 0 = absent or broken.

| #   | Rubric criterion                                          | Weight | Current /10 | Why                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Cheapest single fix to lift it                                                                                                                                                                                                                                                        |
| --- | --------------------------------------------------------- | -----: | ----------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Bronze→Silver→Gold pipeline with rejected records store   |     4% |     **7.5** | `src/` modules exist, `run_pipeline.py` runs, `data/silver_rejected/` is **populated** (`transactions_history_rejected.csv` 644 KB, `outlet_coordinates_rejected.csv` 17 KB, `holiday_list_rejected.csv` 7.7 KB, `quality_summary.csv`). Two `_rejected.csv` files are 42 B (empty) — looks suspicious; either fix or delete.                                                                                                                                                                                          | 5 min: drop the 42 B empty rejected files; add a single-line `README` in `data/silver_rejected/` naming the schema.                                                                                                                                                                   |
| 2   | Reusable + parameterizable DQ checks applied consistently |     8% |     **7.0** | Six functions in `src/quality/checks.py` are documented in the PDF and signatures look reusable (`duplicate_check`, `null_check`, `range_check`, `domain_check`, `referential_integrity_check`, `geospatial_bounds_check`). Risk: judge will open the file and check that the **same** function is genuinely called from **multiple** ingestors — not redefined per dataset.                                                                                                                                           | 10 min: verify each check is called from ≥2 ingestors; if not, refactor the call site, not the function.                                                                                                                                                                              |
| 3   | Identified + neutralized legacy system artifacts          |     8% |     **8.0** | Strong: `Grocry→Grocery`, `Bakry→Bakery`, lowercase `small→Small`, missing `Outlet_Size→Unknown`, coord bounds (5.5–10 / 79–82.5), 4.9k non-positive volume rows, 4.7k non-positive bill rows, 93 holiday duplicates. Cited with exact counts in PDF §1.                                                                                                                                                                                                                                                               | 0 min — already a strength. Optional: add 1 screenshot of the rejected-records sample CSV to PDF.                                                                                                                                                                                     |
| 4   | Robust web-scraping / API pipeline for external POI       |     8% |     **8.0** | `poi_pipeline/` exists end-to-end. `poi_features.parquet` covers **19,760 / 20,000 outlets**, 9 categories, 63 features, **80.9% have ≥1 POI within 2 km**. Coverage report exists with honest "kades are sparse" disclosure. Approach (Geofabrik PBF + pyrosm + BallTree haversine, idempotent download) is clearly defensible.                                                                                                                                                                                       | 0 min — strong. Optional: add wall-clock timing to coverage report (judges love numbers).                                                                                                                                                                                             |
| 5   | Engineered features that isolate true market signals      |    12% |     **4.0** | **Critical leak.** `Docs/model_validation_summary.md` shows `poi_demand_score` is **0.0 across every row** (mean / median / 90 / 95 / 99 / max all 0). All POI–target correlations are blank/NaN. The pipeline computed 63 POI features but **none reach the model** — the most-judged 12-point criterion is being thrown away. `catchment_density_score` correlation with the prediction is only **0.03**.                                                                                                            | **90 min (top fix):** join `poi_pipeline/output/poi_features.parquet` into the gold table inside `run_pipeline.py` (and/or notebook 21), confirm `poi_demand_score > 0` for ≥80% of rows, re-run validation.                                                                          |
| 6   | Conceptualisation of "latent potential"                   |    20% |     **7.5** | PDF §3 frames it correctly as `y = min(true, constraint)` (Manski 2003), states the estimand is not point-identified, shows the DAG, and reports `[manski_lower, point, manski_upper]`. Solid narrative. Loses points only because the on-disk numbers don't yet match the claim.                                                                                                                                                                                                                                      | 0 min on the concept; the lift comes from making the numbers match (Fix #1 + #2 below).                                                                                                                                                                                               |
| 7   | Math/stat handling of missing target + censored data      |    20% |     **3.0** | **Single biggest bleed point.** `Results/validation_report.md` is currently `V3b FAIL (27.92% below historical_max)` and `V4 FAIL (median uplift = 1.000)`. Sensitivity sweep confirms it: every (quantile × scheme × cap) combo gives median uplift ≤ 1.022 and `% capped = 0.0%`. So the SFA / multi-q / CQR / CH-3 stack is in the code but **collapses to "predict ≈ historical_max" for ~half the outlets and below it for ~28%**. The PDF claims `[OK] V3b, [OK] V4` — judges will catch the mismatch instantly. | **30 min (cheapest hard fix):** in `predict.py`, change the final floor from `lower_bound` to `np.maximum(potential_raw, observed_max_monthly_liters)`. This is exactly R2's N1 that was supposed to be fixed — the v2 CSV shows it wasn't, on-disk. Rerun → V3b should jump to ≥99%. |
| 8   | Clear documentation of how/where/why LLMs were used       |     7% |     **8.0** | `Docs/ai_transparency_log_v2.md` is 7 KB, structured, and PDF §4 has a per-phase table covering research / audit / implementation / SFA derivation / POI design / report drafting + a "what we did NOT use AI for" section. Cleanest area in the submission.                                                                                                                                                                                                                                                           | 0 min — already strong.                                                                                                                                                                                                                                                               |
| 9   | AI used intelligently as accelerator                      |     7% |     **8.0** | Three rounds of parallel council reviews (4 critics × 3 rounds), research swarm, Cursor IDE scaffolding. Provenance trail is real.                                                                                                                                                                                                                                                                                                                                                                                     | 0 min.                                                                                                                                                                                                                                                                                |
| 10  | Critical evaluation of AI-generated outputs               |     6% |     **9.0** | Each round found bugs in the previous round's fixes (R2 caught N1–N4 created by R1's fixes; R3 caught N1–N5 created by R2's fixes). That **is** critical evaluation, on the record. Loses 1 point only because R3 itself flagged 5 surviving bugs and the team hasn't shown a R3-fix log yet.                                                                                                                                                                                                                          | 5 min: add a `Reviews/council_round3/r3_fix_log.md` checking off N1–N5 status.                                                                                                                                                                                                        |

## Weighted score

| Rubric block              | Weight |              Avg /10 inside block |  Weighted points |
| ------------------------- | -----: | --------------------------------: | ---------------: |
| DE & Forensics (#1–5)     |     40 | (7.5+7.0+8.0+8.0+4.0)/5 = **6.9** |         **27.6** |
| Methodology & Math (#6–7) |     40 |            (7.5+3.0)/2 = **5.25** |         **21.0** |
| GenAI Workflow (#8–10)    |     20 |        (8.0+8.0+9.0)/3 = **8.33** |         **16.7** |
| **Total expected today**  |        |                                   | **~65–67 / 100** |

---

# Top 3 ROI Fixes

Ranked by **(expected score lift) / (hours of work)**.

|  Rank | Fix                                                                                                             |                                                                                                                          Score lift |          Time |                 ROI (pts/hr) | What to do                                                                                                                                                                                                                                                                                                                                        |
| ----: | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------: | ------------: | ---------------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1** | **Fix `predict.py` to floor at `observed_max`** (clear V3b + V4)                                                |                                                         **+10 to 12 raw pts** (Crit 7 jumps from 3 → 7; PDF claim matches artifact) |    **30 min** |                      **~22** | In `src/modeling/predict.py`, replace the `lower_bound` floor with `np.maximum(potential_raw, df["observed_max_monthly_liters"].fillna(df["lower_bound"]))`. Rerun notebook 22 → verify `Results/validation_report.md` shows V3b ≥ 99%, V4 median ∈ [1.05, 2.5]. Update PDF only after the report file actually says PASS.                        |
| **2** | **Wire `poi_features.parquet` into the model** (Crit 5 goes from "POI is plumbing-only" to "POI drives signal") | **+5 to 8 raw pts** (Crit 5 jumps from 4 → 7; modest lift in Crit 7 because POI gives the constraint score something real to score) | **60–90 min** |                       **~6** | In `run_pipeline.py` (or notebook 21 gold step), join `poi_pipeline/output/poi_features.parquet` on `Outlet_ID` BEFORE feature scaling. Confirm `poi_demand_score > 0` for ≥80% of rows in the next `model_validation_summary.md`. Then re-train q90 + SFA — the 0.03 catchment correlation should rise.                                          |
| **3** | **Submission-file hygiene** (rename + quarantine v1 files)                                                      |                                                                           **+0 to +3 raw pts** but **prevents –100** (DQ avoidance) |    **10 min** | **infinite (negative-tail)** | (a) `mv Results/smile_labs_predictions.csv Results/_legacy/v1_row_id_914rows.csv`; (b) `cp Results/smile_labs_predictions_v2.csv Results/smile_labs_predictions.csv`; (c) `mv Results/smile_labs_predictions_full_20000.csv Results/_legacy/`; (d) `head -1` the surviving file and confirm header is exactly `Outlet_ID,Maximum_Monthly_Liters`. |

> **Net of all 3:** ~+15 raw points in ~2 hours of work → score moves from **~66 → ~81** with the same model architecture, same POI scrape, same report. The lift is almost entirely _plumbing and renaming_.

---

# Ship-Or-Fix Decision Matrix

### If submission must happen in **the next 1 hour**

**Do Fix #3 (10 min) + Fix #1 (30 min). Ship.**

- Rename the CSV and quarantine v1 (saves the comp).
- Patch the `predict.py` floor → rerun → confirm V3b/V4 PASS → upload.
- **Do NOT touch POI wiring or constraint-score weights** — they need a full pipeline rerun and risk new failures.
- **Do regenerate the PDF** (or at minimum, edit the "auto-validation passes" verbatim block to match the _actual_ `validation_report.md`). Submitting a PDF that claims PASS when the artifact says FAIL is the second-worst outcome after DQ.
- Expected score: **~72–75**.

### If submission must happen in **the next 6 hours**

**Do Fixes #3 + #1 + #2 + rebuild the PDF from real numbers.**

- All of the 1-hour plan, plus:
- Wire POI features (90 min), rerun pipeline, regenerate `model_validation_summary.md`.
- Re-knit the PDF (`pandoc` or whatever the team uses) so headline numbers come from `Results/run_summary.json` of the new run, not placeholders / stale numbers.
- Fix the two 42-byte empty rejected CSVs (5 min, optical fix).
- Add the R3-fix log (5 min).
- Expected score: **~78–82**.

### If submission must happen in **the next 12 hours**

**All of the 6-hour plan, plus tighten methodology:**

- Verify R3 N1 (CQR calibration overlap), R3 N2 (SFA leakage no-op), R3 N3+N4 (manski.py cap merge + point-clip bug) are actually fixed in the v2 notebooks — these are quiet bugs that a hostile judge with a debugger will find.
- Run the sensitivity sweep with POI in-model and confirm the `% capped = 0.0%` flat-line goes away.
- Manually audit the **top-10 highest-uplift outlets** + the **bottom-10 lowest-uplift outlets** and put 1 paragraph in the PDF (judges love this).
- Tighten V4 range from `[1.05, 2.5]` to `[1.25, 2.2]` per R3 — but only after the POI wire-in actually moves the median uplift above 1.25.
- Expected score: **~83–87**.

**Hard rule for all three windows:** _NO new methods_. Every fix is "make what's already documented actually run".

---

# The One Unforced-Error Risk

> **`Results/` currently has FIVE prediction-looking files. The default-named one (`smile_labs_predictions.csv`) is the broken v1 with `row_id` as the column header and 914 rows. If anyone — judge, teammate, or upload-script — picks that file, the team is auto-disqualified per the official PDF schema requirement (`Outlet_ID, Maximum_Monthly_Liters`, 20,000 outlets in scope).**

This is unforced because:

- It was already R1 blocker B1+B2.
- It was reported FIXED in R2.
- R3 explicitly flagged "STILL has `row_id` + 914 rows … NOT TOUCHED".
- It is **still not touched today**, three rounds later.

**Mitigation (10 minutes, do this first):**

```powershell
# from Results/
mkdir _legacy 2>$null
Move-Item smile_labs_predictions.csv _legacy/v1_row_id_914rows.csv
Move-Item smile_labs_predictions_full_20000.csv _legacy/
Copy-Item smile_labs_predictions_v2.csv smile_labs_predictions.csv
Get-Content smile_labs_predictions.csv -TotalCount 2   # MUST print Outlet_ID,Maximum_Monthly_Liters
(Get-Content smile_labs_predictions.csv).Count          # MUST print 20001
```

Until those two assertions hold, **nothing else matters**.

---

# Final Expected Score

| Scenario                                                                                          | DE&F /40 | Method /40 | GenAI /20 | **Total /100** |
| ------------------------------------------------------------------------------------------------- | -------: | ---------: | --------: | -------------: |
| **Today, as on disk**                                                                             |     27.6 |       21.0 |      16.7 |        **~65** |
| After the 1-hour plan (Fix #1 + #3)                                                               |     27.6 |   **29.0** |      16.7 |        **~73** |
| After the 6-hour plan (+ Fix #2 + PDF rebuild)                                                    | **31.6** |   **31.0** |      16.7 |        **~79** |
| After the 12-hour plan (+ R3 N1–N5 closeout + audit paragraph)                                    | **33.0** |   **33.5** |  **17.5** |        **~84** |
| Ceiling if team also re-fits with POI in constraint score and tightens V4 to [1.25, 2.2] honestly |       34 |         35 |        18 |        **~87** |

The path from **65 → 84** is **plumbing, not modeling**. The single biggest mistake the team can make in the next 12 hours is starting a new method instead of finishing the four they already documented.
