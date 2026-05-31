# Gap Analyzer — Council Round 6 (Data Storm 7.0)

**Reviewer:** Competition Gap Analyzer (R6)
**Scope:** v2 deliverables vs 40/40/20 rubric — post-R5 fixes audit
**Validation state going in:** 6/6 PASS (`validation_report.md` confirmed)
**Bottom line:** R5 fixed the `run_pipeline.py` bugs and filled report placeholders. But **3 R5 TODOs remain undone**, `Docs/smile_labs_final_report.md` is still visible with ghost methods, `data/gold/` has 13 stale CSV files, and `Results/` has 4 duplicate prediction CSVs. The EDA charts are on disk but not in the report. The model is sound but the packaging is still B+ territory.

---

# Expected Score Today (post-R5, pre-R6 fixes)

| Rubric block              | Weight | Score /10 |  Weighted pts | Notes                                                                                                                                                                 |
| ------------------------- | -----: | --------: | ------------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DE & Forensics (#1–5)     |     40 |       8.0 |      **32.0** | run_pipeline.py clean; SHA-256 full; TEAM_NAME correct. Lost pts: stale CSVs in gold/, 4 prediction CSVs in Results/, smile_labs_final_report.md still visible        |
| Methodology & Math (#6–7) |     40 |       7.8 |      **31.2** | SFA+multi-q+CH-3+Manski stack running. Lost pts: V4 at knife edge (1.250), CH-3 no-op not disclosed in report, EDA charts not wired, sfa_converged not in run_summary |
| GenAI Workflow (#8–10)    |     20 |       8.0 |      **16.0** | ai_transparency_log_v3.md created (R3+R4 logged). Lost pts: R5 not in transparency log, README council trail complete but transparency log incomplete                 |
| **Total today**           |        |           | **~79 / 100** |                                                                                                                                                                       |

---

# New Issues Found in R6 (not present in R5)

## N6.1 [HIGH] `Docs/smile_labs_final_report.md` — R5 said archive it, still present

R5 T1.3 explicitly said "Archive to `Docs/_archive/`". The file is still at `Docs/smile_labs_final_report.md` with:

- Line 13: `| Median uplift vs historical max | 1.18x |` (wrong — should be 1.250)
- Line 6: `"...Tobit Type-I MLE..."` — ghost method, no `tobit.py` in `src/modeling/`
- Different method claims than what the code actually does

This is the single highest credibility risk. A judge who opens `Docs/` sees two conflicting reports.

**Fix:** Move to `Docs/_archive/smile_labs_final_report_v1.md`. Already documented in R5, just wasn't executed.

## N6.2 [HIGH] `data/gold/` has 13 stale CSV files — v1 artifacts + diagnostics

```
outlet_features.csv (6.2 MB) — v1 duplicate of .parquet
outlet_features_v2.csv (9.6 MB) — v2 duplicate of .parquet
outlet_monthly_sales.csv (39.1 MB) — v1 intermediate
outlet_poi_features.csv (220 KB) — v1 POI
outlet_poi_features_full.csv (10.1 MB) — v1 POI full
poi_cleaned.csv (605 KB) — v1 POI cleaned
prediction_diagnostics.csv (4.7 MB) — diagnostic dump
validation_extreme_uplift.csv (137 B) — diagnostic
validation_missed_opportunity.csv (4.8 KB) — diagnostic
validation_top_100_potential.csv (9.6 KB) — v1 validation
validation_top_100_uplift.csv (9.2 KB) — v1 validation
```

Total: ~73 MB of stale files. The repo zip limit is 100 MB. These are gitignored but will be in the zip if not cleaned. R4 Tier 2 said to delete these — not done.

**Fix:** Delete all CSV files in `data/gold/` except `.gitkeep` and `.png` files. Parquets are canonical.

## N6.3 [MEDIUM] `Results/` has 4 duplicate prediction CSVs

```
smile_labs_predictions.csv (361 KB) — canonical
smile_labs_predictions_full_20000.csv (361 KB) — duplicate
smile_labs_predictions_full_20000_v2.csv (361 KB) — duplicate
smile_labs_predictions_v2.csv (361 KB) — duplicate
```

The `write_submission()` function at `run_pipeline.py:368-371` writes BOTH `{TEAM_NAME}_predictions.csv` AND `{TEAM_NAME}_predictions_full_20000.csv`. The `_v2.csv` and `_full_20000_v2.csv` are from notebook 22 runs. Having 4 files with the same row count but potentially different content is the exact "5 prediction files" footgun R3 flagged.

**Fix:** Keep only `smile_labs_predictions.csv`. Move others to `Results/_legacy/`. Modify `write_submission()` to write only one file OR document why the full version exists.

## N6.4 [MEDIUM] EDA charts not wired into `Reports/final_report.md`

R5 T2.2 said to add 3 figure inserts. Not done. The 10 EDA charts at `Reports/figures/eda_*.png` are invisible to judges reading the PDF. The report has no `\includegraphics` references.

**Fix:** Add figure references in Sections 1-3 of `Reports/final_report.md`:

1. `eda_cooler_saturation.png` in §1 (cooler knee at 3)
2. `eda_poi_outlet_type.png` in §2 (honest POI framing)
3. `eda_top100_sanity.png` in §3 (top-100 uplift sanity)

## N6.5 [MEDIUM] `ai_transparency_log_v3.md` ends at R4 — R5 not logged

The log covers R1-R4. R5 found 12 new issues and applied critical fixes (run_pipeline.py bugs, report placeholders). Not logging R5 leaves ~1-2 GenAI rubric points on the table.

**Fix:** Add R5 entry to `ai_transparency_log_v3.md` following the R4 format.

## N6.6 [LOW] `sfa_converged` not in `run_summary.json`

R5 T3.3 not done. The `main()` function at `run_pipeline.py:440-447` writes `run_summary.json` with `elapsed_sec`, `submission`, `median_uplift`, `mean_uplift`, `max_uplift` — but no `sfa_converged`. If SFA fails to converge, the report can't mention it.

**Fix:** Add `sfa_converged` field to the summary dict. Requires passing `sfa_fit` through to `main()`.

## N6.7 [LOW] CH-3 no-op language not updated in report

R5 T3.1 not done. `Reports/final_report.md` §3 still claims "q90 is re-fitted on rows where P(censored) < 0.10" — but in practice 100% of rows are kept because the censoring proxy is single-class. The R5 Modeling Diagnostician provided exact replacement language.

**Fix:** Replace the CH-3 paragraph in `Reports/final_report.md` with the honest framing from R5.

---

# ROI-Ranked Fix Priority

| Rank | Fix                                      |               Score lift |   Time |       ROI |
| ---: | ---------------------------------------- | -----------------------: | -----: | --------: |
|    1 | N6.1: Archive smile_labs_final_report.md |      +1 pt (credibility) |  2 min | 30 pts/hr |
|    2 | N6.2: Delete stale gold CSVs             | +0.5 pt (DE cleanliness) |  5 min |  6 pts/hr |
|    3 | N6.3: Clean up duplicate prediction CSVs |             +0.5 pt (DE) |  5 min |  6 pts/hr |
|    4 | N6.4: Wire 3 EDA charts into report      |     +2 pts (Methodology) | 20 min |  6 pts/hr |
|    5 | N6.5: Add R5 to transparency log         |            +1 pt (GenAI) | 10 min |  6 pts/hr |
|    6 | N6.7: Update CH-3 report language        |        +0.5 pt (honesty) |  5 min |  6 pts/hr |
|    7 | N6.6: Add sfa_converged to run_summary   |     +0.5 pt (provenance) | 10 min |  3 pts/hr |

**Total: ~+5-6 raw points, ~1 hour of work → 79 → ~84-85.**

---

# Ship-Or-Fix Decision Matrix

### If < 30 minutes to submission

Fix N6.1 only. Archive the stale report. Do NOT touch code.

### If 1–2 hours to submission

Fix N6.1-N6.5. Clean gold CSVs, clean Results CSVs, wire 3 EDA charts, update transparency log. Rebuild PDF.

### If 3+ hours to submission

All of the above + N6.6 + N6.7. Add sfa_converged, update CH-3 language. Rebuild PDF. Do NOT open new method tracks.

---

# The One Unforced-Error Risk

**`Docs/smile_labs_final_report.md` is still visible.** It claims 1.18× uplift and "Tobit Type-I MLE" — a method that doesn't exist in the codebase. If a judge opens `Docs/` and finds two conflicting reports, the credibility damage is severe and irreversible. This was flagged in R5 and not actioned. Fix it now.

---

# Expected Score After R6 Fixes

| Scenario                     |   DE /40 | Method /40 | GenAI /20 |   Total |
| ---------------------------- | -------: | ---------: | --------: | ------: |
| Now (post-R5)                |     32.0 |       31.2 |      16.0 | **~79** |
| After N6.1-N6.5 (1 hour)     | **33.5** |   **33.0** |  **17.0** | **~84** |
| After all R6 fixes (2 hours) | **34.0** |   **33.5** |  **17.5** | **~85** |
