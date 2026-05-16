# AI Council Round 2 — Master Synthesis

**4 parallel premium critics re-audited the refactored v2 pipeline.**

| Critic | Round 1 grade | Round 2 grade |
|---|---|---|
| Statistician | C− | B / B+ |
| Skeptic | D+ | B− (B/B+ after fixes) |
| Methodology Architect | B− | B+ |
| Safety + DE | D+ | B (B+ after rerun) |
| **Consensus** | **D+** | **B / B+** |

**One-line verdict:** *Substantive lift since round 1, but four real bugs survived the refactor and one of them will make the auto-validation fail by construction. ~90 minutes of fixes lifts this to A-.*

---

## What landed (round 1 -> round 2)

| Round 1 issue | Status | Evidence |
|---|---|---|
| (B1) `row_id` -> `Outlet_ID` | FIXED | `Results/teamname_predictions.csv` head verified |
| (B2) 914-row -> 20,000 rows | FIXED | wc -l confirmed 20,001 |
| (B3) `data/silver_rejected/` populated | DEFERRED | will populate when team runs `python run_pipeline.py` |
| (B4) `src/` modules exist | FIXED | 23 .py files across 6 sub-packages |
| (B5) POI pipeline exists | FIXED (code) / DEFERRED (output) | scripts in `poi_pipeline/`; output appears after run |
| (M1) Quadruple throttling | FIXED | `predict.py` is one linear interpolation |
| (M2) `valid_coordinate_rank` in score | FIXED | `constraint_score.py` rebuilt; no DQ flag |
| (M3) Lower bound = max-of-maxes | FIXED | `lower_bound.py` uses 3rd-highest month |
| (M4) Censoring uncorrected | PARTIAL | CH-3 module exists; threshold may be too lax |
| (M5) No validation/sensitivity | FIXED (auto-validation + sensitivity exist) |

---

## NEW blockers from round 2 (4 critical, all fixable in ~90 min)

These are the **must-fix-now** items. All flagged independently by 2+ reviewers.

### N1. `predict.py` will fail auto-validation V3b by construction (Statistician + Skeptic)

`predict.py` clamps the prediction to `lower_bound` = the new robust 3rd-highest month. But validation V3b requires `predicted >= historical_max` for >=99% of outlets. By definition `lower_bound <= historical_max`, so any outlet whose `constraint_score * gap` is small will land BELOW `historical_max` and V3b fails.

**Fix:** floor predictions at `historical_max` (i.e. `observed_max_monthly_liters`), not at `lower_bound`.

```python
# in predict.py, replace:
df["potential_raw"] = np.maximum(df["potential_raw"], df["lower_bound"])
# with:
df["potential_raw"] = np.maximum(
    df["potential_raw"],
    df["observed_max_monthly_liters"].fillna(df["lower_bound"])
)
```

### N2. `manski.py` has `manski_lower < observed_max` (Statistician)

The Manski floor for right-censored data is `observed_max` (the smallest known true demand). Currently `manski_lower = lower_bound` which can be lower. Wrong by definition.

**Fix:** in `manski.py`, set `manski_lower = max(lower_bound, observed_max_monthly_liters)`.

### N3. SFA has target leakage (Skeptic)

`run_pipeline.py` feeds `observed_p90`, `observed_p95`, `observed_median`, `observed_mean` into `sfa_X` while predicting `log(observed_max)`. These columns are deterministic functions of the target -> `sigma_u -> 0`, `TE ≈ 1`, the SFA frontier collapses to OLS, and the second methodology track is theatre.

**Fix:** drop those 4 columns from the SFA feature list (use Cooler_Count, sku_breadth, catchment, POI features, calendar features only).

### N4. CQR is implemented but never called (Statistician + Architect + Skeptic)

`src/modeling/conformal.py` is a real CQR implementation, but the orchestrator never invokes it. The README claims "calibrated coverage via Conformalised Quantile Regression" -- false today.

**Fix:** add a `conformalise()` step in `run_pipeline.py` after the multi-quantile fit, using a 20% outlet-level holdout (the helper `split_by_outlet` already exists in `conformal.py`). Write the calibrated `[q05, q95]` band to `Results/conformal_intervals.csv`.

