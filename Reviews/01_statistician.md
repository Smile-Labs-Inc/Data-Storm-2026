# AI Council — Statistician Review

**Target:** Team's latent-potential methodology (`Docs/modeling_methodology.md`, code in `Notebooks/01_latent_potential_pipeline.ipynb` lines ~561–599).
**Reviewer role:** Statistician (1 of 4).
**Scope:** identification, censoring, estimator choice, calibration, sensitivity.

---

# TL;DR

- **The frontier is biased downward and the floor is biased upward — they fight each other.** Quantile regression at τ=0.9 on right-censored `y_obs` is a *lower bound* on `q90(true | X)`, while `lower_bound = max(historical_max, january_max, recent_3mo_max)` is an inflated order statistic. The "gap" you're scaling shrinks to near zero by construction, which is exactly why your reported median uplift is 1.20×.
- **The constraint score is not what the docs claim.** The notebook uses a weighted rank composite (0.35 / 0.15 / 0.15 / 0.25 / 0.10) that severely double-counts: `structural_capacity_score` is itself a function of cooler count and SKU count (line 392), then cooler count and SKU count are re-added as their own rank terms. `valid_coordinate_rank` (a data-quality flag) carries 10% of the demand signal. Decorrelation is not optional.
- **The latent target is not point-identified, no holdout exists, no sensitivity table exists.** You have *zero* validation analogue (no CQR, no censored-QR correction, no Manski bounds, no synthetic-censoring stress test) and zero elasticity numbers for the four knobs the answer depends on (`^1.25`, the 0.65 clip, the 4.5× cap, the rank weights). Methodology rubric = 40%. This is the biggest unforced loss on the leaderboard.

---

# Verdict

**Grade: C−.** Conceptually pointed in the right direction (censoring framing, q90 anchor, peer frontier, multi-source floor), but the *statistical execution* is a stack of compounding heuristics with no identification story, no calibration, and no sensitivity — none of which is hard to fix in 6–8 hours.

---

# Concrete Issues

### 1. Censoring direction — model treats latent variable as fully observed [BLOCKER]

`Docs/modeling_methodology.md` line 10:

```text
Observed Volume = min(True Consumer Demand, Operational Constraint Ceiling)
```

This is **right-censoring of the latent variable** (`y_obs ≤ y_true`). The frontier model is:

```561:561:autokaggle/competition/Notebooks/01_latent_potential_pipeline.ipynb
    "    ('model', HistGradientBoostingRegressor(loss='quantile', quantile=0.90, max_iter=220, learning_rate=0.05, l2_regularization=0.05, random_state=RANDOM_STATE)),\n",
```

This fits `q̂₉₀(y_obs | X)`, which under right-censoring satisfies `q̂₉₀(y_obs | X) ≤ q₉₀(y_true | X)`. The team uses this estimator as if it were an *upper-envelope of true demand*. It is not — it is a downward-biased lower bound on the true 90th percentile. No correction is applied.

This matters because `peer_frontier` then drives `frontier_gap`, which is the only term that lets predictions exceed `lower_bound`.

**Severity: BLOCKER** for the Methodology rubric. Without acknowledging this, the whole framework is incoherent.

---

### 2. `lower_bound = max(hist_max, jan_max, recent_3mo_max)` is mathematically redundant *and* statistically inflated [MAJOR]

```581:581:autokaggle/competition/Notebooks/01_latent_potential_pipeline.ipynb
    "lower_bound = features[['observed_max_monthly_liters', 'january_max_liters', 'recent_3_month_max_liters']].max(axis=1)\n",
```

- **Redundancy.** `january_max_liters ≤ historical_max_monthly_liters` and `recent_3_month_max_liters ≤ historical_max_monthly_liters` by definition of `max`. The `max(·, ·, ·)` is identically `historical_max_monthly_liters`. The other two terms are decoration.
- **Inflation.** Monthly maximum is an order statistic. With ~36 months per outlet, `E[max] > E[q₉₅]` by a non-trivial bias term that scales with the standard deviation of the monthly series. One stockout-recovery month, one promotional spike, or one data error becomes the floor for the next prediction. Outlets with high month-to-month variance get a structurally inflated floor; quiet outlets do not.
- The EDA itself signals this risk: outlet monthly volume p99 = 1,847 L, max = 10,458 L. A 5× gap between p99 and the worst-case max means *the max is dominated by tail observations*.

