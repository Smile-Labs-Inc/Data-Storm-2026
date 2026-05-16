# Skeptic Review v2 — Data Storm 7.0 (Council Round 2)

> Round 1 grade was D+. The team rewrote ~90% of the modeling layer.
> My job here: confirm the round-1 blockers landed, find the *new* theatre,
> and predict what hostile judges will still kill them on.

---

# TL;DR

- **The CSV is fixed, the pipeline isn't proven to run.** `Results/teamname_predictions.csv` now has `Outlet_ID,Maximum_Monthly_Liters` and 20,000 rows — but `data/silver_rejected/` is empty and `poi_pipeline/output/` does not exist. If the team submits **without re-running `run_pipeline.py` and the 4 POI scripts**, the report claims (Bronze→Silver→Gold + POI catchment) are not backed by artifacts on disk. The grade is then "nice repo, no evidence".
- **SFA has target leakage.** `run_pipeline.py:278-282` fits SFA with `y = observed_max_monthly_liters` and `X = feature_cols_numeric` that **includes `observed_mean`, `observed_median`, `observed_p90`, `observed_p95`** — all derived from the same monthly-volume series. The frontier model basically learns `max ≈ p95 + tiny`, which forces `sigma_u → 0`, `lambda → 0`, `TE ≈ 1`. The "second methodology track" is fictitious until those four columns are dropped from `sfa_X`.
- **"Manski bands" are not Manski bands.** `src/reporting/manski.py:25,54-60` defines `manski_upper = max(peer_p99, lower_bound × min(cap_uplift, 6.0))` with a hard-coded `DEFAULT_MAX_UPLIFT = 6.0`. That's an empirical cap with a famous label glued on. A real Manski bound needs an exogenous identifying assumption; here the upper is mechanically tied to the same `cap_table` used for the point estimate, so the "honest disclosure interval" is decorative.

---

# Verification of Round-1 Blockers

| ID | Blocker (Round 1) | Status | Evidence |
| --- | --- | --- | --- |
| **B1** | Submission column `row_id` → `Outlet_ID` | **PASS** | `Results/teamname_predictions.csv` line 1: `Outlet_ID,Maximum_Monthly_Liters`. Written by `run_pipeline.py:320` (`sub = preds[["Outlet_ID", "Maximum_Monthly_Liters"]]`). |
| **B2** | Submission row count 914 → 20,000 | **PASS** | File is 20,001 lines (header + 20,000). Legacy 914-row file moved to `Results/legacy_914row_predictions.csv` (915 lines, still has `row_id` schema) — kept as backup, **must not be uploaded**. |
| **B3** | `data/silver_rejected/` actually populated | **FAIL — must-do blocker** | `Glob` of `data/silver_rejected/*.csv` returns **zero files**; only `.gitkeep`. Population happens inside `run_pipeline.silver_clean()` via `write_rejected(qc, SILVER_REJECTED_DIR)` (line 168) and `write_silver(... coords_rej)` (lines 177-179). **The team has not yet executed `python run_pipeline.py`.** Without it the report's claim "480 coordinate + 9,606 transaction rows quarantined" (`README.md:93`) has no artifact behind it. |
| **B4** | `src/*.py` modules exist (not just notebooks) | **PASS** | 23 Python files under `src/`. Modeling layer present: `lower_bound.py`, `constraint_score.py`, `frontier.py`, `sfa.py`, `conformal.py`, `censored_qr.py`, `caps.py`, `predict.py`. Reporting layer present: `manski.py`, `dag.py`, `sensitivity.py`, `validation.py`. Quality + cleaning + features layers also present. |
| **B5** | POI pipeline shipped | **PARTIAL — must-do blocker** | `poi_pipeline/{01_download_pbf, 02_extract_pois, 03_build_features, 04_quality_audit}.py` + `config.py` + `README.md` + `src/` all exist. **But `poi_pipeline/output/*` is empty** (Glob returns nothing). `run_pipeline.py:197` guards with `if POI_FEATURES_PARQUET.exists()` and silently continues without POI. The README claims POI is wired in; today, in this checkout, no POI features are loaded by the gold builder. |

