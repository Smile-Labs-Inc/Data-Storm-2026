# TL;DR

1. Grade: B now; A- after one canonical v2 handoff.
2. The v2 notebooks tell one coherent story; the package still tells two.
3. The v1 PDF says Overpass, 914 rows, row_id, old lower bound, and rank-sum constraint score.
4. The v2 story says Geofabrik or POI-if-present, 20,000 rows, Outlet_ID, robust lower bound, frontier gap, Manski, and validation.
5. The stack overshot: keep POI plus Manski plus one XGBoost q90 frontier plus constraint score.
6. Notebook 22 writing a v2 file is safe during QA and risky at final upload.
7. The one move: make Notebook 22 the canonical release gate and report source of truth.

# Coherence Re-grade

Verdict: v2 alone tells one story. v1 plus v2 still tell two competing stories.

The v2 notebooks now form a coherent latent-demand architecture:

    observed sales are censored lower bounds
    -> Bronze/Silver/Gold data pipeline
    -> optional POI catchment features
    -> robust lower bound
    -> censored q90 frontier
    -> residual / plateau / PCA constraint score
    -> bootstrap cap
    -> Manski lower / point / upper band
    -> 20,000-row Outlet_ID submission

That is one story. It is much stronger than Round 1.

The package is not one story yet because the old v1 PDF and the old default CSV still point to the earlier method. That is a viva risk. A judge can ask which method produced the uploaded file, and the current materials give two answers.

| Team v1 PDF claim | v2 support or contradiction | Verdict |
|---|---|---|
| Final output is Results/smil_labs_predictions.csv. | Notebook 22 writes Results/smil_labs_predictions_v2.csv and does not overwrite v1. Current visible Results/smil_labs_predictions.csv starts with row_id. | Contradicted operationally. |
| Platform output has 914 rows. | Notebook 22 targets 20,000 rows. | Contradicted. Use 20,000 unless portal gives an official 914-row template. |
| Submission column is row_id. | Notebook 22 asserts Outlet_ID. | Contradicted. v2 is right. |
| Historical sales are censored demand. | Notebook 21 implements censoring correction and Manski bands. | Supported and strengthened. |
| Bronze/Silver/Gold exists. | Notebook 20 implements it. | Supported in code, but generated artifacts are absent until run. |
| Rejected records exist. | Notebook 20 writes them, but the inspected folder only had .gitkeep. | Supported by code, not by disk evidence. |
| 20,000 outlets and 2,376,389 transactions. | Notebook 20 reads outlet master and transactions. | Supported if raw data is present and Notebook 20 runs. |
| Dirty-data counts are 196 missing sizes, 600 lowercase small, 390 Grocry, 395 Bakry, 240 invalid coordinates, 9,606 bad transactions. | Notebook 20 should reproduce these. | Keep only if rerun output confirms them. |
| POI came from Overpass; 9,581 POIs; 902 target rows. | v2 report says Geofabrik PBF; Notebook 20 only merges poi_features.parquet if present. | Contradicted. Delete the Overpass story. |
| Lower bound is max of historical max, January max, recent 3-month max. | Notebook 21 uses robust lower bound and floors final prediction at observed max. | Contradicted. Remove v1 formula. |
| Constraint score includes coordinate availability and rank-sum components. | Notebook 21 uses frontier residual plus plateau plus PCA. | Contradicted. Remove old score. |
| v1 validation metrics: mean 445.34 L, median 259.77 L, median uplift 1.18x. | Notebook 21 prints new v2 metrics, but no v2 results were present in the inspected tree. | Legacy only. Do not use in v2 report. |
| AI usage was for research, modeling, POI workflow, debugging, validation, and drafting. | v2 council and notebooks support this. | Supported, but the log must mention the v2 cutover. |

Bottom line: methodology is no longer the main blocker. Source-of-truth control is.

# Notebook-Report Alignment Matrix

This walks the 5-page Reports/final_report.md.

