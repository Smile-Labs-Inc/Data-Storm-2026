# TL;DR

- **BLOCKER:** Page 5 has a visible overflow: the reproducible-codebase deliverable runs off the right edge. The LaTeX log confirms an **Overfull hbox 98.6524pt too wide** at lines 432--434.
- **MAJOR:** The report invites the "you tuned the answer to pass validation" attack. Median uplift is exactly **1.250**, the validation lower bound is **1.25**, and the method explicitly adds a **1.25x uplift floor**.
- **MAJOR:** The PDF avoids three facts a hard judge will ask for: SFA fit diagnostics (`sigma_u`, `sigma_v`, `lambda`), actual CQR empirical coverage, and the team's own EDA finding that POI signal is near zero (`|r| <= 0.026`).

# Last-Minute Disaster Check (10 items, severity-tagged)

1. **BLOCKER -- Uploading the wrong CSV or stale v1 artifact.**  
   **Manifestation:** Platform gets an old `smil_labs_predictions.csv`, stale v1 PDF, or docs with row_id / 1.18x claims.  
   **5-min fix:** Keep only `Reports/final_report_v3.pdf` and `Results/smil_labs_predictions.csv` in the upload staging folder. Re-open both immediately before upload.

2. **BLOCKER -- Page 5 text is visibly clipped.**  
   **Manifestation:** In `final_report_v3_p-5.png`, the notebook path in the final bullet runs past the right edge. Log says `Overfull \hbox (98.6524pt too wide) in paragraph at lines 432--434`.  
   **5-min fix:** Replace the long notebook chain with shorter text: `Notebooks 20 -> 21 -> 22; modules in src/`, or use `\path{}` / smaller font / manual line break.

3. **MAJOR -- Page 1 has no visible page footer.**  
   **Manifestation:** Pages 2--5 show `2 of 5` ... `5 of 5`; page 1 is `\thispagestyle{empty}` and the PNG has no visible `1 of 5`. If judges inspect page numbering, this looks inconsistent.  
   **5-min fix:** Remove `\thispagestyle{empty}` or add a manual centered `1 of 5` footer on the cover.

4. **MAJOR -- The 1.250 median looks engineered.**  
   **Manifestation:** Page 1 says median uplift **1.250x**. Page 5 says validation accepts `[1.25, 2.2]` and reports **median = 1.250**. A judge can say the model was tuned to just hit the pass threshold.  
   **5-min fix:** Reword as a transparent conservative business floor, not a discovered statistical median. Be ready to explain why 1.25 was chosen.

5. **MAJOR -- SFA is named but not evidenced.**  
   **Manifestation:** Methodology claims SFA MLE, but the report gives no `sigma_u`, `sigma_v`, `lambda`, convergence flag, or log-likelihood. A stats judge can ask whether SFA actually identified a one-sided inefficiency term.  
   **5-min fix:** Add one compact parenthetical: `SFA converged; sigma_u=..., sigma_v=..., lambda=...` if values are available. If not, soften SFA from "frontier evidence" to "auxiliary frontier component."

6. **MAJOR -- CQR is claimed but empirical coverage is not quoted.**  
   **Manifestation:** Page 4 says calibrated `[q05, q95]`; page 5 says `90% target coverage`. The file has only `Outlet_ID,cqr_lower,cqr_upper`, not a coverage summary.  
   **5-min fix:** Add `calibration empirical coverage = X%` from the CQR result, or remove "calibrated" from the visible claim.

7. **MAJOR -- POI story can be attacked with the team's own EDA.**  
   **Manifestation:** Page 3 sells 42,386 POIs and 63 columns. Round 4 EDA says per-type POI correlation is `[-0.026, 0.008]`; all effectively zero.  
   **5-min fix:** Add one sentence: "POI is used as weak catchment context, not a standalone demand predictor."

8. **MAJOR -- Validation report column order conflicts with actual CSV.**  
   **Manifestation:** Actual CSV header is `['Outlet_ID', 'Maximum_Monthly_Liters']`; `validation_report.md/json` prints sorted columns as `['Maximum_Monthly_Liters', 'Outlet_ID']`. The PDF uses the actual order.  
   **5-min fix:** Change validation detail to preserve `list(submission.columns)` instead of `sorted(actual_cols)`, or ignore if no rebuild is possible.