**Net**: 3 of 5 truly fixed (B1, B2, B4). B3 and B5 are *code complete but artifact missing* — i.e. they depend on the team actually running both pipelines before submission. If either run is skipped, the round-1 BLOCKER returns.

---

# Theatre vs Substance Audit

## `src/modeling/constraint_score.py` — partial substance, false orthogonality claim

The signals are real, but the docstring claim "three **orthogonal** signals" (line 7-13) is not enforced anywhere.

- **Frontier residual z** (`_frontier_residual_z`, lines 38-42): real. `(peer_q90 - observed_max) / peer_sd` clipped to `[-3, 5]`. This is the honest signal.
- **Plateau** (`_plateau_signal`, lines 45-72): real but **binary** — `plateau = float((months_since_max > 6) and (var_ratio < 0.4))`. After the z-scaling at line 124 (`z_plateau = plateau_signal * 1.5`), the plateau term contributes either **0 or 0.45** to the logit (weight 0.3 × 1.5). It's a coarse step, not a signal — most outlets sit at 0.
- **PCA capacity** (`_pca_capacity`, lines 75-85): is **literally PC1 of `[Cooler_Count, sku_breadth, catchment_density_score]`** (line 95-99). For these three size-monotone variables, PC1 *is* the size axis. The score then **flips its sign** at line 125 (`z_capacity_inv = -df["capacity_pc1"]`), so **small outlets now get higher constraint score**. Round-1 bug was "constraint score rewards big outlets". The new bug is the mirror image: "constraint score rewards small outlets". Neither is a constraint signal.
- **The orientation hack** at lines 82-85 is non-deterministic across row order: `if pc[X.shape[0] // 2] < 0 and X.iloc[X.shape[0] // 2].sum() > X.values.mean(): pc = -pc`. The flip depends on the median *row*, which changes if rows are reshuffled upstream.
- **Orthogonalisation claim is unsupported**: the three signals are independently z-scored and weighted, but no Gram-Schmidt or partialing out happens. They are likely positively correlated (large `frontier_residual_z` outlets tend to be smaller, which also pushes `-capacity_pc1` up). Net effect: the frontier-residual signal is double-counted via the capacity PC.

**Verdict**: real math wrapped around a misframed claim. Honest fix: drop `capacity_pc1` from the score, or regress capacity_pc1 on frontier_residual_z and use the residual.

## `src/modeling/sfa.py` — math is correct, but pipeline wiring leaks the target

The module itself is real:

- `_neg_log_lik` (lines 50-65) is the standard Aigner-Lovell-Schmidt (1977) closed-form: `f(eps) = (2/sigma) * phi(eps/sigma) * Phi(-lambda*eps/sigma)`. The log-form is numerically stable.
- `technical_efficiency` (lines 107-127) is the textbook Jondrow-Lovell-Materov-Schmidt (1982) `E[u|eps]` with `sigma_star^2 = sigma_v^2 * sigma_u^2 / sigma^2`. Then `TE = exp(-E[u|eps])`. Not a wrapper around `np.exp(-residual)`.

**But the *use* in `run_pipeline.py:276-291` is broken.**

```278:282:autokaggle/competition/run_pipeline.py
            sfa_X = X[feature_cols_numeric].copy()
            sfa_fit = fit_sfa(sfa_X, y, log_target=True)
            te = technical_efficiency(sfa_fit, sfa_X, y, log_target=True)
            sfa_frontier = sfa_predict_frontier(sfa_fit, sfa_X, log_target=True)
            print(f"     SFA: sigma_v={sfa_fit.sigma_v:.3f}, sigma_u={sfa_fit.sigma_u:.3f}, lambda={sfa_fit.lambda_:.3f}, converged={sfa_fit.converged}")
```

