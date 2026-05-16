# Statistician — Round 3 review (v2 notebooks 20→21→22)

**Reviewer:** Statistician (council R3).
**Targets:** `Notebooks/20_v2_data_pipeline.ipynb`, `Notebooks/21_v2_modeling.ipynb`, `Notebooks/22_v2_validation_and_submission.ipynb`, plus the `src/modeling/*` and `src/reporting/manski.py` modules they call.
**Compared to:** R1 master `Reviews/council_review.md`, R2 master `Reviews/council_round2/council_review_v2.md`.

---

## TL;DR

- All four R2 N-blockers (N1–N4) are **mechanically fixed** in the modules and called correctly from NB21. R1 M1–M5 are likewise fixed in code. The plumbing is real this time.
- The headline "**median uplift 1.4–1.7×**" target will **not** be hit. NB21 floors `potential_raw` at `observed_max_monthly_liters` (correctly, to pass V3b) but the multi-quantile q90 frontier is fitted on a target that is itself `observed_max`. For the median outlet, `frontier_q90 ≈ observed_max`, so the floor binds and uplift collapses to ≈ 1.0. Expected median uplift end-to-end: **1.05–1.20×**.
- Two new issues neutralise the methodology theatre claim: (a) the CH-3 censoring proxy threshold (`>0.3` of months) is so strict that <20% of outlets are flagged, so the propensity filter keeps almost all rows and q90 stays effectively uncorrected; (b) the SFA frontier is fitted on the same right-censored target without any censoring correction, then ensembled 60/40 with q90 — the 40% SFA contribution is also biased downward, and the ensemble is reported as the headline frontier while the sensitivity sweep silently uses XGB-only.

---

## 1. Verification table for R1 + R2 issues

Cell indices are 0-based as they appear in the `.ipynb` JSON (matches the order in the Read tool output).

| Issue                                                               | Status      | Notebook + cell                                                                                                                     | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **R1 M1** quadruple throttling                                      | **FIXED**   | NB21 cell 19 → `latent_potential` in `src/modeling/predict.py`                                                                      | `predict.py:56-64` is `lower_bound + cs * gap` with a single floor and a single bucket cap via `apply_caps`. No `**1.25`, no `clip(0,0.65)`, no `peer_p98 * 1.35`, no `4.5x size cap` chain.                                                                                                                                                                                                                                                                |
| **R1 M2** `constraint_score` has DQ flag                            | **FIXED**   | NB21 cell 15 → `build_constraint_score` in `src/modeling/constraint_score.py`                                                       | `constraint_score.py:92-132` builds sigmoid of (0.5·frontier_residual_z + 0.3·plateau_signal·1.5 + 0.2·(−capacity_pc1)). `valid_coordinate_rank` does not appear anywhere in the module. NB21 cell 15 also prints `mean constraint_score by Outlet_Size` as a hostile-judge sanity check (good).                                                                                                                                                            |
| **R1 M3** `lower_bound` dominated by `historical_max`               | **FIXED**   | NB21 cell 3 → `robust_lower_bound` in `src/modeling/lower_bound.py`                                                                 | `lower_bound.py:32-58` returns 3rd-highest month, or own p95 when fewer than 6 active months, with a `max(.., median)` floor. NB21 cell 3 also reports the `lower_bound / observed_max` ratio — that diagnostic is honest.                                                                                                                                                                                                                                  |
| **R1 M4** q90 fitted on capped sales                                | **PARTIAL** | NB21 cells 6–7 (proxy + CH-3) → `chernozhukov_hong_correction` in `src/modeling/censored_qr.py`                                     | The CH-3 module exists and is called. **But:** NB21 cell 7 aggregates to outlet level via `delta_per_month.groupby("Outlet_ID")["delta"].mean() > 0.3` — the per-month proxy itself fires only on 3-month-stuck-at-95% or 6-month-flat-within-5% (`censored_qr.py:65-74`), then needs >30 % of months to fire. In practice this flags very few outlets, so `propensity_threshold=0.10` keeps almost all rows and the q90 fit barely moves. See NEW issue 2. |
| **R1 M5** no validation / sensitivity / robustness                  | **FIXED**   | NB22 cells 5, 7, 9 → `run_validation_suite`, `sensitivity_sweep`, `build_dag`                                                       | All three are wired and write artifacts to `Results/` and `Reports/figures/`.                                                                                                                                                                                                                                                                                                                                                                               |
| **R2 N1** `predict.py` floors below `historical_max` (V3b breakage) | **FIXED**   | NB21 cell 19 → `predict.py:59-64`                                                                                                   | `historical_max = df["observed_max_monthly_liters"].fillna(df["lower_bound"])`, then `df["potential_raw"] = np.maximum(df["potential_raw"], historical_max)`. V3b will pass by construction — but see NEW issue 1 for the side effect.                                                                                                                                                                                                                      |
| **R2 N2** `manski_lower < observed_max`                             | **FIXED**   | NB21 cell 23 → `compute_manski_bands` in `src/reporting/manski.py:41-48`                                                            | `manski_lower = np.maximum(lower_bound.fillna(0), observed_max_monthly_liters.fillna(0))`. Correct Manski floor for right-censored data.                                                                                                                                                                                                                                                                                                                    |
| **R2 N3** SFA target leakage from `observed_p90/p95/median/mean`    | **FIXED**   | NB21 cell 11 explicitly removes `leaky_cols = {observed_mean, observed_median, observed_p90, observed_p95}` from `sfa_feature_cols` | The check is in fact vacuous in NB21 because `base_features` in cell 5 already excludes those columns — so `leaky_cols ∩ feature_cols = ∅`. The intent is correct and the safeguard is defensive. Confirmed no `observed_*_monthly_liters` enters `sfa_X`.                                                                                                                                                                                                  |
| **R2 N4** CQR module not wired                                      | **FIXED**   | NB21 cell 21 → `conformalised_qr` in `src/modeling/conformal.py`                                                                    | Calibration set built via `split_by_outlet` (group-level holdout, no leakage), test interval `[cqr_lower, cqr_upper]` written to `Results/conformal_intervals_v2.csv`. The reported `empirical_coverage` is the calibration-set coverage (good honesty).                                                                                                                                                                                                    |