9. **MINOR -- Several ugly line breaks make the report look rushed.**  
   **Manifestation:** Page 1 has "cate-gories"; page 2 splits "mandatory fields"; page 3 table wraps category labels hard; page 5 references are tiny.  
   **5-min fix:** Abbreviate labels and reduce table text. Do not try a full redesign now.

10. **MAJOR -- Repo/package reproducibility can fail under inspection.**  
    **Manifestation:** PDF says every claim traces to artifacts and code is reproducible, but judges may run a notebook and hit Windows geospatial dependency pain (`pyrosm`, `geopandas`) or missing generated summaries.  
    **5-min fix:** Add a short `RUN_THIS_FIRST.txt` or README note with exact venv, build, and validation commands. Do not make judges infer the path.

# PDF Technical Issues

- **Page numbers / footers:** Pages 2--5 have visible centered footers (`2 of 5` through `5 of 5`). Page 1 has no visible footer because the TeX uses `\thispagestyle{empty}`. This is not fatal, but it is inconsistent with "correct on every page."

- **Orphans, widows, bad line breaks:** The severe issue is page 5: the reproducible-codebase bullet overflows and is visually clipped. Confirmed by LaTeX log: `Overfull \hbox (98.6524pt too wide) in paragraph at lines 432--434`. Minor ugliness: "cate-gories" on page 1, cramped table wrapping on pages 2--3, and very small references on page 5.

- **TOC:** No TOC is fine. With a 5-page hard constraint, a TOC would waste space and hurt the submission. The section numbering is clear enough.

- **Refs / cites:** No visible `??` in the rendered PNGs or extracted PDF text. The LaTeX log has no undefined-reference or undefined-citation warning. Hyperref warnings are bookmark-string cleanup, not unresolved refs.

- **Hyperlinks:** TeX uses `colorlinks=true` with blue-ish internal links and green citations. The PDF binary has link markers (`/Subtype /Link`, `/GoTo`) and no external URI actions. The citation colors are visible but not jarring. There are no useful external clickable URLs in the final PDF.

# Number Consistency Check

- **20,000 outlets:** Consistent. Page 1 says 20,000. Page 5 says 20,000 rows. Python check on `Results/smil_labs_predictions.csv` gives **20,000 data rows**, 20,001 total CSV rows including header.

- **Median uplift 1.250:** Consistent but dangerous. Page 1 says **1.250x**. Page 5 says **median = 1.250**. `validation_report.json` says `median_uplift=1.250`.

- **6/6 PASS:** Consistent. Page 1 says **6 / 6 PASS**. Page 5 table has all six OK rows. `validation_report.json` has `"all_passed": true`.

- **42,386 POIs:** Consistent. Page 1 says **42,386**. Page 3 total row says **42,386**.

- **Rejected records:** Consistent. Page 1 says `480 + 9,606 + 93`; page 2 table has `240 coords + 4,853 volume + 4,753 bill + 93 holidays`, which sums to **10,179** and matches the figure box.

- **POI coverage:** Consistent. Page 1 says **80.9%**. Page 3 total row says **80.9%**.

- **Potential mismatch:** Page 5 PDF says schema order `[Outlet_ID, Maximum_Monthly_Liters]`, actual CSV matches that. But `validation_report.md/json` prints the sorted set as `['Maximum_Monthly_Liters', 'Outlet_ID']`. This is not a data failure, but it is an artifact mismatch.

- **Actual CSV sanity check:** Header is `['Outlet_ID', 'Maximum_Monthly_Liters']`; duplicate IDs = 0; NaN = 0; negative predictions = 0; first ID `OUT_00001`; last ID `OUT_20000`; bad ID pattern count = 0.

# 5 Hostile Questions the PDF Invites

1. **"Did you tune the model to pass your own validation, since the median is exactly 1.250 and your lower bound is 1.25?"**  
   **Why invited:** Page 4 explicitly says constrained outlets receive a `1.25x` uplift floor. Page 5 validates median uplift in `[1.25, 2.2]` and reports `1.250`.  
   **Defensible answer:** "The 1.25x is a conservative business floor for outlets flagged as constrained, bounded by empirical peer-bucket caps. We should not call it a learned median."

2. **"Where are the SFA fit diagnostics?"**  
   **Why invited:** The report names SFA and MLE, but gives no fitted `sigma_u`, `sigma_v`, `lambda`, convergence flag, standard errors, or likelihood.  
   **Defensible answer:** "SFA is one component in a 60/40 ensemble and not the only source of uplift. The code records the fields; the PDF omitted them for space." Weak answer unless the values are ready.