`y = gold["observed_max_monthly_liters"]` (line 253) and `feature_cols_numeric` (lines 227-246) contains `observed_mean_monthly_liters`, `observed_median_monthly_liters`, `observed_p90_monthly_liters`, `observed_p95_monthly_liters`. All four are computed from the **same** monthly-volume series as the target `max`. So the regression `log(max) ~ ... + p95 + p90 + ...` will hit `sigma_u ≈ 0`, `lambda ≈ 0`, `TE ≈ 1` for almost every outlet. Hostile judge:

> "Show me the distribution of your technical efficiency. If `sigma_u` collapses to zero you are reporting noise."

**Fix**: drop the 4 percentile columns + `observed_mean_monthly_liters` from `sfa_X` before the call. Use *structural* / *external* covariates only (`Cooler_Count`, `sku_breadth`, POI decay scores, catchment density, cannibalisation_count_200m, holiday count, seasonality). Without that, the SFA "parallel methodology track" is theatre.

There is also a half-normal vs truncated-normal mismatch: the docstring says "truncated-normal" (line 6) but the parameterisation has no `mu_u`, so this is plain half-normal. A judge who has read the brief will ask.

## `src/reporting/manski.py` — empirical caps with a label

```25:60:autokaggle/competition/src/reporting/manski.py
DEFAULT_MAX_UPLIFT = 6.0  # absolute ceiling on multiplier vs lower bound
...
    if cap_table is not None:
        df = df.merge(
            cap_table[["Outlet_Type", "Outlet_Size", "cap_uplift"]],
            on=["Outlet_Type", "Outlet_Size"],
            how="left",
            suffixes=("", "_cap"),
        )
        cap = df["cap_uplift"].fillna(max_uplift)
    else:
        cap = pd.Series(max_uplift, index=df.index)

    upper_a = peer_p99.fillna(df["observed_max_monthly_liters"])
    upper_b = df["lower_bound"] * np.minimum(cap, max_uplift)
    df["manski_upper"] = np.maximum(upper_a, upper_b)
```

Three problems:

1. **Not a Manski bound.** A Manski (2003) worst-case upper for right-censored latent demand is essentially **unbounded** without auxiliary restrictions, or — at most — the largest defensible "demand support" assumption you can write down. `max(peer_p99, lb × cap)` is an *empirical* ceiling. Labelling it "Manski" invites a viva-killing question: "What identifying assumption gives you that upper?"
2. **Uses the same `cap_table` as the point estimate.** `apply_caps` (in `caps.py:47-62`) already clips `potential_capped` at `cap_uplift × historical_max`. Then `compute_manski_bands` builds its upper from the **same** `cap_uplift` via `lower_bound × cap`. The "interval" is mechanically tied to the point estimate — the upper is at most ~6× the lower, and often less. Judges will read this as "point = upper", which is not partial identification, it's a confidence-band illusion.
3. **`DEFAULT_MAX_UPLIFT = 6.0` is a magic number.** Round-1 Skeptic killed the team for `{Small: 3.0, ..., XL: 4.5}` as "vibes-coded". The cap is now bootstrap-derived, fine — but the *Manski* ceiling is back to 6.0 vibes. The README claims "anything above this would require unverifiable assumptions" (line 12-13 of `manski.py`); the unverifiable assumption is `6.0`.

**Fix**: either (a) remove the "Manski" label and call this an "empirical demand band", or (b) make the upper sigma_u-quantile under SFA (e.g. `frontier × 1/TE_q10`) which is at least anchored to a model.

## `src/reporting/validation.py` — gates set too loose, V5 dead

Six checks. Three are real, three are theatre:

- **V1 schema + row count**: real. Gates `Outlet_ID + Maximum_Monthly_Liters + 20000`. This is the disqualifier check from round 1 — good that it exists.
- **V2 NaN / negative / unique**: real, cheap.
- **V3a Outlet_ID in master**: real, cheap.
- **V3b `>= 99%` outlets above historical max**: **mechanical pass**. `predict.py:58` enforces `np.maximum(potential_raw, lower_bound)`, and `lower_bound >= median` by construction in `lower_bound.py:46`. So this check cannot fail in normal runs. It is *evidence the floor exists*, not validation.
- **V4 median uplift in `[1.05, 2.5]`**: window is **1.45 wide**. With a sigmoid constraint score around 0.5 and cap ~3x, the median uplift will land in `[1.1, 1.8]` for almost any reasonable input. Window is wide enough to swallow most pipeline bugs.
- **V5 cap-binding rate < 25% at `hist_max × 5.9`**: this only catches outlets pegged at the **absolute** 6.0× ceiling, not outlets pegged at their **bucket** cap. If `Outlet_Type=A, Outlet_Size=Small` bucket has `cap_uplift=2.1` and 100% of that bucket binds at 2.1×, V5 still says 0%. V5 is dead unless `cap_uplift` happens to be near 6.0.

**Fix**: V5 should compare each prediction to its own bucket's `cap_uplift × historical_max`. Replace `hist_max * 5.9` with the joined `cap_uplift * hist_max`. Then "cap-binding rate" actually measures cap binding.

---

# 3 Hardest Judge Questions That Remain

> Defensible answers below assume the team executes the fixes I list. Without the fixes, the answers are aspirational.

### Q1. "Your SFA fit has the q90 and p95 of monthly volume on the right-hand side of a regression where the left-hand side is the *max* of monthly volume. That's target leakage. What is your `sigma_u` and what does it imply about your technical-efficiency claim?"

- **Honest answer**: today, `sigma_u` collapses toward 0 and TE is ~1 for every outlet, because `log(max) ~ p95` is near-perfect. The "second methodology track" doesn't produce a usable signal until I rebuild `sfa_X` from structural and external features only (cooler / SKU / POI decay scores / catchment / cannibalisation / seasonality / holidays). After that fix the lambda is meaningful and the JLMS `TE` is a real per-outlet constraint indicator.

### Q2. "Your `manski_upper` is `max(peer_p99, lower_bound × cap_uplift)` with cap ≤ 6.0. Manski-style partial identification requires an identifying assumption. Which assumption did you adopt, and where in the code is it enforced?"

- **Honest answer**: the framework as shipped is an *empirical* demand band, not a Manski bound. The defensible identifying assumption is the "no super-peer" assumption — the true demand of an outlet does not exceed the 99th-percentile observed demand of structurally similar peers (same Outlet_Type × Outlet_Size). Under that assumption `upper = peer_p99` is identified. The `6.0` ceiling is a sanity hatch when peer_p99 is missing and should be re-labelled as such, not as Manski.

### Q3. "Your `constraint_score` weights are `0.5 / 0.3 / 0.2`. The 0.2 term is PC1 of `Cooler_Count + sku_breadth + catchment_density`, which is the size axis, and you flip its sign. So you are now telling me that smaller outlets are more constrained. Why?"

- **Honest answer**: the claim being made is that *capacity-constrained* outlets (few coolers, narrow SKU breadth) cannot serve latent demand they have. The defensible version is to drop PC1 (which is collinear with frontier-residual via outlet size) and use **per-bucket residuals**: regress `Cooler_Count` on `peer_q90` within `Outlet_Type × Outlet_Size`, take the residual, and use the negative of that as the capacity-shortage signal. That is orthogonal-by-construction. The current PC1 design double-counts size.

---

# Pre-mortem Scenarios A / B / C

### A. Team submits the v1 file by accident (didn't run new pipeline)