**Bottom line:** every R1 + R2 issue is at least PARTIAL, and seven of nine are fully FIXED. The remaining PARTIAL (M4) is the one that quietly determines the headline number.

---

## 2. NEW issues found in v2 notebooks 20→21→22

Severity tags: **BLOCKER** (will visibly hurt the report or fail validation), **MAJOR** (real statistical defect, hides bias), **MINOR** (cosmetic / audit-trail / efficiency).

### Issue 1 — Floor at `observed_max` mechanically collapses median uplift to ≈ 1.0 **[BLOCKER for headline narrative]**

NB21 cell 19 produces `potential_raw = lower_bound + constraint_score * (frontier_q90 − lower_bound)` then floors at `observed_max_monthly_liters` (`predict.py:64`). The XGBoost q90 target is itself `observed_max_monthly_liters` (NB21 cell 5: `y = gold["observed_max_monthly_liters"]`), so for the **median outlet** `E[frontier_q90 | X] ≈ observed_max`. Then `gap = frontier − lower_bound ≈ observed_max − 0.8·observed_max = 0.2·observed_max`, `cs ≈ 0.5`, so `potential_raw ≈ 0.9·observed_max` → **the floor binds** → `potential_capped = observed_max` → `uplift_ratio = 1.00`.

Uplift > 1 only for outlets where `frontier_q90 ≫ observed_max` (i.e. the model thinks this small outlet's X looks like a large outlet's X). With the (very strict) CH-3 filter this is a minority of outlets.

**Fix options:** (i) compute `q90` on the **uncensored subset only** with a much LOOSER censoring proxy (per-month `delta` should fire when `volume ≥ 0.90·max for 2+ months`, and outlet-level should be `mean(delta) > 0.10`), (ii) or fit q90 against a **peer-frontier target** (e.g. `max(y, peer_q95_of_y_given_X)`) so the model is anchored on a frontier rather than the outlet's own cap, (iii) or relax V3b to `predicted ≥ lower_bound` so the floor doesn't force uplift = 1 on half the population. Note V3b at 99 % is the team's own self-imposed validation — the brief does not demand it.

### Issue 2 — CH-3 censoring proxy threshold is too strict, neutralising M4 **[MAJOR]**

