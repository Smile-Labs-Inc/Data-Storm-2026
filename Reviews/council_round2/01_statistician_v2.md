# AI Council R2 — Statistician (v2)

**Reviewer:** Statistician (1 of 4), Round 2.
**Round 1 grade:** **C−** (11 issues; see `Reviews/01_statistician.md`).
**Scope of v2:** verify each Round-1 fix landed; flag new defects in the refactored `src/` modules and `run_pipeline.py`.

---

# TL;DR

- **The headline triple of M1/M2/M3/M4 (quadruple throttle, double-counted constraint score, max-of-maxes floor, censored-q90 frontier) is genuinely fixed.** The new formula in `src/modeling/predict.py` is a single-throttle linear interpolation, the constraint score is rebuilt from frontier-residual + plateau + PCA capacity (no DQ flag, no `^1.25`), and a Chernozhukov–Hong style censoring correction is wired into `run_pipeline.py`. **M5 is also partly fixed**: a sensitivity sweep (`src/reporting/sensitivity.py`) and a 6-item validation suite (`src/reporting/validation.py`) both run end-to-end. This is real progress and warrants a real grade lift.
- **But three NEW statistical defects materially threaten defensibility.** (1) The Manski **lower bound is silently below the demonstrated maximum** (`src/reporting/manski.py:41`, `src/modeling/lower_bound.py:32–58`) — using the 3rd-highest month as a Manski lower violates the trivial identification floor "true ≥ observed max". (2) The **predict→validate chain is internally inconsistent**: `predict.py` floors at the new robust `lower_bound` (≤ historical max), so for outlets with small frontier gap the prediction lands **below** historical max, which makes V3b (`predicted ≥ historical_max for ≥99%` of outlets, `validation.py:80–87`) likely to **FAIL by construction**. (3) **V5 cap-binding check uses a hard-coded 5.9× threshold** (`validation.py:98`) instead of each bucket's own `cap_uplift` — it will systematically under-report cap binding for buckets with low caps (which is most of them under `min_cap=1.5`).
- **Two background statistical concerns survive but are no longer blockers**: the censoring proxy is per-outlet (mean-of-monthly delta > 0.3) instead of per-observation, which makes the CH-3 step closer to a pre-screen than a textbook correction; and the constraint-score sigmoid is a weighted z-sum of components on different intrinsic scales (PC1 variance ≠ 1, `plateau_signal ∈ {0, 1}`, frontier z is *re-standardised* after a clipped z), so the headline weights `(0.5, 0.3, 0.2)` are not interpretable as marginal contributions. Treat the score as an *index*, not a probability — and stop the README from calling it one.

---

# Verification Table

One row per issue from `Reviews/01_statistician.md`. Status legend: **FIXED** = problem materially addressed, **PARTIAL** = direction right, residual risk; **NOT FIXED** = still present.