- **What happens**: `Results/legacy_914row_predictions.csv` has `row_id,Maximum_Monthly_Liters` and 915 lines. Uploading it = automatic scoring failure (wrong schema **and** missing 19,086 outlets).
- **Severity**: **CRITICAL — single-button disqualifier.** Worst-case loss of the whole prediction track.
- **Mitigation**:
  1. **Move** `legacy_914row_predictions.csv` out of `Results/` to `Results/_legacy_do_not_submit/`. Name-collision-proofing > documentation.
  2. Add a final assertion in `run_pipeline.write_submission()`: `assert list(sub.columns) == ["Outlet_ID", "Maximum_Monthly_Liters"] and len(sub) == 20_000`. The validation suite catches this *after* the fact; the assertion catches it at write time.
  3. Stop writing the duplicate `teamname_predictions_full_20000.csv` (lines 324-325). One file. Round-1 Skeptic flagged this same "two CSVs" smell.

### B. POI pipeline fails on the day (no internet, OSM down)

- **What happens**: `01_download_pbf.py` cannot reach Geofabrik. `poi_features.parquet` is never written. `run_pipeline.py:197` sees `POI_FEATURES_PARQUET.exists() == False`, prints "no POI features at ...; proceeding without external POI", and continues. The submission CSV is still produced.
- **Hidden cost**: the README (lines 67-69, 97-99) and `final_report.md` (not yet written) will claim POI is part of the methodology. Judges open the gold parquet, find zero `*_decay_score` columns, conclude the team lied.
- **Severity**: **HIGH on Method/DE rubric**, because POI is the headline external-data deliverable.
- **Mitigation**:
  1. `run_pipeline.py` must write `Results/run_manifest.json` recording every optional stage: `{"poi_loaded": bool, "sfa_converged": bool, "censoring_correction_applied": bool, ...}`.
  2. The 5-page PDF must read that manifest and **conditionally** state "POI features were [loaded / **not loaded** due to offline-only run]". No silent over-claiming.
  3. Cache the PBF file under `poi_pipeline/data/raw/sri-lanka-latest.osm.pbf` **now**, before submission day. `01_download_pbf.py` is described as idempotent — prove that by running it tonight.

### C. SFA convergence fails (likely on log-volume with sparse outlets)

- **What happens**: `run_pipeline.py:289-291`:

  ```289:291:autokaggle/competition/run_pipeline.py
          except Exception as e:
              print(f"     SFA failed: {type(e).__name__}: {e} -- continuing without SFA")
              sfa_out = None
  ```

  Then frontier ensemble at line 309-311 collapses to **XGBoost q90 only**. The submission is still produced. The README still claims a 60/40 ensemble.
- **Twist**: even when SFA "succeeds" with target leakage (Scenario per Theatre Audit above), `sigma_u → 0` produces `te ≈ 1` for everyone — the ensemble weight `0.4 * sfa_frontier` is then effectively `0.4 * exp(X @ beta)` which mirrors XGBoost in shape. So the "ensemble" silently degenerates either way.
- **Severity**: **HIGH on Method rubric** (claims exceed execution); **MEDIUM on prediction quality** (XGBoost q90 alone is decent).
- **Mitigation**:
  1. Same `run_manifest.json` fix as B — record `sfa_converged`, `sigma_u`, `lambda`.
  2. Fix the leakage first; then convergence is also more likely (the residual variance becomes large enough that `lambda` is identifiable).
  3. If SFA still fails after the fix, fall back to a SECOND independent frontier — e.g. **quantile random forest at q90** — so the "ensemble" claim survives. Do not let the ensemble silently collapse to a single model.

---

# Honest Strengths

