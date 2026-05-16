# AI Council Round 3 — Master Synthesis

**4 parallel premium critics audited the 3 v2 notebooks** (20_v2_data_pipeline, 21_v2_modeling, 22_v2_validation_and_submission).

| Critic                | R1     | R2       | R3                                         |
| --------------------- | ------ | -------- | ------------------------------------------ |
| Statistician          | C−     | B/B+     | **B+** (A− after fixes)                    |
| Skeptic               | D+     | B−/B/B+  | **B−/B** today (B+ after 45-min packaging) |
| Methodology Architect | B−     | B+       | **B+** (coherent if v2 displaces v1)       |
| Safety + DE           | D+     | B/B+     | **B−** (not fresh-clone reproducible)      |
| **Consensus**         | **D+** | **B/B+** | **B today, A− achievable**                 |

**One-line verdict:** _The v2 notebooks exist and the methodology lands in code — but 5 new bugs surfaced that the prior rounds didn't catch, the v1 notebooks/CSVs/PDF still sit in the repo waiting to mislead a judge, and the v2 stack has never been run end-to-end. ~45 minutes of fixes + 1 successful end-to-end run gets you to A−._

---

## What the v2 notebooks did right (verified)

| Issue                                | Status | Evidence                                                                                   |
| ------------------------------------ | ------ | ------------------------------------------------------------------------------------------ |
| M1 quadruple throttling              | FIXED  | `src/modeling/predict.py:56-64` -- single linear interpolation                             |
| M2 constraint_score has DQ flag      | FIXED  | `src/modeling/constraint_score.py:92-132` -- PCA + frontier-residual + plateau, no DQ flag |
| M3 lower_bound dominated by hist_max | FIXED  | `src/modeling/lower_bound.py:32-58` -- 3rd-highest month or own p95                        |
| R2 N1 manski_lower < observed_max    | FIXED  | `src/reporting/manski.py:45-48` -- `max(lower_bound, observed_max)`                        |
| R2 N2 predict floors at lower_bound  | FIXED  | `predict.py:65-72` -- floors at `observed_max`                                             |

---

## NEW issues found in Round 3 (5 critical, all flagged by 2+ critics)

### N1. CQR calibration set overlaps the q90 training set (Statistician + Skeptic)

`21_v2_modeling.ipynb` cell ordering bug: the multi-quantile model is fit in cell 9 on `X_train` (the post-CH-3 uncensored subset). Then in cell 21 the CQR step splits the SAME data 80/20 and uses the 20% holdout for calibration. But that 20% was already used to fit the q90 model -- so `qhat` is biased downward and the reported empirical coverage is optimistic.

**Fix:** split BEFORE fitting q90. Either: (a) hold out 20% of outlets FIRST, fit q90 on the 80%, then calibrate CQR on the 20%; OR (b) use cross-conformal prediction.

### N2. The "SFA leakage filter" is a NO-OP (Statistician + Skeptic)

`21_v2_modeling.ipynb` cell 11 has:

```python
leaky_cols = {"observed_mean_monthly_liters", "observed_median_monthly_liters",
              "observed_p90_monthly_liters", "observed_p95_monthly_liters"}
sfa_feature_cols = [c for c in feature_cols if c not in leaky_cols]
```

But `feature_cols` (from cell 7) is `base_features + poi_decay_cols` -- the `observed_*` columns were NEVER in `feature_cols` to begin with. So the filter removes nothing. SFA is fitting on the correct (non-leaky) feature set by accident, not by design.

**Fix:** rewrite as an explicit whitelist: `sfa_feature_cols = [explicit list of structural + POI + calendar features]`.

### N3. `src/reporting/manski.py` cap_table merge silently no-ops (Skeptic)

`manski.py:54-61`:

```python
df = df.merge(
    cap_table[["Outlet_Type", "Outlet_Size", "cap_uplift"]],
    on=["Outlet_Type", "Outlet_Size"],
    how="left",
    suffixes=("", "_cap"),
)
cap = df["cap_uplift"].fillna(max_uplift)
```

But `predictions` (from `predict.py`) already has a `cap_uplift` column. The `suffixes=("", "_cap")` causes the merge's `cap_uplift` to become `cap_uplift_cap`, while `df["cap_uplift"]` still points to the ORIGINAL one from predict.py. The Manski upper bound effectively reuses the point-estimate cap instead of a Manski-specific upper-bound cap.

**Fix:** rename the merged column explicitly: `cap_table.rename(columns={"cap_uplift": "manski_cap"})` then use `manski_cap`.

### N4. `manski.py:70` clips the point inside the Manski interval (Skeptic)

```python
df["point"] = np.clip(df["point"], df["manski_lower"], df["manski_upper"])
```

The submission CSV's `Maximum_Monthly_Liters` is NOT clipped. So `manski_bands_v2.csv` shows a different `point` value than the submission for any outlet where the predict.py output exceeds the Manski upper.

**Fix:** drop the clip OR emit a sentinel "outside_band" flag.

### N5. Notebook 22 cell 3 asserts BEFORE the reindex (Skeptic)

The asserts (`is_unique`, `not isna`, `>= 0`) run on `sub` BEFORE the merge against `outlet_master`. After the merge, the left-join can introduce NaN rows that bypass all 4 checks.