| Report section or claim | v2 notebook artifact | Alignment | Fix before final PDF |
|---|---|---|---|
| Cover: 20,000 outlets, Jan 2026 horizon, latent potential. | Notebook 20 loads outlet master; Notebook 22 writes 20,000-row v2 submission. | Good if run. | Remove any 914-row language. |
| One-line method: sales are right-censored. | Notebook 21 builds censoring proxy, frontier, and Manski bands. | Strong. | Keep as the spine. |
| Headline uplift numbers. | Notebook 21 prints uplift summary. | Weak until run output exists. | Paste actual final-run values only. |
| Six validation checks pass. | Notebook 22 calls run_validation_suite. | Weak until validation artifact exists. | Do not claim PASS before running 22. |
| Bronze to Silver to Gold. | Notebook 20 creates Bronze audit, Silver Parquet, and Gold features. | Strong in code. | Run it and include artifacts. |
| Reusable DQ checks. | Notebook 20 imports and applies duplicate, null, range, domain, referential, and geospatial checks. | Strong. | Say checks are applied where relevant. |
| Rejected-record store. | Notebook 20 writes rejected files. | Strong in code, absent on disk now. | Include generated rejected CSVs or summary. |
| Geofabrik POI pipeline. | Notebook 20 consumes poi_features.parquet; POI scripts produce it. | Partial. | State whether POI was present in the final run. |
| 9 POI categories and about 63 POI columns. | POI pipeline output then Notebook 20 merge. | Conditional. | Do not claim counts without output. |
| Manski non-identification. | Notebook 21 writes Manski bands. | Strong. | Keep. |
| DAG figure. | Notebook 22 calls build_dag. | Good if run. | Use one simple DAG figure. |
| Robust lower bound. | Notebook 21 calls robust_lower_bound. | Strong. | Remove v1 max-of-max formula. |
| Multi-quantile XGBoost. | Notebook 21 calls fit_multi_quantile. | Strong. | Make q90 the main frontier. |
| SFA blend. | Notebook 21 calls fit_sfa and blends if it works. | Real but too much. | Demote or cut from main report. |
| CH censoring correction. | Notebook 21 calls chernozhukov_hong_correction. | Strong. | Describe as a frontier training filter. |
| Constraint score. | Notebook 21 calls build_constraint_score. | Strong. | Keep; call it an index. |
| Bootstrap caps. | Notebook 21 writes cap_table_v2; Notebook 22 validates cap binding. | Strong. | Keep. |
| CQR interval. | Notebook 21 writes conformal intervals. | Overcomplete. | Cut unless final coverage is strong. |
| Sensitivity sweep. | Notebook 22 writes sensitivity table. | Good if run. | Cite actual output only. |
| Top-100 audits. | Notebook 22 writes top potential and uplift audits. | Good if run. | Use one sanity chart if useful. |
| Submission file. | Notebook 22 writes v2 CSV. | Correct schema, risky naming. | Create a final upload copy. |
| AI transparency. | v2 report has a stronger AI table. | Mostly aligned. | Update log to mention v2 cutover. |

# Minimal Stack Check

R2 recommended POI plus Manski plus one frontier plus calibrated constraint score.

v2 includes that. It also adds SFA, CQR, censored QR, sensitivity, DAG, and caps. That is too much for a 5-page report.

Keep:

- POI features.
- Manski bounds.
- One main frontier: CH-filtered XGBoost q90.
- Rebuilt constraint score.
- Bootstrap caps as guardrails.

Demote:

- CH correction: describe it as a training detail.
- SFA: keep as robustness only.

Cut from the main PDF:

- CQR, unless actual coverage output is strong and space remains.

Clean final formula:

    potential_i = max(observed_max_i, lower_bound_i + score_i * (frontier_q90_i - lower_bound_i))
    then cap by bootstrap peer bucket
    then report Manski lower / point / upper

That is the story judges can remember.

# 5-min Viva Pitch (3 slides)

## Slide 1 - Observed sales are not demand

Chart: scatter plot of observed_max versus v2 predicted potential, colored by constraint_score, with the diagonal prediction equals observed_max.

Point: the model never goes below demonstrated capability and only lifts outlets when frontier gap and constraint evidence agree.

## Slide 2 - POI and catchment explain upside

Chart: Sri Lanka map or hexbin of outlets colored by uplift ratio, with POI or catchment density overlay.

Point: upside is not random. It appears where external footfall and internal catchment support latent demand. If POI did not run, say so and show internal catchment only.

## Slide 3 - The upload is guarded

Chart: validation dashboard with six green checks plus a small sensitivity band chart.

Show 20,000 rows, Outlet_ID, no NaN, no negatives, no duplicates, historical-max floor, cap-binding below threshold, and median uplift in range.

Do not pitch SFA math. Do not pitch CQR math. Do not spend slide time on every typo fix.

# Submission Policy Review

Notebook 22 writes Results/smil_labs_predictions_v2.csv and Results/smil_labs_predictions_full_20000_v2.csv. It does not overwrite Results/smil_labs_predictions.csv.

Verdict: safe during development, risky for submission.

This was the right comparison policy while v2 was being tested. It is not the right final-hour policy. The old file has the familiar name and starts with row_id,Maximum_Monthly_Liters. The team can upload it by habit.

Final policy:

1. Keep smil_labs_predictions_v2.csv as the audit copy.
2. Create Results/FINAL_UPLOAD.
3. Copy v2 into that folder as smil_labs_predictions.csv.
4. Put only the final upload CSV in that folder.
5. Add a README saying upload only Results/FINAL_UPLOAD/smil_labs_predictions.csv, with schema Outlet_ID,Maximum_Monthly_Liters and 20,000 rows.

If the portal proves 914 rows are required, filter v2 to the official template IDs. Do not resurrect the old row_id file.

# The One Move

Make Notebook 22 the canonical release gate.

It should run validation, write v2 artifacts, write the final upload folder, write a method manifest, print the exact upload path, and print row count, schema, and hash.

The manifest should include final row count, schema, POI presence, SFA status, CQR status, validation pass/fail, paths to Manski, sensitivity, DAG, top-100 audits, and exact claims allowed in the final report.

This one change lifts the grade highest because it collapses code, report, and upload behavior into one source of truth.

# The One Thing to Avoid

Do not touch the core v2 prediction formula unless validation fails.

The working spine is good:

    observed lower bound
    -> censored q90 frontier
    -> residual / plateau / PCA constraint score
    -> bootstrap cap
    -> Manski band

Do not add DEA. Do not add Heckman. Do not add causal forests. Do not tune weights to chase a nicer uplift number.

Cut claims. Do not add methods.