---

## Other issues to fix opportunistically (after the 4 blockers)

| # | Issue | Severity | Module | Fix |
|---|---|---|---|---|
| O1 | V5 cap-binding uses hardcoded `5.9 * hist_max` | MAJOR | `validation.py:98` | use the actual bucket `cap_uplift` from the cap_table |
| O2 | Cap proxy `obs_max / obs_median` measures within-outlet swing, not headroom | MINOR | `caps.py` | swap to `peer_q95 / outlet_obs_median` |
| O3 | SFA `predict_frontier` returns log-conditional median (not mean) and isn't floored at zero | MINOR | `sfa.py` | exp-correct + clip to `>=0` |
| O4 | PCA capacity sign heuristic in `constraint_score.py:83-84` is essentially random | MINOR | `constraint_score.py` | enforce direction by signing on a known-positive feature (e.g. Cooler_Count) |
| O5 | Legacy 914-row CSV still in `Results/` -> accidental upload risk | MAJOR (DQ risk, not statistical) | filesystem | move `legacy_914row_predictions.csv` to `Results/_legacy/` |
| O6 | `manski.py` uses hardcoded `DEFAULT_MAX_UPLIFT = 6.0` for upper bound | MINOR | `manski.py` | derive from cap bootstrap, not hardcoded |

---

## What's still theatre (to either fix or stop claiming)

| Claim in README | Reality | Fix |
|---|---|---|
| "Conformalised Quantile Regression" gives calibrated intervals | Module exists, not wired | Wire it (N4) |
| "SFA + multi-quantile ensemble" | SFA leaks the target -> collapses to OLS | Fix features (N3) |
| "Manski bounds" | Implementation is wrong (N2 + O6) | Fix to true Manski floor |
| 6-item auto-validation passes | V3b will fail by construction (N1) | Fix N1 |

---

## Critical path for the next 24 hours

```
HOUR 0-2  (now)        4 blocker fixes (N1-N4) + 2 high-value fixes (O1, O5)
HOUR 2-3               run `python run_pipeline.py` -- verify all 6 validations pass
HOUR 3-9               run POI pipeline (4 scripts in poi_pipeline/) in background;
                       in parallel start 5-page PDF draft
HOUR 9-12              re-run run_pipeline.py with POI features; verify medians shift
HOUR 12-18             finish 5-page PDF + final figures + DAG + sensitivity table
HOUR 18-24             package: zip repo, final preflight, GenAI log review
HOUR 24+               buffer
```

---

## Critic agreement on grades

All 4 critics independently said the same thing in different words:

- **As-shipped today:** B / B-
- **After the 4 blocker fixes:** B+ / A-

The pipeline went from "narrative without receipts" to "receipts pending the run button". The remaining work is execution, not redesign.

---

## What ship/no-ship looks like

**SHIP if:**
- N1, N2, N3, N4 are fixed
- `python run_pipeline.py` runs cleanly end-to-end
- All 6 validations PASS
- Either the POI pipeline ran, or you honestly disclose it didn't (mention attempted Geofabrik fetch)
- 5-page PDF is written and matches what the code actually does

**DO NOT SHIP if:**
- Any validation FAILs and the team can't explain why
- The legacy 914-row file gets uploaded by accident
- The PDF claims SFA/CQR/Manski but the code doesn't actually do them

---

## Pointers

- Round 1 reviews + master: `Reviews/01-04_*.md` + `Reviews/council_review.md`
- Round 2 individual critics:
  - `Reviews/council_round2/01_statistician_v2.md`
  - `Reviews/council_round2/02_skeptic_v2.md`
  - `Reviews/council_round2/03_methodology_architect_v2.md`
  - `Reviews/council_round2/04_safety_and_de_v2.md`
- Research swarm: `research/research_brief.md` + `research/0[1-9]_*.md` + `10_*.md`

The team should now read this file, then start the 4 blocker fixes. Total estimated time: 90 minutes including a sanity rerun.