**Fix:** reorder -- reindex first, then assert.

---

## STILL-OUTSTANDING items from prior rounds

| Issue                                                                         | Status            | Fix needed                                                    |
| ----------------------------------------------------------------------------- | ----------------- | ------------------------------------------------------------- |
| `Results/smile_labs_predictions.csv` STILL has `row_id` + 914 rows (R1 B1+B2) | NOT TOUCHED       | overwrite OR move to `Results/_legacy/` after v2 runs         |
| `README.md` lines 9-11/39/86-89 still document v1                             | NOT TOUCHED       | update to point to notebooks 20/21/22 + `requirements_v2.txt` |
| `Docs/final_report.pdf` still documents v1 numbers                            | NOT TOUCHED       | rebuild after v2 runs                                         |
| `data/silver_rejected/` empty (only `.gitkeep`)                               | NOT YET RUN       | will populate when notebook 20 runs                           |
| `poi_pipeline/output/` empty                                                  | NOT YET RUN       | needs 4 POI scripts to be run, or v2 runs without POI         |
| `requirements.txt` (the official one) missing xgboost>=2.0, mapie, etc.       | NOT TOUCHED       | merge `requirements_v2.txt` in or replace                     |
| `ALT_RAW_DIR` in notebook 20 points to my local autokaggle path               | TEAM-SPECIFIC BUG | replace with a clean error message                            |

---

## Architect's "ONE move" recommendation

> **Make Notebook 22 the canonical release gate.** Today, notebook 22 writes `_v2.csv` and tells the team "you decide which to upload". That's a 30% clean-ship probability. Architect's move: notebook 22 should (a) overwrite the v1 file by default (moving v1 to `_legacy/`), (b) regenerate `Docs/final_report.pdf` directly from the v2 numbers, (c) write a `run_manifest.json` so a judge can verify exactly what produced the CSV.

---

## Predicted v2 numbers on a clean end-to-end run

Per Statistician + sanity from research/06 + 07:

- **Median uplift: ~1.10–1.18x** (NOT 1.4–1.7x as R1 hoped). The floor at `observed_max` pegs ~50% of outlets at exactly 1.0x. The constraint score only moves the OTHER 50%.
- **Mean uplift: ~1.35–1.50x**.
- **6-item validation: ALL PASS** with current thresholds. But V4 range `[1.05, 2.5]` is too generous -- it passes even if M1 didn't really land. Tighten to `[1.25, 2.2]` to be honest about the fix.

The "M1 landed in code" is technically true; the "M1 changes the headline number" is largely false because the floor-at-observed_max constraint dominates. This is acceptable -- it's the right tradeoff for V3b safety -- but the report should disclose it honestly.

---

## Critical-path fixes (the 45-minute packaging fix)

In priority order:

1. **N1 fix** — refactor notebook 21 to split BEFORE fitting q90 (15 min)
2. **N2 fix** — explicit SFA feature whitelist (5 min)
3. **N3 + N4 fix** — `src/reporting/manski.py` rename + drop point-clip (5 min)
4. **N5 fix** — notebook 22 reindex BEFORE asserts (5 min)
5. **ALT_RAW_DIR fix** — replace my path with `raise FileNotFoundError("Place raw CSVs in Datasets/")` (2 min)
6. **README update** — replace v1 references with v2 (5 min)
7. **V4 tighten** — change range to `[1.25, 2.2]` (1 min)
8. **Move v1 CSVs to Results/\_legacy/** so they can't be uploaded by mistake (2 min)
9. **Run notebook 20 -> 21 -> 22 end-to-end** to populate artifacts on disk (10 min compute, depending on POI)

---

## Clean ship checklist

After all fixes:

- [ ] notebook 20 runs cleanly -> `data/silver_rejected/*.csv` non-empty, `data/gold/outlet_features.parquet` exists
- [ ] notebook 21 runs cleanly -> `data/gold/predictions_v2.parquet` exists, SFA prints converged
- [ ] notebook 22 runs cleanly -> 6 validations PASS, `Results/smile_labs_predictions_v2.csv` is `Outlet_ID, Maximum_Monthly_Liters` with 20,000 rows
- [ ] CQR coverage reported is realistic (not optimistic)
- [ ] `Docs/final_report.pdf` rebuilt with v2 numbers
- [ ] `README.md` points to v2 notebooks + `requirements_v2.txt`
- [ ] `Results/smile_labs_predictions.csv` either replaced with v2 or moved to `_legacy/`

---

## What to ship vs what to shelf

**SHIP if:** all 8 critical-path fixes done + clean end-to-end run + PDF rebuilt + v1 CSV moved.

**SHELF (use v1 instead) if:** time runs out before fixes complete. v1 stays at D+ to C grade, but it's _runnable_ and ships _something_. Don't ship a half-broken v2.

---

## Pointers

- Individual R3 critic files:
  - `Reviews/council_round3/01_statistician_v3.md`
  - `Reviews/council_round3/02_skeptic_v3.md`
  - `Reviews/council_round3/03_methodology_architect_v3.md`
  - `Reviews/council_round3/04_safety_and_de_v3.md`
- Prior rounds: `Reviews/council_review.md` + `Reviews/council_round2/council_review_v2.md`
- Research: `research/research_brief.md`