| # | Round-1 Issue | Status now | File / line evidence | Residual risk |
|---|---|---|---|---|
| 1 | **Censoring direction** — q90 fitted on right-censored `y_obs`, used as upper-envelope. | **PARTIAL** | `src/modeling/censored_qr.py:35–144` (CH-3 module), `run_pipeline.py:255–268` (wired, `USE_CENSORING_CORRECTION=True`). | Censoring proxy is **per-outlet**, not per-month: `is_censored_outlet = monthly_delta.mean() > 0.3` (`run_pipeline.py:258–260`). Then propensity is fit on outlet-level X with no class-weighting (`censored_qr.py:94`). Likely keeps ~all 20k outlets at `propensity_threshold=0.10`, making the correction nearly a no-op. Plus the q90 model is fit on `observed_max_monthly_liters` (an outlet aggregate, `run_pipeline.py:253`), not the monthly panel — so this is "filter outlets that look chronically capped, then fit q90(max)", not the textbook 3-step Chernozhukov–Hong on `y_obs`. |
| 2 | **`lower_bound = max(hist, jan, recent_3mo)`** — collapses to `hist_max`, dominated by single-month spikes. | **FIXED** | `src/modeling/lower_bound.py:32–59`. Now: `max(3rd-highest month, median)` if `n≥6`, else `max(p95, median)`. The old `max(hist, jan, recent_3mo)` is gone. | Spillover defect: this new floor is **below** historical max by construction, so the *Manski lower bound* (which copies it, `manski.py:41`) and the *V3b validation gate* (which compares to historical max, `validation.py:80–87`) become inconsistent (see New Issue N1, N2). |
| 3 | **`^1.25` exponent + `clip(0, 0.65)` triple-throttle** — uplift mechanically capped. | **FIXED** | `src/modeling/predict.py:1–87`. New: `gap = (frontier_q90 − lower_bound).clip(lower=0); potential_raw = lower_bound + constraint_score × gap`. No exponent, no clip on the score, single `min(·, cap_uplift × hist_max)` cap from the bootstrap table. | None on the formula itself. Risk has migrated: now the cap (`apply_caps`, `caps.py:56–62`) is the only throttle, and the bootstrap proxy `obs_max / obs_median` (`caps.py:24–27`) is itself a within-outlet seasonal-swing statistic, not a true headroom estimator (see New Issue N4). |
| 4 | **Constraint score double-counts size + carries DQ flag** (`has_valid_coordinates` 10%, `Cooler_Count` and `mean_sku_count` enter via two paths). | **FIXED** | `src/modeling/constraint_score.py:1–144`. Components are now: (a) frontier-residual z-score, (b) plateau signal (months-since-new-max + recent-variance ratio), (c) PCA-decorrelated capacity. `has_valid_coordinates` is gone. `structural_capacity_score` is gone. Sigmoid map to [0, 1]. | Three residual concerns: (a) PCA sign-orientation heuristic (`constraint_score.py:83–84`) compares row N/2 against the matrix mean — essentially random sign flipping; should correlate PC1 against `Cooler_Count` and flip if negative. (b) Components live on incompatible scales (PC1 variance ≠ 1; `plateau_signal ∈ {0, 1}` × 1.5; frontier z re-standardised after asymmetric `clip(-3, 5)` in `_frontier_residual_z`, `constraint_score.py:42`), so the weights `(0.5, 0.3, 0.2)` are not marginal contributions in standardised units. (c) Plateau is a hard boolean (`(months_since_max > 6) and (var_ratio < 0.4)`, line 65) — discrete jump, not smooth. |
| 5 | **Peer frontier = max-of-maxes** with magic 0.85 / 1.35 multipliers. | **FIXED** | `src/modeling/frontier.py:1–127`. Now ONE multi-quantile model (XGBoost 2.0 `reg:quantileerror` with `quantile_alpha=[0.5, 0.75, 0.9, 0.95]`, monotone constraints, isotonic per-row sort for crossing). LightGBM fallback. The old `np.maximum.reduce` over 5 estimators with hard-coded `*0.85` / `*1.35` is gone. | Quantile model still trains on `observed_max_monthly_liters` (`run_pipeline.py:253`), an upper-tail order statistic per outlet — so `q90` of an order statistic is itself a noisy frontier proxy. The CH censoring filter (Issue 1) helps, but only weakly given the per-outlet aggregation. |
| 6 | **Multiplicative size caps** invert the prior (heavy censoring → small ceiling). | **PARTIAL** | `src/modeling/caps.py:14–44`. Bootstrap-derived `cap_quantile=0.95` of `obs_max / obs_median` per `(Outlet_Type, Outlet_Size)` bucket, clipped to `[1.5, 6.0]`. Replaces the static `{Small: 3.0, …, Extra Large: 4.5}` table. | Still multiplicative on `historical_max` (`caps.py:58–61`). The same inversion-of-prior dynamic survives: a chronically-constrained outlet with low `historical_max` and low `obs_median` could land in a low-cap bucket and be permanently capped near its historical level. The cap proxy `max/median` measures *within-outlet seasonal swing*, not headroom of true demand vs current sales — these are different objects (see New Issue N4). |
| 7 | **No holdout / no CV / no calibration** (CQR, pinball, synthetic-censoring stress test). | **PARTIAL** | `src/modeling/conformal.py:1–67` exists with `conformalised_qr` and `split_by_outlet`. **But `conformal.py` is never imported by `run_pipeline.py`** — `grep` for `conformal` in `run_pipeline.py` returns nothing. No CQR is computed; no empirical-coverage diagnostic is logged; no synthetic-censoring stress test exists. Sensitivity sweep partially substitutes for elasticity reporting. | Major: README/Architect already flag this — the project *claims* conformal intervals but does not produce them. Pinball loss on a holdout, empirical coverage, and the synthetic-censoring stress test (drop top-20% monthly volume → re-fit → reconstruct?) are still all absent. |
| 8 | **Latent target not point-identified, no honest interval reported.** | **PARTIAL** | `src/reporting/manski.py:1–66` builds `[manski_lower, point, manski_upper]` and `run_pipeline.py:341–343` writes `Results/manski_bands.csv`. DAG (`src/reporting/dag.py`) makes the censoring story explicit. | The Manski **lower** is wrong (see New Issue N1): it's the new robust `lower_bound` (3rd-highest), which is **below** the demonstrated max — a strict violation of the trivial Manski floor `true ≥ observed max`. The Manski **upper** uses `peer_p99` of `observed_max` (still censored) blended with `lower_bound × cap_uplift` capped at 6.0× — defensible but loose. The *Identifying Assumptions* subsection promised by my Round-1 F8 is not in any docs file I can see (no `Identification` heading in `Docs/`). |
| 9 | **Heteroscedasticity / distribution-shape blind spots** (L2 baseline, no `log1p` / Tweedie). | **PARTIAL** | `src/modeling/sfa.py:73–104` uses `log_target=True` (log1p) by default, and the SFA blend (`run_pipeline.py:307–311`) brings log-scale inference into the frontier. The XGBoost q90 is loss-robust (`reg:quantileerror`) so this is less of a concern than the L2 baseline of Round 1. | The XGBoost target is still raw `observed_max_monthly_liters` on the original scale (`run_pipeline.py:253`); no `log1p` for that head. Diagnostic plots / Q-Q / fitted-vs-actual are not saved in `data/gold/diagnostics/` (folder doesn't exist in the tree). The SFA `predict_frontier` returns the log-space conditional median, not the mean (`sfa.py:130–139`), and is not floored at zero — `expm1(negative)` gives negative volumes which then enter the 0.6 / 0.4 frontier blend. |
| 10 | **No sensitivity / elasticity table** for the four free knobs. | **PARTIAL → FIXED-ish** | `src/reporting/sensitivity.py:1–110` sweeps `quantile ∈ {0.85, 0.90, 0.95}`, `score_scheme ∈ {balanced, frontier_heavy, plateau_heavy}`, `cap_multiplier ∈ {2, 3, 4, 5, 6}` and reports `(median_uplift, mean_uplift, max_uplift, % capped)` per cell to `Reports/figures/sensitivity_table.csv` + `sensitivity_summary.md`. | Three knobs are *not* swept: the censoring `propensity_threshold` (currently 0.10), the SFA blend weight (currently 0.6 / 0.4, `run_pipeline.py:309–311`), and the lower-bound rule (3rd-highest vs p95 vs historical-max). Each of these can swing predictions materially. |
| 11 | **Smaller bugs** — `+1` in plateau CV, magic `0.85`/`1.35`, `+1` in uplift_ratio denominator, holiday duplicates. | **MOSTLY FIXED** | Magic 0.85 / 1.35 gone (Issue 5). `_january_holiday_count` (`gold.py:142–146`) takes the count of January holidays before silver dedup (`run_pipeline.py:172–173` uses the de-duped `hol_silver`), so duplicates are handled upstream. `predict.py` uses `replace(0, np.nan)` instead of `+1` in the uplift denominator (line 70) — better. `plateau` now uses `var_ratio = recent_var / max(all_var, 1e-6)` (`constraint_score.py:64`) — proper epsilon, not `+1 L`. | One residue: `caps.py:57` does `out["cap_uplift"].fillna(out["cap_uplift"].median() or 3.0)`. `np.nan or 3.0` evaluates to `nan` (NaN is truthy in Python `or`), so if the median is NaN the fallback never fires. Edge case, but the `or 3.0` is dead code. |

---

# New Issues

Severity legend: **BLOCKER** (must fix before submission, will fail validation or invalidate a key claim), **MAJOR** (will cost methodology rubric points if asked), **MINOR** (worth fixing if time permits).

### N1. Manski **lower bound** is below the demonstrated maximum — violates the trivial identification floor [BLOCKER]

In `src/reporting/manski.py:39–41`:

```37:41:autokaggle/competition/src/reporting/manski.py
    df = predictions.copy()
    df["manski_lower"] = df["lower_bound"]
```

…and `lower_bound` is the new robust `max(3rd-highest, median)` from `src/modeling/lower_bound.py:44–47`. For an outlet with monthly volumes `[100, 90, 80, …]` the new `lower_bound = 80`, while `observed_max_monthly_liters = 100`.

Manski (2003) bounds on **latent true demand** under right-censoring `y_obs = min(y_true, c)` give the *trivial* lower identification floor

> `y_true ≥ observed maximum across periods`

(because if you observed 100 once, true demand was at least 100 that period). Reporting `manski_lower = 80` for that outlet is *strictly below* the trivial Manski floor. The docstring even claims the lower is "the robust historical max ... what the outlet has DEMONSTRABLY achieved at least once" (`manski.py:7–8`) — but the code does not implement that claim.

**Fix (3 lines):** in `manski.py`, set `df["manski_lower"] = np.maximum(df["lower_bound"], df["observed_max_monthly_liters"])`. Keep the robust `lower_bound` as the *modeling* floor inside `predict.py` (it's correct there as a noise-robust shrinkage anchor); but for the *reported* Manski lower, use the demonstrated max.

### N2. `predict.py` floor + V3b validation are mutually inconsistent — V3b will FAIL by construction [BLOCKER]

`src/modeling/predict.py:52–58`:

```52:58:autokaggle/competition/src/modeling/predict.py
    df["lower_bound"] = df["lower_bound"].fillna(df["observed_max_monthly_liters"]).fillna(0.0)
    df["frontier_q90"] = df["frontier_q90"].fillna(df["lower_bound"])
    df["constraint_score"] = df["constraint_score"].fillna(0.0)

    gap = (df["frontier_q90"] - df["lower_bound"]).clip(lower=0)
    df["potential_raw"] = df["lower_bound"] + df["constraint_score"] * gap
    df["potential_raw"] = np.maximum(df["potential_raw"], df["lower_bound"])
```

Floor is the new robust `lower_bound` ≤ `observed_max_monthly_liters`. So for any outlet where `constraint_score × (frontier_q90 − lower_bound) < (historical_max − lower_bound)`, the prediction lands **below** `historical_max`. The cap step (`apply_caps`, `caps.py:58–61`) only `min`'s — never lifts.

But `src/reporting/validation.py:80–87` enforces:

```80:87:autokaggle/competition/src/reporting/validation.py
    merged = submission.merge(historical_max.rename("hist_max"), on="Outlet_ID", how="left")
    pct_below = float(((merged["Maximum_Monthly_Liters"] < merged["hist_max"]).fillna(False)).mean() * 100)
    v3_ok = pct_below < 1.0
```

Concrete example: outlet with months `[100, 90, 80, 70, 60, 50, 40, 30, 20, 10]`, `historical_max = 100`, `lower_bound = max(3rd-highest=80, median=55) = 80`, `frontier_q90 = 120`, `constraint_score = 0.3`:

- `potential_raw = 80 + 0.3 × 40 = 92`
- `potential_capped = min(92, 3 × 100) = 92`
- `92 < 100 = historical_max` → V3b violation.

Any outlet with constraint_score below `(hist_max − lower_bound) / (frontier − lower_bound)` triggers this. Whether this is 1% or 30% depends on the joint distribution of (gap, score) — but it is **non-zero by construction**, and V3b's threshold is `< 1%`.

**Fix:** change `predict.py:58` from `np.maximum(df["potential_raw"], df["lower_bound"])` to `np.maximum(df["potential_raw"], df["observed_max_monthly_liters"])`. The "evidence floor" for the *prediction* must be the demonstrated maximum, not a robust within-outlet quantile. The robust lower stays as a Manski/sensitivity object only.

### N3. V5 cap-binding check uses a hard-coded 5.9× threshold instead of the bucket's actual cap [MAJOR]

`src/reporting/validation.py:98–106`:

```98:106:autokaggle/competition/src/reporting/validation.py
    cap_threshold = (merged["hist_max"] * 5.9).round(2)
    capped = (merged["Maximum_Monthly_Liters"] >= cap_threshold).fillna(False)
    pct_capped = float(capped.mean() * 100)
    v5_ok = pct_capped < cap_binding_max_pct
    checks.append(CheckResult(
        name=f"V5: cap-binding rate < {cap_binding_max_pct}%",
        passed=v5_ok,
        detail=f"{pct_capped:.2f}% appear capped at ~6x historical max",
    ))
```

Bootstrap caps come out anywhere in `[1.5, 6.0]` (`caps.py:19–35`). For a Pharmacy × Small bucket whose empirical 95th-percentile uplift proxy is, say, 2.0×, every outlet capped right at `2.0 × historical_max` is the bucket's *binding* outlet — but `validation.py` only counts outlets ≥ `5.9 × historical_max`, which is essentially zero. The check will pass spuriously while a quarter of the buckets could be hard-capped.

**Fix:** join the cap_table into the validation step and compare against `cap_uplift_per_bucket × hist_max - 1e-6` per outlet. The orchestrator already has `cap_table` in scope (`run_pipeline.py:299, 314`); pass it to `run_validation_suite`.

### N4. Bootstrap cap proxy `obs_max / obs_median` measures within-outlet seasonal swing, not headroom of true demand vs current sales [MAJOR]

`src/modeling/caps.py:23–35`:

```23:35:autokaggle/competition/src/modeling/caps.py
    df = features.copy()
    df["_uplift_proxy"] = (
        df["observed_max_monthly_liters"]
        / df["observed_median_monthly_liters"].replace(0, np.nan)
    )

    rows: list[dict] = []
    for keys, sub in df.groupby(list(bucket_cols)):
        if len(sub) < min_bucket_n:
            cap = float(np.nanquantile(df["_uplift_proxy"].dropna(), cap_quantile))
        else:
            cap = float(np.nanquantile(sub["_uplift_proxy"].dropna(), cap_quantile))
        cap = float(np.clip(cap, min_cap, max_cap))
```

The reasoning chain "p95 of (max / median) per peer cell = empirical uplift cap" assumes that within-outlet seasonal/promotional swing is a good proxy for *latent demand vs observed* headroom. It is not. An outlet with very stable monthly demand and a single Christmas spike has `max/median ≈ 3` — but might still have 10× latent headroom. An outlet whose true demand is wildly volatile but never censored has high `max/median` — but zero latent uplift. The two distributions are not the same. As a "defensible empirical anchor" this is fine *if it's documented as such*; it is currently labelled "uplift cap" and treated as a true demand ceiling.

**Fix (cheap):** rename `cap_uplift` → `bucket_swing_cap` in `caps.py` and `manski.py`, and add a one-line note in `Docs/modeling_methodology.md` explaining the proxy assumption ("we cap the predicted multiplier at the 95th-percentile within-outlet swing observed in same-bucket peers; this is an empirical anchor, not a true-demand ceiling"). **Fix (expensive):** add a second cap based on `peer_q90 / outlet_observed_median` — a cross-outlet headroom estimator.

### N5. CH censoring proxy is per-outlet (mean over months) — far weaker than the textbook 3-step [MAJOR]

`run_pipeline.py:255–268`:

```255:268:autokaggle/competition/run_pipeline.py
    if USE_CENSORING_CORRECTION:
        print("  -> Chernozhukov-Hong censoring correction")
        delta_per_month = build_censoring_proxy(monthly)
        is_censored_outlet = (
            delta_per_month.groupby("Outlet_ID")["delta"].mean() > 0.3
        ).astype(int)
        delta = pd.Series(0, index=gold.index)
        delta_map = is_censored_outlet.reindex(gold["Outlet_ID"]).fillna(0).astype(int).values
        delta = pd.Series(delta_map, index=gold.index)
        X_train, y_train, corr = chernozhukov_hong_correction(X, y, delta)
```

Three concerns:

1. **Aggregation drops information.** `build_censoring_proxy` returns one row per outlet-month with `delta ∈ {0, 1}` — the natural CH-3 step is then `P(censored | X_t) → keep observation t if low`. The current code averages `delta` over months, thresholds at 0.3, then keeps *whole outlets*. So an outlet with one censored month and 35 free ones is treated identically to an outlet that's free always. (Conversely, an outlet with 4/12 censored months is dropped entirely from training.)
2. **Class imbalance is unhandled.** `LogisticRegression(max_iter=200, n_jobs=-1)` (`censored_qr.py:94`) — no `class_weight='balanced'`. Given the strict proxy thresholds (3 consecutive months at ≥95% of max, OR plateau detector), `is_censored_outlet=1` is likely small (<10% of 20k). The fitted propensity is then biased toward 0 for everyone, and `propensity_threshold=0.10` keeps almost all rows.
3. **Sample-mismatch with the q90 target.** The XGBoost q90 head fits on `observed_max_monthly_liters` (one value per outlet), not on the monthly panel. CH-3 is meant to debias quantile regression on per-observation `y_obs`. Filtering at the outlet level before fitting `q90(max)` is closer to "exclude dirty rows" than to a censoring correction.

The first line of `delta = pd.Series(0, index=gold.index)` is also dead code (overwritten three lines later) — `run_pipeline.py:261`.

**Fix:** the cheapest correct version is to fit the q90 head on the **monthly panel** (`monthly`) with outlet-level features broadcast, apply the CH-3 step at the *month* level, and aggregate predictions to per-outlet q90 of conditional fitted values. This matches the cited Chernozhukov–Hong reference.

### N6. Constraint-score components live on incompatible scales; weights are not interpretable as marginal contributions [MAJOR]

`src/modeling/constraint_score.py:120–132`:

```120:132:autokaggle/competition/src/modeling/constraint_score.py
    z_frontier = (df["frontier_residual_z"] - df["frontier_residual_z"].mean()) / (
        df["frontier_residual_z"].std() or 1.0
    )
    z_plateau = df["plateau_signal"].astype(float) * 1.5  # +1.5 z if plateaued
    z_capacity_inv = -df["capacity_pc1"]  # low capacity = more constrained

    raw = (
        weight_frontier * z_frontier
        + weight_plateau * z_plateau
        + weight_capacity * z_capacity_inv
    )
    df["constraint_score"] = _sigmoid(raw.values)
```

- `z_frontier`: started as `(peer_q90 − obs_max) / peer_sd` (an in-sample z), then asymmetrically `clip(-3, 5)` (`constraint_score.py:42`), then re-standardised to mean 0, std 1. Net: roughly N(0, 1) but with a left tail tied off and a longer right tail.
- `z_plateau`: `plateau_signal × 1.5` ∈ {0, 1.5}. Mean ≈ 1.5 × P(plateau); std ≈ 1.5 × √(p(1−p)). Not standardised.
- `z_capacity_inv`: `-PC1`. PC1 has variance equal to the first eigenvalue (typically > 1 for correlated features). Not standardised.

So the headline weights `(0.5, 0.3, 0.2)` are not the marginal contributions in standardised units that they appear to be. The plateau term contributes very little to the variance of `raw` (std ≈ 0.45 × 1.5 ≈ 0.7 if 50% plateaued, less otherwise), while capacity can dominate or vanish depending on the eigenvalue. The sigmoid then squashes into [0, 1], so the operational behaviour is closer to "frontier residual + capacity, with plateau as a small bump."

This is fine for a heuristic index but the README/Architect cite the score weights as if they were probabilities. They aren't.

**Fix:** standardise all three components to mean 0, std 1 *after* construction (`StandardScaler` on each in turn) before the weighted sum. Then the `(0.5, 0.3, 0.2)` weights are interpretable. Also, fix the PCA sign-orientation heuristic at `constraint_score.py:83–84` — currently it looks at row N/2, which is essentially random; replace with `if pearsonr(pc, df['Cooler_Count'])[0] < 0: pc = -pc`.

### N7. SFA frontier returns log-space conditional median, not mean; not floored at zero [MINOR]

`src/modeling/sfa.py:130–139`:

```130:139:autokaggle/competition/src/modeling/sfa.py
def predict_frontier(
    fit: SFAResult,
    X: pd.DataFrame,
    log_target: bool = True,
) -> pd.Series:
    X_arr = np.column_stack([np.ones(len(X)), X.fillna(X.median(numeric_only=True)).values])
    yhat = X_arr @ fit.beta
    if log_target:
        yhat = np.expm1(yhat)
    return pd.Series(yhat, index=X.index, name="sfa_frontier")
```

For the log-target SFA `log1p(y) = X β + v − u` with `v ∼ N(0, σ_v²)`, the conditional **mean** of `y` on the frontier (`u = 0`) is `expm1(X β + 0.5 σ_v²) − 1`, not `expm1(X β)`. The current code returns the conditional **median**, which under-estimates frontier means by `≈ exp(0.5 σ_v²) − 1` (≈ 5% if `σ_v=0.3`, ≈ 13% if `σ_v=0.5`).

It is also not floored at zero. `expm1` of any negative `X β` returns negative values, which then enter the 0.6 / 0.4 frontier blend at `run_pipeline.py:309–311`. With small-bucket outlets and noisy fits this can produce a frontier *below* the observed max for some rows.

**Fix:** in `predict_frontier`, return `np.maximum(np.expm1(X @ beta + 0.5 * fit.sigma_v ** 2), 0.0)`. Document this as the conditional-mean frontier.

### N8. Sensitivity sweep does not vary the censoring threshold, the SFA blend weight, or the lower-bound rule [MINOR]

`src/reporting/sensitivity.py:24–91` sweeps quantile, score scheme, cap multiplier — but the project has at least three additional free knobs that were called out as load-bearing:

- `propensity_threshold` (CH censoring filter, `chernozhukov_hong_correction(..., propensity_threshold=0.10)`, `censored_qr.py:112`).
- The 0.6 / 0.4 SFA / XGB blend (`run_pipeline.py:309–311`).
- `MIN_ACTIVE_MONTHS_FOR_3RD_HIGHEST = 6` and the `max(3rd-highest, p95)` rule in `lower_bound.py:21, 44–51`.

**Fix:** add these three knobs to the sweep with 3 levels each (e.g., `propensity_threshold ∈ {0.05, 0.10, 0.20}`, `sfa_weight ∈ {0.0, 0.4, 0.6}`, `lower_bound ∈ {3rd-highest, p95, hist_max}`). Even if the headline numbers don't move much, the *report* gains a directly defensible "knob → impact" table.

### N9. Conformalised QR module exists but is never called — overclaim risk [MAJOR]

`src/modeling/conformal.py:1–67` is a clean implementation of split-CQR with `split_by_outlet` for outlet-level holdout. **It is never imported by `run_pipeline.py`.** No empirical-coverage diagnostic is logged anywhere. The Methodology Architect already flagged this in `03_methodology_architect_v2.md:42, 49`. From the statistician's seat the same applies: the project will lose Methodology rubric points if it claims calibrated intervals it does not produce.

**Fix:** wire `conformal.conformalised_qr` into `run_pipeline.model_and_predict`: split the outlet panel, hold out 20% of *outlets*, re-fit the multi-quantile head on 80%, conformalise on 20%, log empirical coverage at α = 0.10 and α = 0.20 to `Reports/figures/cqr_coverage.json`. Time cost: ~30 minutes given the existing helpers.

### N10. Mid-pipeline `Outlet_ID` join keys are unverified — silent merge mismatches possible [MINOR]

`run_pipeline.py:296–314` does multiple merges on `Outlet_ID` (constraint score, lower bound, frontier, cap table) without an assertion that the join keys are 1:1 and complete. If `gold` has outlets that are missing from `transactions` (e.g., zero-transaction outlets in the master), `lower_bound.robust_lower_bound` returns no row for them, and `predict.py:52` falls back to `observed_max_monthly_liters` (which is also NaN for those outlets) → the `.fillna(0.0)` then sets their floor to 0. The 6-item validation will then see a few outlets at 0 and fail V3b.

**Fix:** in `predict.py`, add `assert df["Outlet_ID"].is_unique` after the merges, and `df["lower_bound"] = df["lower_bound"].fillna(df["observed_max_monthly_liters"]).fillna(df["observed_max_monthly_liters"].median()).fillna(0.0)` so zero-transaction outlets get a sensible non-zero floor.

---

## LOST functionality vs Round 1

I did not find any *legitimate* signal that was dropped. The things that disappeared (the static `{Small: 3.0, …}` cap table, the `^1.25` exponent + `clip(0, 0.65)`, the `max(hist, jan, recent_3mo)` floor, the 5-source `np.maximum.reduce` peer frontier, the `has_valid_coordinates` rank, the `+1 L` plateau hack) are exactly the things Round 1 asked to remove. **No false positives — nothing was thrown out by accident.**

One mild regression: the Round-1 notebook produced a `data_quality_report.md` with explicit channel scores; the Round-2 silver layer writes one too (`run_pipeline.py:167`), but I haven't verified the markdown content is identical in structure. Worth a 30-second eyeball before submission.

## Implementation-bug log (off-by-one / wrong axis / sign)

- `caps.py:57` — `fillna(median or 3.0)` is dead code when median is NaN (Python `nan or 3.0 == nan`). Use `fillna(median if not pd.isna(median) else 3.0)`.
- `constraint_score.py:83–84` — PCA sign-orientation heuristic is essentially random. Replace with correlation against `Cooler_Count`.
- `run_pipeline.py:261` — `delta = pd.Series(0, index=gold.index)` is overwritten three lines later. Dead code.
- `manski.py:41` — `manski_lower = lower_bound`, but the docstring says it should be `historical max`. Doc/code mismatch (BLOCKER, see N1).
- `predict.py:58` — flooring at `lower_bound` (≤ historical_max) creates V3b failures (BLOCKER, see N2).
- `validation.py:98` — hard-coded 5.9× cap-binding threshold (MAJOR, see N3).

---

# Updated Grade

**Was: C−. Now: B / B+.**

The methodology is no longer incoherent: the formula has one throttle, the constraint score is built from real demand-residual signals, the lower bound is robust to single-month spikes, the q90 head has a censoring-correction pre-screen, the codebase is structured into named `src/` modules, the Manski / sensitivity / validation reports run end-to-end, and the SFA addition is a defensible second-method track (not a model zoo).

Why not A−:

1. The Manski lower bound is still **wrong** in the literal Manski sense (N1).
2. V3b will likely **fail** because of the floor mismatch (N2).
3. V5 silently passes due to the wrong threshold (N3).
4. CQR is **claimed but not produced** (N9).
5. The CH censoring step is a per-outlet pre-screen, not the textbook 3-step on the monthly panel (N5).

These are all 5–60-minute fixes. Land them and the grade is **A−**.

---

# Final Recommendation

**Ship after a 90-minute fix pass — do not rebuild.** The architecture is sound and Round-1's blockers are genuinely resolved. But before pressing submit, the team must (in order, time budget in parens):

1. **(15 min)** `predict.py:58`: change the prediction floor from `lower_bound` to `observed_max_monthly_liters`. Re-run validation. **This alone unblocks V3b.**
2. **(15 min)** `manski.py:41`: change `manski_lower` to `np.maximum(lower_bound, observed_max_monthly_liters)`. Honest Manski floor.
3. **(20 min)** `validation.py:98`: pass `cap_table` into `run_validation_suite` and compute the V5 threshold per bucket. Honest cap-binding rate.
4. **(30 min)** Either *wire CQR* into `run_pipeline.py` (call `conformalised_qr` on a 20% outlet holdout, log coverage to `Reports/figures/cqr_coverage.json`) **or** strike the CQR claim from the README/PDF entirely. Pick one.
5. **(10 min)** Drop the dead lines (`run_pipeline.py:261`, `caps.py:57` `or 3.0`), fix the PCA sign heuristic (`constraint_score.py:83–84` → correlate against `Cooler_Count`), and floor SFA at zero (`sfa.py:138`).

If those 90 minutes are not available before the deadline, the order of priority is N2 → N1 → N3 → N9 → N5. **N2 is the only one that can outright fail validation; the others lose rubric points but do not block submission.**

After this fix pass, the team has a coherent, identifiable, partially-validated, sensitivity-tested latent-potential pipeline. That is a strong B+ submission and a defensible viva. Without N2, V3b can fail and the headline "predicted ≥ historical evidence" claim collapses — that's the only outcome that is unrecoverable in the last hour.