`censored_qr.py:64-74` requires either (a) `v[i] >= 0.95·max_v` for **3 consecutive months** _or_ (b) `i >= 6` and `|v[i] − roll_mean[i]| / roll_mean[i] < 0.05` (a 6+-month plateau within 5 %). Then NB21 cell 7 aggregates: `is_censored_outlet = mean(delta) > 0.30`. With 12 active months that is `> 3.6` flagged months out of 12, i.e. effectively the stuck-at-95 % branch firing for at least 4 of the recent 9 months. Most outlets will not hit this, so very few outlets are passed to the propensity model, the logistic propensities are uniformly small, and `select_uncensored(p_censored < 0.10)` retains almost everything. **The CH-3 step is theatre with these defaults.**

**Fix:** loosen the per-month proxy to `v[i] >= 0.90·max_v` for `2+` consecutive months and drop the outlet-level `> 0.30` threshold (use the per-month `delta` directly inside `fit_propensity`, so propensities are graded rather than binarised twice). Report `n_uncensored_kept` — if it is > 90 % of `n_total`, CH-3 is doing nothing and the team should say so honestly.

### Issue 3 — SFA frontier uses the same right-censored target with no censoring correction **[MAJOR]**

NB21 cell 11 fits `fit_sfa(sfa_X, y=observed_max, log_target=True)`. SFA models inefficiency `u ≥ 0` but **not** right-censoring of the dependent variable. With `y` capped, the MLE drives `β_0` and the slope coefficients downward, and `sigma_u → 0` is a well-known collapse mode when the residuals are not asymmetric (the data look one-sided because of censoring, not inefficiency). Cell 11 prints `lambda = sigma_u/sigma_v` — **if lambda < 0.2 the SFA frontier collapses to OLS** and the second methodology track is fluff. Even when `lambda` is healthy, `predict_frontier` returns `expm1(X @ beta)` which is the log-conditional **median** in the natural scale, not the frontier; you want `exp(X @ beta + 0.5·sigma_v^2)` to back out the conditional mean of the noise-only model, and then the _frontier_ interpretation is `exp(X @ beta)` _only_ if you trust the inefficiency component to absorb censoring (it doesn't). The 60/40 ensemble in cell 13 therefore drags the headline frontier **down**.

**Fix:** either (i) fit SFA on the **uncensored subset** (same CH-3 filter, looser threshold) and disclose it, (ii) or replace the SFA contribution with a robust frontier proxy (peer p95 of y in (Outlet_Type, Outlet_Size) bucket) and rename it `peer_frontier`, (iii) or drop SFA from the headline ensemble and keep it as a _secondary efficiency diagnostic_ used only for the report's narrative about under-realisation. Currently the SFA "track" is a footnote masquerading as a co-headliner.

### Issue 4 — Sensitivity sweep silently uses XGB-only q90, not the headline 60/40 ensemble **[MAJOR]**

NB21 cell 13 overwrites `frontier["frontier_q90"]` with `0.6·XGB + 0.4·SFA` and that ensemble is what feeds `latent_potential` (cell 19). But NB22 cell 7 calls `sensitivity_sweep(..., multi_q_predictions=quantile_preds, ...)` where `quantile_preds` is the **pre-ensemble** XGB output (saved separately in cell 24 as `quantile_predictions_v2.parquet`). `sensitivity.py:46-52` then builds its own frontier from `multi_q_predictions[col]` only — the SFA contribution is dropped on the sensitivity floor. Result: the sensitivity table tells you how the prediction moves under XGB-only knob changes, while the headline uses XGB+SFA. **The two numbers are not the same model.**

**Fix:** either (a) save the ensemble q90 column (e.g. `ensemble_q90`) into `quantile_predictions_v2.parquet` and have `sensitivity_sweep` read that, or (b) re-fit the SFA inside the sweep at each (q, scheme, cap) combo (slow; not worth it). Option (a) is one extra column.

### Issue 5 — `_pca_capacity` orientation heuristic is fragile **[MINOR]**

`constraint_score.py:82-84` flips the PC sign using the single row at `X.shape[0] // 2`. That row may not have above-mean capacity, so the sign is essentially noise. R2 O4 already flagged this. Cell 15 includes a `mean constraint_score by Outlet_Size` print as a smoke test (so a flipped sign would be visible to a human), but the orientation should be deterministic.

**Fix:** sign the PC against `Cooler_Count` (or any other column known to be capacity-increasing): `pc *= np.sign(np.corrcoef(pc, X["Cooler_Count"])[0, 1] + 1e-12)`.

### Issue 6 — `write_silver` overwrites the QC-rejected CSVs from `write_rejected` **[MINOR-MEDIUM, audit-trail downgrade]**

NB20 cell 7 calls `write_rejected(qc, SILVER_REJECTED_DIR)` which writes `{dataset}_rejected.csv` from the QC check failures (with detailed `failed_check` and `failure_reason` per row). NB20 cell 11 then calls `write_silver(..., name="outlet_coordinates", rejected=coords_rej)` etc., which uses the same target filename and **overwrites**. The cleaning rejects are effectively a superset (so no rows are lost), but the granular per-check reason from the QC pass is replaced with a single generic reason like `"coordinate outside Sri Lanka bounds or null"`. A judge inspecting `silver_rejected/` will not see which DQ rule fired.

**Fix:** either (a) make `write_silver` write to `{name}_cleaning_rejected.csv` (different stem), or (b) merge `coords_rej` with the existing QC rejected file before write, preserving the QC `failed_check` column.

### Issue 7 — Coordinate teleport bug still present at modeling step **[MINOR]**

NB20 cell 0 advertises "Coordinate teleport bug fixed — invalid coords get NaN, not median imputation". `silver.py` does the right thing (NaN, not median). **But** NB21 cell 5 then does `X = X.fillna(X.median(numeric_only=True))` on the **full** feature matrix, which median-imputes `outlet_count_1km`, `outlet_count_2km`, `outlet_count_5km`, `catchment_density_score`, `nearest_outlet_distance_km` etc. for outlets with invalid coords. That is exactly the teleport behaviour the team claimed to have fixed — moved from cleaning into modeling.

**Fix:** add a `has_valid_coordinate` indicator feature to `gold` and either (a) drop median-imputed coordinate-derived columns for those rows and substitute peer-bucket medians, or (b) feed `has_valid_coordinate` to the monotone tree model so it can interact with the imputed values. At minimum, log how many rows are median-imputed in cell 17's NaN summary.

### Issue 8 — Notebook 22 never consumes the Manski or CQR side-outputs **[MINOR]**

NB21 cells 21 and 23 write `conformal_intervals_v2.csv` and `manski_bands_v2.csv`. NB22 never reads them. The team's claim in the README that "predictions are reported with `[manski_lower, point, manski_upper]`" needs the validation notebook to at least JOIN them into a single audit CSV. Right now they are orphan files.

**Fix:** add one cell to NB22 that merges `preds`, `manski_bands_v2.csv`, `conformal_intervals_v2.csv` on `Outlet_ID` and writes `Results/smile_labs_predictions_v2_with_bands.csv` for the report's appendix.

### Issue 9 — `january_holiday_count` is a CONSTANT **[MINOR]**

`gold.py:142-146` returns a single int from the full calendar. Every outlet gets the same value. NB20 cell 13 then stamps `january_holiday_count` again on every row with the same value. The feature has zero variance per outlet → it's an intercept shift inside XGBoost, which the model already has. It's not harmful but it is misleading to call it a per-outlet feature in cell 0 of NB20.

**Fix:** either drop it from `base_features` in NB21 cell 5, or replace with `holiday_count_in_next_30_days` keyed to each outlet's geographic locale (no Sri Lanka regional holidays exist by Outlet_ID so this requires the holidays table to have a region key — not available; just drop).

### Issue 10 — Monotone constraint direction for `nearest_outlet_distance_km` **[MINOR]**

`frontier.py:34-37` marks `nearest_outlet_distance_km` as `monotone_down`. The hypothesis is that **closer competitors lower the frontier**. That is competition logic. But the variable is the distance to the NEAREST OTHER OUTLET regardless of channel — including a same-distributor partner, which raises the frontier (logistics co-location, common in FMCG). The sign is **ambiguous** and probably should be 0 (let the tree decide).

**Fix:** set `nearest_outlet_distance_km` to 0 in `monotone_constraints` and add a NEW feature `nearest_competitor_distance_km` (filter to different Outlet_Type before the BallTree query) and mark that one `monotone_down` if you want the cannibalisation signal.

### Issue 11 — `cap_table["cap_uplift"].fillna(out["cap_uplift"].median() or 3.0)` order of evaluation **[MINOR]**

`caps.py:57`: `out["cap_uplift"].fillna(out["cap_uplift"].median() or 3.0)`. Python `or` returns the first truthy operand — if the median is `0.0` or `NaN`, the fallback `3.0` kicks in. With `min_cap = 1.5` enforced upstream this should never matter, but it is brittle. A bucket with literally 0 outlets becomes `cap = 3.0`, a hardcode that the team explicitly removed.

**Fix:** `cap_median = out["cap_uplift"].median(); out["cap_uplift"] = out["cap_uplift"].fillna(cap_median if pd.notna(cap_median) else 3.0)`.

### Issue 12 — `cap_binding_max_pct = 25.0` in V5 with `cap_threshold * 0.999` **[MINOR]**

`validation.py:117-119`: `capped = merged["Maximum_Monthly_Liters"] >= cap_threshold * 0.999`. With the floor-at-`observed_max` semantics from issue 1, many outlets land _exactly_ at `observed_max`, which is `< cap_threshold = cap_uplift × observed_max` whenever `cap_uplift > 1`. So V5 will almost certainly pass — but it is _measuring the wrong thing_ (it now measures "fraction of outlets where the bucket cap binds at the TOP") while issue 1 means the FLOOR binds at the bottom for many. The team needs a symmetric "floor-binding rate" check.

**Fix:** add V5b: `floor_binding_pct = mean(potential_capped ≈ observed_max within 0.1%)`. If V5b > 50 % the headline median uplift will be misleading; the report needs a frank disclosure.

---

## 3. End-to-end statistical sanity if a fresh kernel runs NB20 → NB21 → NB22

Will the numbers be consistent? **Yes** — paths line up, parquet schemas match, `Outlet_ID` is the join key everywhere, and there are no out-of-order-cell hazards. I traced these dependencies:

- NB20 writes `data/silver/{outlet_master,outlet_coordinates,transactions_history,holiday_list,distributor_seasonality}.parquet` and `data/gold/outlet_features.parquet`.
- NB21 reads `data/gold/outlet_features.parquet` and `data/silver/transactions_history.parquet`. Writes `data/gold/predictions_v2.parquet`, `data/gold/quantile_predictions_v2.parquet`, `data/gold/cap_table_v2.csv`, `Results/conformal_intervals_v2.csv`, `Results/manski_bands_v2.csv`.
- NB22 reads the four NB21 outputs plus `outlet_features.parquet`, `transactions_history.parquet`, `outlet_master.parquet`. No mismatched columns; `Maximum_Monthly_Liters` is created in `predict.py:92` and consumed correctly downstream.

**Predicted headline numbers** (no compute, model-anchored estimate):

| Metric                                      | Predicted           | Reasoning                                                                                                                                                                                                                                                                                                                                                                                                     |
| ------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Median uplift**                           | **1.05 – 1.20×**    | Floor-at-`observed_max` (issue 1) pins most outlets to uplift = 1.00 exactly. Only outlets where `frontier_q90 ≫ observed_max` (X-features look big but observed is small) escape the floor. With strict CH-3 (issue 2), q90 is only weakly corrected, so the "escape" population is roughly the 25–35 % of outlets with the largest peer-vs-self residual. The median itself will sit just barely above 1.0. |
| **Mean uplift**                             | **1.30 – 1.55×**    | Right-skewed by the 25–35 % of outlets in the escape population, which can have 1.5–3.0× uplift; capped at bucket `cap_uplift` (≤ 6×).                                                                                                                                                                                                                                                                        |
| **Max uplift**                              | **3 – 5×**          | Bounded by the bucket cap. With `bootstrap_size_type_caps(..., cap_quantile=0.95)` and `min_cap=1.5, max_cap=6.0`.                                                                                                                                                                                                                                                                                            |
| V3b (predicted ≥ historical max for ≥ 99 %) | **PASS at ~100 %**  | By construction; the floor guarantees it.                                                                                                                                                                                                                                                                                                                                                                     |
| V4 (median uplift in [1.05, 2.5])           | **Borderline PASS** | Predicted median 1.05–1.20 just clears the lower edge. If the CH-3 filter is even slightly more conservative than I estimate, V4 could land at 1.03 and **FAIL**. This is the single most fragile validation.                                                                                                                                                                                                 |
| V5 (cap-binding rate < 25 %)                | **PASS easily**     | Few outlets reach the bucket cap because the floor binds at the bottom, not the cap at the top. (This is _not_ a sign of model fit — it is a sign of issue 12.)                                                                                                                                                                                                                                               |
| V1 / V2 / V3a                               | **PASS**            | Schema correct, no NaN/neg/dups, deterministic outlet_master ordering.                                                                                                                                                                                                                                                                                                                                        |

If V4 fails on first run, the team will be tempted to lift `median_uplift_min` from 1.05 to 1.00. **Do not do this.** Instead fix issues 1 + 2 + 3 so the median uplift earns its way past 1.05 on real data.

---

## 4. Three deepest remaining concerns

1. **The model does not uplift the median outlet.** With the V3b floor in place and q90 ≈ observed_max for the median outlet, mathematical certainty says median uplift sits at 1.00 with a thin sliver above. The Skeptic's R1 prediction — _"why is your median uplift only ~1.2×? Are you actually uncapping anything?"_ — is still the right question in R3, and the answer is still _"only for the long-tailed 25–35 % of outlets whose X-features look big but whose history is short"_. This is a defensible result for those outlets but it does NOT match the team's headline narrative of broad-based latent-demand recovery.

2. **The "frontier" is the same target everywhere.** XGBoost q90, SFA `X @ β`, and `peer_q90` inside the constraint score (`constraint_score.py:27-29`) are all derived from `observed_max_monthly_liters` — three views of the same right-censored variable. There is no exogenous variation, no shadow-price proxy, no instrument. Manski-style bounds (the only methodologically clean answer) are computed in NB21 cell 23 but never surfaced in NB22 (issue 8). When a hostile judge asks _"what is your identifying assumption?"_, the answer should be _"none — see Manski bands"_, but the bands aren't in the submission flow.

3. **The CH-3 censoring correction is theatre at the current threshold (issue 2), and SFA inherits the same censoring bias with no correction at all (issue 3).** This means the headline frontier is biased _downward_ by an amount the team has not quantified. The report can defend a frontier that admits residual downward bias — but only if the report SAYS SO. Right now, NB21's documentation and the README will read as _"we corrected for censoring via Chernozhukov-Hong (2002)"_ — which is true in code and false in effect. That is a candor problem the Skeptic + Statistician will both flag in viva.

---

## 5. Final grade vs R2

R2 grade was **B / B+** (Statistician), with the four N-blockers as the gap to A−.

R3 grade: **B+** (Statistician).

| Dimension                                                  | R2           | R3  | Reasoning                                                                                                                                           |
| ---------------------------------------------------------- | ------------ | --- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plumbing (modules exist, imports work, cells run in order) | B+           | A−  | Three v2 notebooks are clean, imports resolve, parquet artifacts chain correctly.                                                                   |
| R1 + R2 fix completeness                                   | C+ (partial) | A−  | 7/9 fully fixed, 2/9 partial (M4 + the floor side-effect from N1).                                                                                  |
| Statistical honesty of the frontier                        | B−           | B−  | Same right-censored target everywhere; CH-3 fix is mostly cosmetic; SFA contribution biased downward and ensembled with XGB. **No movement vs R2.** |
| Validation / sensitivity wiring                            | B+           | B+  | All wired; V5 measures the wrong end (issue 12); sensitivity uses XGB-only (issue 4).                                                               |
| Headline number quality                                    | B−           | B−  | Median uplift will still under-shoot the 1.4–1.7 target; V4 may pass only barely.                                                                   |
| Audit trail                                                | B+           | B   | NB20 silver-rejected overwrite (issue 6) degrades the per-row check provenance.                                                                     |

**Net:** R3 deserves a **B+**, half a grade up from R2's B / B+. The four N-blockers are genuinely fixed, but the floor + censoring-proxy interaction creates a new headline-number problem that R3 reveals and R2 missed. To reach A−, the team needs to (a) loosen the CH-3 proxy (issue 2 fix, ~30 min), (b) decide whether to keep SFA in the ensemble or move it to a secondary diagnostic (issue 3, ~45 min), (c) refit q90 against a peer-frontier-anchored target so uplift does not collapse at the floor for the median outlet (issue 1, ~60 min), and (d) consume Manski + CQR side-outputs in NB22 (issue 8, ~15 min). Total ~2.5 hours.

---

## Pointers

- R1 master: `Reviews/council_review.md`
- R2 master: `Reviews/council_round2/council_review_v2.md`
- This file: `Reviews/council_round3/01_statistician_v3.md`
- Co-reviews (R3): `Reviews/council_round3/02_skeptic_v3.md`, `Reviews/council_round3/03_methodology_architect_v3.md`, (Safety + DE forthcoming).