1. **The disqualifier is gone.** Schema is `Outlet_ID + Maximum_Monthly_Liters`, row count is 20,000, every ID matches `outlet_master`. Round-1 Blocker B1/B2 are clean.
2. **`run_pipeline.py` is a real orchestrator, not a notebook.** One entry point, no CLI flags, CONFIG block at the top, deterministic order, prints + writes audit files at every step. This is exactly the DE-rubric primitive worth points.
3. **`latent_potential` formula is finally honest.** `lower + cs × (frontier - lower)` with **one** bootstrap cap, no `^1.25` magic, no `clip(0, 0.65)`. The round-1 "quadruple throttle" was the worst single thing in v1; it is gone.
4. **SFA math is correct in isolation.** `_neg_log_lik` and `technical_efficiency` are standard Aigner-Lovell-Schmidt + Jondrow-Lovell-Materov-Schmidt closed forms (`sfa.py:50-65, 107-127`), not pretty wrappers around `np.exp`. The leakage problem is a wiring bug, not a maths bug — easy to fix.
5. **`chernozhukov_hong_correction` is implemented honestly.** Logistic propensity → threshold mask → refit q90 only on `P(censored) < tau` rows (`censored_qr.py:108-143`). The censoring proxy is weak (binary plateau / stuck-at-max), but the *procedure* is defensible Round-2 methodology.
6. **POI pipeline is engineering-real.** Geofabrik PBF + pyrosm local parse + BallTree haversine + 9 categories + decay scores + coverage caveat (`poi_pipeline/README.md:46-63`). No Overpass-per-outlet spam. This is the round-1 D-grade "POI absent" lift, *if* the team actually runs the four scripts before submission.

---

# Updated Grade

| Dimension | Round 1 | Round 2 (if run + leakage fixed) | Round 2 (as-shipped today) |
| --- | --- | --- | --- |
| DE / lakehouse | C | B+ | C+ (artifacts not on disk yet) |
| Method | D | B | C+ (SFA leakage, fake Manski) |
| POI | F | B | D (pipeline exists, output empty) |
| GenAI transparency | C+ | C+ | C+ (unchanged) |
| Risk of DQ | HIGH | LOW | MEDIUM (legacy 914 file still in Results/) |

**Was D+. Now B- if `run_pipeline.py` + the 4 POI scripts execute cleanly before submission and the SFA leakage is fixed. C+ if they submit on the strength of code-on-disk without re-running. B / B+ achievable only by also (a) dropping the "Manski" label or anchoring the upper to SFA, (b) deleting the legacy 914-row CSV from `Results/`.**

The intellectual ceiling went from "polite thank-you" to "credible mid-pack with a real story". The execution risk is still high because three things must all hold on the day: pipeline runs, POI runs, SFA covariate set is fixed. Two of three is a soft B-; three of three is a B+.

---

# 7-Line Summary

1. **B1 (column) and B2 (rows) PASS.** Submission schema is `Outlet_ID, Maximum_Monthly_Liters` with 20,000 rows. Legacy 914-row file is still sitting in `Results/` and is a one-click disqualifier — move it out.
2. **B3 (rejected store) and B5 (POI output) are CODE-COMPLETE but ARTIFACT-MISSING.** `data/silver_rejected/` and `poi_pipeline/output/` are empty until the team actually runs `run_pipeline.py` plus the 4 POI scripts. Treat this as a must-do blocker before submission.
3. **B4 (src modules) PASS.** 23 Python modules exist with the right names and responsibilities.
4. **Biggest hidden bug**: `run_pipeline.py:278-282` fits SFA with `observed_p90 / p95 / median / mean` on the right-hand side of `log(observed_max)` — target leakage forces `TE ≈ 1` and makes the "second methodology track" a no-op. Drop those 4 columns from `sfa_X`.
5. **"Manski bands" are mislabelled empirical caps.** `manski.py` uses the same `cap_table` as the point estimate and a hard-coded `6.0` ceiling. Either re-anchor the upper to SFA's `1/TE_q10` or rename to "demand band".
6. **Constraint-score "orthogonality" is unsupported.** PCA capacity component is the size axis with flipped sign; it double-counts the frontier-residual signal. Use partial residuals instead.
7. **Updated grade: D+ → B- as-shipped, B / B+ if the pipeline runs and the SFA leakage + Manski mislabel are fixed.** The team has gone from "narrative without receipts" to "receipts pending the run button".