3. **"If POI correlation is near zero, why do you spend a whole page on POI?"**  
   **Why invited:** Page 3 sells POI volume, 63 features, and 80.9% coverage. Round 4 EDA says `|r| <= 0.026` by outlet type.  
   **Defensible answer:** "POI is not a direct demand predictor. It is a weak catchment context signal and a data-acquisition rubric requirement. The strongest signals remain observed history, outlet attributes, frontier residuals, and constraints."

4. **"What is the empirical CQR coverage?"**  
   **Why invited:** Page 4 says calibrated CQR. Page 5 says 90% target coverage. The final PDF never quotes empirical coverage or quantile correction.  
   **Defensible answer:** "The calibration object computes empirical coverage on the held-out set; we omitted the number from the 5-page version." Bad if the number cannot be produced immediately.

5. **"How can you claim robustness when the sensitivity sweep median uplift is only [1.000, 1.022] but the submitted median is 1.250?"**  
   **Why invited:** Page 5 says sweep medians stay `[1.000, 1.022]`, while the headline prediction median is `1.250`. That sounds like the model is robustly no-uplift until the manual floor is applied.  
   **Defensible answer:** "The sweep tests frontier/scheme/cap sensitivity before the constrained-outlet policy floor. The floor is separate and should be labelled as such."

# What the PDF Conspicuously Avoids

- **Actual SFA fit values:** The code defines `sigma_v`, `sigma_u`, `lambda_`, `log_likelihood`, and `converged`, but the PDF does not report them. This is the most obvious missing methodology detail.

- **CQR empirical coverage:** `src/modeling/conformal.py` computes `empirical_coverage` and `quantile_correction`, but `Results/conformal_intervals_v2.csv` only has `Outlet_ID`, `cqr_lower`, and `cqr_upper`. The PDF says "90% target coverage" but avoids the actual achieved coverage.

- **POI weak-signal result:** Round 4 EDA found `poi_catchment_score` vs observed volume correlations: Bakery `-0.021`, Eatery `-0.007`, Grocery `0.001`, Hotel `0.000`, Kiosk `0.008`, Pharmacy `-0.026`, SMMT `-0.016`. The PDF says POI is a catchment signal but does not disclose the near-zero empirical signal.

- **Censoring rarity:** Round 4 EDA says only **232 / 20,000 = 1.16%** outlets show a real plateau fingerprint. The PDF leans heavily on right-censoring and CH-3; a judge may ask whether this is methodological theater for a small subset.

- **Why the floor threshold is `cs >= 0.40`:** The PDF states the threshold but does not justify it. That leaves the team exposed to "why not 0.35 or 0.50?"

# The Single Statement Most Likely to Backfire

> **"Outlets with `cs >= 0.40` receive a `1.25x` uplift floor over `observed_max`; the floor is bounded by the bucket cap."**

This is the live grenade. It explains exactly why the median lands on **1.250**, which is also the validation lower bound. A hostile judge can frame the whole submission as a rule-based uplift floor dressed as SFA + CQR.

**Safer wording:**  
"For outlets with strong constraint evidence, we apply a conservative policy floor of 1.25x over historical max, bounded by empirical peer-bucket caps. We report this transparently as a decision rule, not as a purely learned effect."

# Pre-Submission Preflight (10 items)

1. Open `Reports/final_report_v3_p-5.png` and fix the clipped reproducible-codebase line before upload.
2. Decide whether page 1 needs a visible `1 of 5` footer. If yes, remove `\thispagestyle{empty}` and rebuild.
3. Re-run the PDF build and scan `final_report_v3.log` for `Overfull`, `undefined`, `Citation`, and `Reference`.
4. Open the final PDF, not just the TeX, and search visually for `??`, clipped text, and weird citation coloring.
5. Re-check `Results/smil_labs_predictions.csv`: exactly 20,000 rows, exact header `Outlet_ID,Maximum_Monthly_Liters`, no blank final row.
6. Confirm the platform wants only two columns. Do not upload the full business CSV by mistake.
7. Keep a one-line answer ready for the 1.25x floor: "transparent conservative policy floor, not a learned median."
8. Have SFA diagnostics ready in notes: `sigma_u`, `sigma_v`, `lambda`, convergence flag, log-likelihood.
9. Have CQR calibration notes ready: empirical coverage, alpha, calibration-set size, quantile correction.
10. Have POI caveat ready: 42,386 POIs prove acquisition robustness; POI is weak direct signal and only used as catchment context.