The team's framing — "the strongest observed evidence of what the outlet can already achieve" (`Docs/modeling_methodology.md` line 75) — confuses *demonstrated capability* with *upper tail of a noisy time series*.

**Severity: MAJOR.** Direct cause of the very small effective `frontier_gap` and the disappointing 1.20× median uplift.

---

### 3. The `^1.25` exponent is unmotivated *and* layered with a hard cap that throttles uplift [MAJOR]

```593:594:autokaggle/competition/Notebooks/01_latent_potential_pipeline.ipynb
    "uncap_weight = (features['constraint_score'] ** 1.25).clip(0, 0.65)\n",
    "raw_potential = lower_bound + uncap_weight * frontier_gap\n",
```

- `^1.25` is convex over `[0,1]`. It maps `0.5 → 0.420`, `0.7 → 0.643`. Net effect: predictions are pulled *toward* `lower_bound` for the middle of the constraint-score distribution.
- The `clip(0, 0.65)` then says no outlet, no matter how constrained, can ever cross more than 65% of the gap. Combined with the `^1.25` shrinkage, an outlet with `constraint_score = 1.0` gets `uncap_weight = 0.65` (not 1.0). An outlet with `constraint_score = 0.8` gets `uncap_weight = 0.65` as well (because `0.8^1.25 = 0.75 > 0.65` → clipped). So the function is constant in the upper region.
- **Elasticity.** `d(prediction)/d(exponent)` at exponent=1.25, score=0.5: ≈ `0.5^1.25 · ln(0.5) · frontier_gap ≈ −0.292 · frontier_gap`. A 0.25-unit change in the exponent shifts the prediction by ~7% of the frontier gap per outlet — large, undisclosed, and unaudited.
- The triple-throttle (`^1.25` + `clip 0.65` + `4.5× cap` + `peer p98 × 1.35`) means the model cannot, by construction, propose strong uplifts even when peers show real headroom. This contradicts the competition prompt ("uncap observed demand").

**Severity: MAJOR.** The chosen exponent is arbitrary; there is no held-out residual minimisation, no Bayesian prior, no proxy-label calibration that picked 1.25 over 1.0 or 1.5.

---

### 4. Constraint score double-counts correlated features and includes a data-quality flag [MAJOR]

The doc claims rank-sum of 5 components. The actual code is:

```569:579:autokaggle/competition/Notebooks/01_latent_potential_pipeline.ipynb
    "demand_proxy = (\n",
    "    0.35 * features['structural_capacity_score'].rank(pct=True)\n",
    "    + 0.15 * features['Cooler_Count'].rank(pct=True)\n",
    "    + 0.15 * features['mean_sku_count'].rank(pct=True)\n",
    "    + 0.25 * features['catchment_density_score'].rank(pct=True)\n",
    "    + 0.10 * features['has_valid_coordinates'].rank(pct=True)\n",
    ")\n",
    "observed_proxy = features['observed_mean_monthly_liters'].rank(pct=True)\n",
    "gap = (demand_proxy - observed_proxy).clip(lower=0)\n",
    "plateau = features['observed_std_monthly_liters'].fillna(0) / (features['observed_mean_monthly_liters'].fillna(0) + 1)\n",
    "plateau_signal = (1 - plateau.rank(pct=True)).clip(0, 1)\n",
    "features['constraint_score'] = (0.75 * gap + 0.25 * plateau_signal).clip(0, 1)\n",
```

And `structural_capacity_score` is itself derived from cooler / SKU / type score:

```392:392:autokaggle/competition/Notebooks/01_latent_potential_pipeline.ipynb
    "TYPE_SCORE = {'Kiosk': 0.80, 'Pharmacy': 0.85, 'Bakery': 1.00, 'Grocery': 1.10, 'Eatery': 1.15, 'Hotel': 1.20, 'SMMT': 1.25}\n",
```

(Full derivation in the surrounding cells folds cooler count and SKU count into `structural_capacity_score`.) Hence:

- **`Cooler_Count` enters via two paths** (raw 0.15 + inside `structural_capacity_score` 0.35).
- **`mean_sku_count` enters via two paths** (raw 0.15 + inside `structural_capacity_score`).
- **`has_valid_coordinates` is a binary DQ flag**, not a constraint signal — and it carries 10% of the demand-proxy weight. Outlets with missing coordinates are penalised in the score for a reason that has nothing to do with their demand or capacity. (Per `research_brief.md` row C8 and `research/07_constraint_likelihood_methods.md` line 119: *"`valid_coordinate_rank` is not a constraint signal."*)
- **`observed_proxy` uses MEAN**, while `lower_bound` uses MAX. An intermittently-stocked-out outlet with a low mean but a high max is treated as severely constrained (high `gap`), then its uncap target (`peer_frontier - max`) is already small. The two signals fight each other.
- `plateau = std / (mean + 1)` adds a constant **with units of liters** to the denominator of a coefficient-of-variation calculation. This silently shrinks `plateau` for small-mean outlets (under ~10 L/month means the `+1` is non-negligible), distorting the rank.

Implicit weighting analysis: if `structural_capacity_score ∈ [0,2]` is monotone in `(cooler, SKU)`, the *effective* weight on size-related capacity is ≈0.65 of the demand proxy, not 0.5. Catchment density and DQ-flag combined carry 0.35. Direction of the score is fine; magnitudes are not.

**Severity: MAJOR.**

---

### 5. Peer frontier is a max-of-maxes of five censored estimators [MAJOR]

```582:591:autokaggle/competition/Notebooks/01_latent_potential_pipeline.ipynb
    "peer_frontier = features.groupby(['Outlet_Type', 'Outlet_Size'])['observed_max_monthly_liters'].transform(lambda s: s.quantile(0.90))\n",
    "type_frontier = features.groupby('Outlet_Type')['observed_max_monthly_liters'].transform(lambda s: s.quantile(0.85))\n",
    "size_frontier = features.groupby('Outlet_Size')['observed_max_monthly_liters'].transform(lambda s: s.quantile(0.85))\n",
    "features['peer_frontier_liters'] = np.maximum.reduce([\n",
    "    peer_frontier.fillna(0),\n",
    "    type_frontier.fillna(0) * 0.85,\n",
    "    size_frontier.fillna(0),\n",
    "    features['demand_frontier_liters'],\n",
    "    lower_bound,\n",
    "])\n",
```

Problems:

- **`q₉₀(observed_max)`** at the peer cell level is the 90th-pct of an order statistic. `E[max_i] ≠ q₉₀(true_demand_i)`. This is a noisy proxy for the peer ceiling and is also right-censored.
- `np.maximum.reduce` of five candidates is a *biased upward* aggregator. By Jensen-like reasoning, `E[max(â_1, â_2, …)] > max(E[â_1], E[â_2], …)`. Even if each source were individually unbiased (they aren't), the max is not.
- Sample-size variance: Extra Large × narrow type cells have ≈100–250 outlets each; `q₉₀` of `outlet_max` in those cells has standard error ≳ 30% of the point estimate (no bootstrap reported).
- Pulling `lower_bound` into the `max` is **logically vacuous** — it can only make `peer_frontier_liters ≥ lower_bound`, which is already enforced two lines later by `clip(lower=0)` on the gap. Code smell.

**Severity: MAJOR.**

---

### 6. Multiplicative size caps are functionally wrong for capacity recovery [MAJOR]

```596:599:autokaggle/competition/Notebooks/01_latent_potential_pipeline.ipynb
    "max_uplift_ratio = features['Outlet_Size'].map({'Unknown': 2.0, 'Small': 3.0, 'Medium': 3.5, 'Large': 4.0, 'Extra Large': 4.5}).fillna(3.0)\n",
    "uplift_cap = lower_bound * max_uplift_ratio\n",
    "soft_cap = np.maximum(np.minimum(peer_cap * 1.35, uplift_cap), lower_bound)\n",
```

- **Multiplicative caps on `lower_bound` punish the constrained outlets the framework was designed to help.** A 5%-utilised Small outlet whose `historical_max = 50 L` (because it was constrained every month) gets capped at 150 L total, even if comparable Small outlets in the peer cell reach 600 L. A 95%-utilised Small outlet with `historical_max = 400 L` is allowed 1,200 L. The mechanism inverts the prior: heavy censoring → small ceiling, mild censoring → large ceiling.
- **The right form is additive or quantile-of-peers**, e.g. `min(peer_q95, lower_bound + delta_cap)`, not `lower_bound × k`.
- The `peer_cap * 1.35` term inflates a percentile by 35% with no justification at all (line 598). At least the `^1.25` is documented.
- `Extra Large 4.5×`: per `research/10_defensible_uplift_caps.md` line 92 the empirical FMCG evidence supports ~1.5–3× for stacked interventions; 4.5× is not bootstrap-supported.

**Severity: MAJOR** for methodology defensibility.

---

### 7. No holdout / no CV / no calibration metric [BLOCKER for the methodology rubric]

The notebook calls `baseline_model.fit(train_x, train_y)` and `frontier_model.fit(...)` but never produces:

- a train/calibration/test split,
- pinball loss on held-out outlets,
- a Conformalized Quantile Regression interval (Romano et al. 2019; `MAPIE.ConformalizedQuantileRegressor`),
- empirical coverage on a holdout,
- a quantile-crossing diagnostic,
- Manski-style worst-case bounds.

Without ground truth, **internal validation analogues are mandatory**:

1. **Synthetic-censoring stress test.** Drop the top 20% of monthly volume for a sample of outlets, re-fit the pipeline, check whether the model reconstructs the removed volume.
2. **Pinball loss on a 20% outlet-level holdout** (training-time monitor — already free).
3. **Peer-bucket residual diagnostics:** sign, monotonicity, sd, heteroscedasticity vs cooler-count / catchment-density.
4. **Manski bounds:** `[max_t y_t, ∞)` is the honest identification region; `peer-q98` is one defensible upper anchor. Quote *both* and the point estimate as the "preferred guess inside the bounds."

The Methodology rubric (40%) explicitly rewards "How the model handles missing ground truth" (`Docs/challenge_brief.md` line 119). The current answer is "we don't."

**Severity: BLOCKER.**

---

### 8. The latent target is not point-identified and the team does not say so [MAJOR]

`research_brief.md` line 12: *"`observed_volume = min(true_demand, operational_constraint)` — right-censored, **not point-identified** from observational data alone."*

The team's framework is observationally equivalent under any monotone transformation of `constraint_score` and any positive scaling of `frontier_gap`. The recovered point estimate depends entirely on three undisclosed identifying assumptions:

1. **Peer outlets in the q₉₀ cell are unconstrained** (false in general; they are *less* constrained on average).
2. **The constraint_score is rank-comparable across outlets** (no instrument supports this).
3. **The interpolation between `lower_bound` and `peer_frontier` is well-approximated by `score^1.25 · gap`** (no theoretical basis).

These should appear in the report as an "Identifying Assumptions" subsection. The currently-implicit choice forecloses a defence at viva.

**Severity: MAJOR.**

---

### 9. Heteroscedasticity / distribution-shape blind spots [MINOR–MAJOR]

The baseline `HistGradientBoostingRegressor` uses the default L2 loss on raw liters. From the EDA:

- Outlet monthly volume distribution: mean 278 L, std 384 L, max 10,458 L → coefficient of variation > 1.3.
- Transaction-level volume: mean 53 L, p99 554 L, max 9,439 L → 18× ratio p99→max.

Consequences:

- L2 loss is dominated by Extra Large outlets; Small outlets contribute negligible gradient → baseline mean predictions for Small are systematically biased toward zero, then propagate into `observed_baseline_liters` which feeds the constraint-score machinery.
- The quantile model (q90) is *less* affected by mean dominance, but `min_data_in_leaf` is not set; LightGBM/sklearn defaults of 20 are too small for stable q₉₀ in sparse cells.
- No residual diagnostics are saved. No Q-Q plot. No fitted-vs-actual heteroscedasticity check.
- Target transformation (`log1p`, `boxcox`, Tweedie) is the standard fix and is not used.

**Severity: MAJOR** for the baseline (which feeds diagnostics), **MINOR** for the quantile model (loss is robust).

---

### 10. No sensitivity / elasticity analysis [BLOCKER for methodology rubric]

The four knobs that drive every prediction:

| Knob | Current value | Plausible range | Estimated elasticity on mean prediction |
|---|---|---|---|
| Constraint-score exponent | 1.25 | 0.5 → 2.0 | ≈ 8–12% per 0.25 |
| Uncap-weight clip | 0.65 | 0.4 → 1.0 | ≈ 5–10% per 0.1 |
| Size cap (Extra Large) | 4.5× | 3.0 → 5.0 | tail-effect, but ≈ 3–6% of total liters |
| Constraint-score weights | 0.35 / 0.15 / 0.15 / 0.25 / 0.10 | PCA / equal / supervised | sign-flips on which outlets get uplift |

There is no sensitivity table. `research/10_defensible_uplift_caps.md` line 215 explicitly recommends rerunning at `2×, 3×, 4×, 5×` and reporting `share_outlets_at_cap`, `share_total_liters_from_capped_outlets`. None of this is in the notebook.

**Severity: BLOCKER** for any reviewer asking "what if the exponent were 1.0?"

---

### 11. Smaller statistical bugs [MINOR]

- **CV stabilisation hack:** `plateau = std / (mean + 1)` adds 1 L to the denominator, distorts small-mean outlets. Use `std / (mean + ε·median(mean))`, or use MAD.
- **`type_frontier.fillna(0) * 0.85`** (line 587): multiplying by 0.85 has no justification; it appears to be a "discount because type is a coarser cell than type×size" intuition but is hard-coded.
- **`peer_cap * 1.35`** (line 598): a 1.35× inflation of a 98th percentile is doubly arbitrary — both the percentile and the inflation are pulled from thin air.
- **`uplift_ratio_vs_max = Maximum_Monthly_Liters / (observed_max + 1)`** (line 633): adds 1 L to denominator; OK for stability, but reported uplift summary statistics inherit the +1 distortion.
- **Holiday duplicates** (EDA line 14): 93 duplicate holiday rows; if holiday features are aggregated via `count`, this triple-counts some dates.

---

# Recommended Fixes

| # | Issue | Fix |
|---|---|---|
| F1 | #1 censoring | **Apply Chernozhukov-Hong 3-step censored quantile regression.** (a) Fit a δ-propensity classifier `P(censored_i | X_i)` using {months-at-max ≥3, plateau flag, low SKU breadth given size, etc.} as the censoring proxy. (b) Refit q₉₀ *only on rows where* `P(censored) < 0.10`. (c) Use the refit as the unbiased latent-q₉₀ estimator. Cite `research/01_latent_demand_modeling.md` + `research_brief.md` row C5. |
| F2 | #2 lower bound | Replace `max(...)` with a robust within-outlet upper-tail estimator: `lower_bound_i = max(q₉₅(monthly_history_i), trimmed-max-top-3)`. Optionally blend with cell empirical-Bayes: `(n_i / (n_i + 50)) · q₉₅_self + (50 / (n_i + 50)) · q₉₅_peer`. Drop `january_max` and `recent_3mo_max` from the `max` (they're dominated). Keep them as *features* into the model if seasonality matters. |
| F3 | #3 exponent | Remove the `^1.25`. Recalibrate the uncap weight by **fitting it on a proxy label** (e.g. outlets at ≥95% of own-max for ≥3 of last 6 months) via `LogisticRegressionCV`; the predicted probability *is* the uncap weight, calibrated in [0,1]. If you keep an exponent, *cross-validate it* on the proxy task. Drop the `clip(0, 0.65)`; let the cap layer enforce the ceiling. |
| F4 | #4 constraint score | (a) Drop `has_valid_coordinates` from the score (use it as a separate `confidence_weight` that down-weights the *uplift*, not the score). (b) PCA on `[structural_capacity_score, Cooler_Count, mean_sku_count]` → use PC1 as a single "store-size" axis. (c) Replace `gap` with a quantile-frontier residual *in liters*: `s_frontier_i = clip((q̂₉₀(X_i) - observed_max_i) / q̂₉₀(X_i), 0, 1)`. (d) Switch `observed_proxy` from mean to max for consistency with `lower_bound`. (e) Replace `+1` in plateau with a scale-aware ε. See `research/07_constraint_likelihood_methods.md` line 135 for the composite recipe. |
| F5 | #5 peer frontier | Pick **one** principled estimator: pooled XGBoost 2.0 `reg:quantileerror` with `quantile_alpha=[0.5, 0.75, 0.9, 0.95]`, `outlet_type × outlet_size` as native categoricals, monotone constraint on `outlet_size` ordinal, then `np.sort(preds, axis=1)` for crossing fix. Use the q90 column directly. Drop the `np.maximum.reduce` and the magic `0.85` / `1.35` multipliers. |
| F6 | #6 caps | Replace multiplicative caps with **bucket bootstrap caps** (`research/10_defensible_uplift_caps.md` §"Recommended Cap Methodology"). Compute `cap_b = bootstrap-p95(peer_q90/peer_median)` per `Outlet_Size × Outlet_Type` cell with ≥100 outlets; shrink toward size-level cap for sparser cells. Apply additively or as a soft shrinkage (line 186 of that doc). Lower Extra Large from 4.5× → 4.0× unless bootstrap supports higher. |
| F7 | #7 holdout | Add: (a) 20% outlet-level holdout, (b) MAPIE `ConformalizedQuantileRegressor` for 80%/90% intervals, (c) crossing-rate + empirical-coverage diagnostics in `data_quality_report.md`, (d) **synthetic-censoring stress test**: artificially censor the top 20% of monthly volume on a random outlet subset and verify the pipeline reconstructs ≥70% of removed volume. Code skeleton in `research/03_quantile_regression_for_potential.md` §4 and §7. |
| F8 | #8 identification | Add an **"Identification" subsection** to the report: (i) Manski bounds `[outlet_historical_max, peer_q98]` as the honest interval, (ii) point estimate via SFA or CH-3step as the preferred guess inside the bounds, (iii) sensitivity bands (see F10). |
| F9 | #9 distribution | Re-fit the baseline with `loss='gamma'` or `log1p(y)` target, OR switch to LightGBM `objective='tweedie'`. Save fitted-vs-actual + residual-Q-Q plots into `data/gold/diagnostics/`. |
| F10 | #10 sensitivity | Add a sensitivity table (recompute pipeline tail under each setting): `exponent ∈ {1.0, 1.25, 1.5}`, `clip ∈ {0.5, 0.65, 1.0}`, `size_cap ∈ {3×, 4×, 5×}`, `score_weights ∈ {current, equal, PCA, supervised}`. Report `(mean, p90, p99, max, share_at_cap)` for each cell. **Pick the lowest cap where p99 and total_liters stabilise.** |

---

# What the team got RIGHT

1. **Correct framing.** Treating observed volume as `min(true_demand, constraint)` and refusing to forecast historical sales straight up is the right starting point. Many teams miss this entirely.
2. **q90 (not q99) as the frontier anchor.** With ~36 months per outlet and 943 outlets in the smallest size class, q99 is unstable; q90 is the defensible single τ. (Per `research/03_quantile_regression_for_potential.md` §1 table — confirmed.)
3. **Cell-based peer frontiers** (Outlet_Type × Outlet_Size with type/size fallbacks). The fallback hierarchy is sensible even if the `max`-aggregation choice is wrong.
4. **Catchment density features** with BallTree-haversine and 1/2/5 km rings — clean implementation, exactly the right primitive for downstream POI joins.
5. **Bronze / Silver / Gold pipeline with rejected-records store.** 240 invalid coords + 9,606 invalid txn rows quarantined cleanly. This is rubric-relevant work that many teams skip.
6. **Honest about known limitations.** The methodology doc admits POI features aren't yet in and flags it as the top next step. Good epistemic hygiene.

---

**End of statistician review.** Hand off to Prompt Engineer / Safety / Skeptic for orthogonal critiques. Synthesis agent should weight findings #1, #7, #10 highest by rubric impact (Methodology = 40% of score).
