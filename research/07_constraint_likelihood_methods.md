# Constraint-Likelihood Methods for Latent Demand Scoring
*Channel 7 — Data Storm 7.0 (Sri Lanka beverage retail, 20k outlets, Jan 2026 latent-volume prediction)*

---

## TL;DR

- **Use 3 complementary signals**, not one composite rank-sum: (a) **quantile-regression frontier residual** (cheap, robust upper-envelope), (b) **stochastic-frontier inefficiency `TE = exp(-u_i)`** (principled latent-demand model), and (c) **plateau / variance-collapse flag** (catches saturated outlets the regressors miss). Combine via a Bayesian average or supervised proxy label, **not** equal-weight rank sums.
- **The team's current `constraint_score` (sum of 5 ranks ^1.25) is directionally OK but statistically weak**: it double-counts correlated features (cooler count ↔ SKU breadth ↔ structural capacity), throws away magnitude information by ranking, gives no calibration to actual demand units, and treats the geo/coordinate-validity rank as if it were a constraint signal (it isn't — it's a data-quality signal).
- **Top-3 fixes with biggest expected lift**: (1) replace `^1.25` heuristic with a **τ=0.9 quantile-regression frontier** to get a real demand-units headroom, (2) PCA- or correlation-decorrelate the 4 capacity ranks before summing (kill double counting), (3) add a **plateau detector** (variance over last N months + months-since-new-max) as a separate dimension — it captures behaviour ranks cannot see.

---

## Method Survey

For each method: **verdict** + 1-line justification + Python implementation hint.

### 1. Residual-based scoring (fit observed-sales model, score = magnitude of negative residual)

**Idea.** Fit `E[observed_sales | X]` with gradient boosting / GLM. Stores with large negative residuals (sold far less than peers with same X) are constrained candidates.

- **Pros.** Cheap, uses every feature you have, naturally calibrated in liters.
- **Cons.** Mis-specified mean: the model learns the *constrained* mean, not the latent frontier. Negative residuals also flag *low-demand* outlets, not just constrained ones. Symmetric noise model (Gaussian/Tweedie) cannot separate inefficiency from luck — this is exactly why SFA was invented.
- **Verdict: SUPPLEMENT.** Use as one signal, never alone.
- **Python:** `sklearn.ensemble.GradientBoostingRegressor` or `lightgbm` with `objective="tweedie"` (volumes are non-negative skewed). Residual = `y - y_hat`; standardise by `y_hat` to get a relative gap.

### 2. Peer-gap z-scores `(peer_max − observed_max) / sd(peer_max)`

**Idea.** Group outlets by peer cell (channel × city tier × catchment-density bucket × SKU-breadth bucket); for each outlet compute z vs peer max.

- **Pros.** Distribution-free, interpretable, fast, no model assumptions.
- **Cons.** Heavily depends on peer-cell definition; small cells give noisy `sd`. `peer_max` is itself censored — top of the peer cell may also be constrained, so the frontier is biased *down*. Not robust to outlet heterogeneity unless you condition on enough covariates.
- **Verdict: USE** as a sanity-check / blending feature. Replace `peer_max` with **τ=0.95 quantile** of peer cell (less noisy than max).
- **Python:** `pandas.groupby(peer_cell)[volume].transform(lambda v: v.quantile(0.95))`; z via `(q95 − obs) / mad(v)` (MAD beats sd for heavy tails).

### 3. Plateau detection (variance collapse / time-since-new-max / ARIMA breakpoint)

**Idea.** A truly constrained outlet shows flat volume hugging a ceiling: low rolling variance, no new monthly max for many months, possibly a structural break where growth stopped.

Three plateau metrics:
1. **Variance ratio** `var(last 6 months) / var(prior 6 months)` — drops to ~0 at a ceiling.
2. **Months since new max** — large value = sustained plateau.
3. **Bai-Perron / PELT change-point** — detects a regime shift to flat behaviour.

- **Most defensible:** combine #1 and #2. `var_ratio < 0.3 AND months_since_new_max ≥ 4` is a strong joint flag; both rely only on observed series, no model fit. Bai-Perron is more powerful but needs `≥ 24` points to be reliable — many outlets won't have it. ARIMA breakpoint detection is **over-engineered** for a 36-hr hackathon.
- **Verdict: USE.** This is the cheapest signal that's *orthogonal* to capacity ranks, and the team isn't using it.
- **Python:** rolling stats with `pandas.rolling`; PELT via `ruptures.Pelt(model="l2").fit(series).predict(pen=...)`; Bai-Perron via the `regimes` package on `statsmodels`.

### 4. Anomaly detection (Isolation Forest on multivariate (volume, transactions, SKU breadth))

**Idea.** Train Isolation Forest on `[volume, transactions, SKU_breadth, cooler_count]`. Anomalies *below* the cluster mean (low volume given high capacity) → constrained.

- **Pros.** Unsupervised, multivariate, no distribution assumptions.
- **Cons.** Isolation Forest finds anomalies in *both* directions and does not know "below the cluster" matters. You must post-filter: keep only points where `volume < cluster_centroid_volume`. False positive rate is known to be high on imbalanced data.
- **Verdict: SUPPLEMENT.** Useful as a coarse flag, not a score. Better alternative: **one-class quantile regression** (point below the τ=0.1 conditional quantile of volume given features).
- **Python:** `sklearn.ensemble.IsolationForest(contamination=0.1)`; or `sklearn.linear_model.QuantileRegressor(quantile=0.1)` for a directional version.

### 5. Data Envelopment Analysis (DEA) with `pyDEA`

**Idea.** Linear-programming, non-parametric. Inputs = `[cooler_count, SKU_breadth, structural_capacity, catchment_density]`; output = `observed_max_volume`. Each store gets an efficiency score `θ ∈ (0,1]`; `1 − θ` is your constraint score.

- **Pros.** No functional form, handles multiple inputs/outputs, classic OR method, intuitive (radial input reduction).
- **Cons.** **Deterministic — no noise term**, so any measurement error inflates inefficiency. Sensitive to outliers (one star outlet defines the frontier for everyone). At 20,000 DMUs, classic DEA LPs become **slow** (`O(N²)` LPs). Choice of returns-to-scale (CRS vs VRS) matters a lot. Inputs that are correlated (cooler_count vs SKU_breadth) cause weight flexibility problems.
- **Verdict: REJECT for production, OPTIONALLY supplement for sanity-check.** 36 hours is too short to debug DEA on 20k DMUs; SFA is the principled alternative. If you do try it, run on a 2k-outlet **stratified sample** first.
- **Python:** `pyDEA` (`pip install pyDEA`); VRS input-oriented model. Or roll your own with `scipy.optimize.linprog` for one outlet at a time.

### 6. Stochastic Frontier Analysis (SFA) — `TE_i = exp(−u_i)`

**Idea.** Specify `log(volume_i) = f(X_i; β) − u_i + v_i`, with `u_i ≥ 0` (inefficiency, half-normal or truncated-normal) and `v_i` symmetric noise. `TE_i = exp(−E[u_i | ε_i])` ∈ (0,1] is your efficiency; `1 − TE_i` is the constraint score.

- **Pros.** Separates noise from inefficiency — this is exactly the right framing. Bayesian variants give posterior distributions over `u_i`. Used in retail studies on 2,500-store grocery chains with average inefficiency ~28% reported.
- **Cons.** Distributional assumption on `u_i` matters; specification-sensitive. Cobb-Douglas form is restrictive but cheap; translog adds interactions. Requires log-linearisable inputs.
- **Verdict: USE — this should be the primary signal**, replacing or anchoring the team's heuristic. If channel 2 already produced an SFA score, take it directly.
- **Python:** statsmodels does not ship SFA. Options:
  - `from frontier import SFA` (PyPI: `frontier` package) — half-normal Cobb-Douglas in one call.
  - `pystoned` for non-parametric stochastic frontiers.
  - Bayesian SFA in `pymc` with `u ~ HalfNormal(σ_u)`, `v ~ Normal(0, σ_v)`; sample `u_i` per store.

### 7. Bayesian latent constraint indicator — `P(constrained | features, observed sales)`

**Idea.** Tobit / censored regression: `y_obs = min(y_true, C)` where `y_true ~ Normal(Xβ, σ)` and `C` is an outlet-specific capacity ceiling that depends on cooler count, SKU breadth, etc. Posterior `P(y_true > y_obs | y_obs, X)` is the constraint probability.

- **Pros.** Right model of the problem. Gives calibrated probabilities + posterior latent demand directly. Recent diffusion-aware censored regression work (arxiv 2501.12354) handles substitution between products.
- **Cons.** MCMC on 20k outlets is heavy; expect 30+ min sampling. Identification requires a proxy for `C` or carefully-chosen instruments. Tobit + Bayesian latent demand is the *gold-standard* but slow.
- **Verdict: USE if time permits; otherwise approximate** with a frequentist Tobit (`statsmodels.regression.linear_model.Tobit` via `linearmodels` or roll your own). The posterior latent mean is *directly* the prediction you need — this can replace the whole `lower_bound + score * (frontier − lower_bound)` formula.
- **Python:** `pymc` with `pm.Censored("y", normal, lower=None, upper=C_i, observed=y)`; or `linearmodels.censoredreg`. For speed, an EM approximation works fine.

### 8. Capacity-utilization features (cooler_count vs SKU breadth vs observed_max)

**Idea.** Derive simple engineered ratios that capture headroom directly:

- `volume_per_cooler = observed_max / cooler_count` — low values for huge stores = underused capacity.
- `volume_per_sku = observed_max / SKU_breadth` — same logic.
- `cooler_sku_imbalance = |z(cooler_count) − z(SKU_breadth)|` — mismatch implies bottleneck.
- `headroom = 1 − (observed_max / theoretical_max(cooler_count, SKU_breadth))`, where `theoretical_max` is fit via τ=0.95 quantile regression of volume on those two inputs.

- **Verdict: USE.** These are the most interpretable features and feed *every* downstream method (SFA, quantile-regression frontier, anomaly detection). Cheap, fast, low-risk.
- **Python:** plain pandas; `sklearn.linear_model.QuantileRegressor` for `theoretical_max`.

### 9. Composite score — combining 4–6 weak signals defensibly

Options ranked by defensibility:

| Method | Pros | Cons |
|---|---|---|
| **Equal weights** | Transparent, no overfit | Double-counts correlated signals; assumes equal importance |
| **PCA on standardised signals → use PC1** | Removes redundancy, data-driven | PC1 may not align with "constrained"; weights can be illogical for minority indicators; sign ambiguity |
| **Supervised on a proxy label** | Best calibration if proxy is good | Needs a proxy — e.g. outlets that hit a max ≥ 3 months in a row = `constrained=1` |
| **Bayesian model averaging (BMA)** | Combines models, not features; quantifies model uncertainty | Heavier to set up |

**Recommended.** Start with **proxy-label supervised blend**: define `proxy_constrained = 1` for outlets that (i) hit a near-max for ≥ 3 of last 6 months **and** (ii) have high capacity rank. Train a calibrated classifier (`sklearn.linear_model.LogisticRegression` or `lightgbm` with `is_unbalance=True`); use predicted probability as the composite. Then **decorrelate inputs first** with PCA on the 4 capacity ranks so structural-capacity / coolers / SKU breadth don't triple-count.

### 10. Critical review of the team's current `constraint_score` (rank-based sum)

**What's right.** Direction is correct (high capacity + low realisation ⇒ likely constrained), and ranks are robust to outliers.

**What's wrong.**
1. **Double counting.** `structural_capacity_rank`, `cooler_count_rank`, `SKU_breadth_rank` are highly correlated (a big store has all three). Sum-of-ranks gives big stores ~3× weight on the same latent factor.
2. **`valid_coordinate_rank` is not a constraint signal.** It's a data-quality flag. Mixing it in conflates "we don't know where this store is" with "this store is constrained." Pull it out.
3. **Magnitude information thrown away.** A store at rank 19,999 vs 20,000 is treated similarly to rank 1 vs 2 — but the volume gap may differ by 100×. Ranks are robust but lossy.
4. **No demand observation in the score.** The score is purely a capacity index. A huge store at 5% utilisation and a huge store at 95% utilisation get the *same* constraint_score. That is the opposite of what we want.
5. **`^1.25` exponent is arbitrary.** It pushes constraint scores up superlinearly with no theoretical basis. Calibrate against a held-out proxy instead.
6. **Catchment-density rank is ambiguous.** High density could mean high latent demand (good for constraint signal) *or* high competition (cap on capture). Need to interact with own-share or distance-to-competitor.

**Top-3 specific improvements (with expected impact):**

| # | Fix | Expected impact |
|---|---|---|
| 1 | **Replace rank-sum with a τ=0.9 quantile-regression frontier residual** in liters: `score = (q90(volume \| X) − observed_max) / q90(volume \| X)`. Anchors the score in real demand units; encodes utilisation directly. | **High** — biggest single lift; the current formula is a heuristic standing in for exactly this. |
| 2 | **Decorrelate the capacity inputs** before any aggregation. PCA on `[structural_capacity, cooler_count, SKU_breadth]` → use PC1 as a single "store-size" axis. Keep catchment-density and a *separate* utilisation feature as additional axes. Drop `valid_coordinate_rank` from the score (use it as a *confidence* / down-weighting flag instead). | **Medium-high** — removes ~30% double counting; sharpens the constraint signal. |
| 3 | **Add a plateau term**: `plateau_flag = (var_ratio_last6_vs_prior6 < 0.3) AND (months_since_new_max ≥ 4)`. Blend as a multiplicative gate or as an extra feature in the supervised blend (method 9). | **Medium** — catches saturated outlets the static capacity ranks miss; orthogonal information. |

---

## Recommended Composite Score (Formula + Weights)

A two-tier design that is defensible, fast to ship in 36 hours, and theoretically grounded.

**Step 1 — engineer four orthogonal signals (in `[0,1]`, higher = more constrained):**

1. `s_frontier` — quantile-regression frontier headroom.
   - Fit `q90(volume) ~ f(cooler_count, SKU_breadth, structural_capacity, catchment_density)` with `sklearn.linear_model.QuantileRegressor(quantile=0.9, alpha=0.0)` **or** `lightgbm` with `objective="quantile", alpha=0.9`.
   - `s_frontier_i = clip( (q90_i − observed_max_i) / q90_i, 0, 1 )`.

2. `s_sfa` — stochastic-frontier inefficiency.
   - Fit `log(volume) = β'X − u + v`, half-normal `u`, normal `v` (frontier package or Bayesian via pymc).
   - `s_sfa_i = 1 − exp(−E[u_i | ε_i])`.

3. `s_plateau` — variance + time-since-new-max combo.
   - `s_plateau_i = 0.5·1{var_ratio_i < 0.3} + 0.5·min(months_since_new_max_i / 6, 1)`.

4. `s_anomaly` — directional anomaly score.
   - Isolation Forest score on `[volume, transactions, SKU_breadth, cooler_count]`, **post-filtered** to keep only `volume < cluster_centroid_volume`. Min-max scale.

**Step 2 — combine via supervised proxy or BMA:**

- **Recommended (fast):** define a proxy label `y_proxy_i = 1` if outlet was at ≥ 95% of its own historical max for ≥ 3 of last 6 months AND has capacity-rank ≥ 0.7; else 0.
  Train `LogisticRegressionCV` on `[s_frontier, s_sfa, s_plateau, s_anomaly]` → predicted probability is the **composite constraint score** in `[0,1]`, naturally calibrated.

- **Fallback (if proxy is too noisy):** weighted blend
  `score = 0.40·s_frontier + 0.30·s_sfa + 0.20·s_plateau + 0.10·s_anomaly`
  Justification: frontier and SFA are the principled estimators (larger weight); plateau is orthogonal behaviour; anomaly is a coarse safety-net.

**Step 3 — plug into the team's existing final formula, but recalibrate the exponent.**

Replace `final = lower_bound + score^1.25 · (peer_frontier − lower_bound)` with:

```
peer_frontier = q90_i        # from step 1 — already a real upper-envelope
final_i       = lower_bound_i + score_i · (peer_frontier_i − lower_bound_i)
```

The `^1.25` becomes unnecessary because `score` is now itself a calibrated probability or residual fraction. If you keep an exponent, **fit it on held-out outlets** instead of hard-coding.

---

## References

1. Sellers-Rubio, R. & Mas-Ruiz, F. *Efficiency determinants in retail stores: a Bayesian framework*. Omega 39 (2011). https://www.sciencedirect.com/science/article/abs/pii/S0305048310000812
2. *Benchmarking Retail Productivity Considering Retail Pricing and Format Strategy*. J. Retailing 89 (2013). https://ideas.repec.org/a/eee/jouret/v89y2013i1p1-14.html
3. *Identifying Sales Performance Gaps with Internal Benchmarking* (stochastic frontier on salespeople × category). J. Retailing 93 (2017). https://ideas.repec.org/a/eee/jouret/v93y2017i4p401-419.html
4. *Strategic Groups, Frontier Benchmarking and Performance Differences: UK Retail Grocery*. J. Mgmt Studies. https://onlinelibrary.wiley.com/doi/10.1111/1467-6486.00365
5. araith. *pyDEA documentation* (DEA models, returns to scale, weight restrictions). https://araith.github.io/pyDEA/
6. *Dynamic quantile stochastic frontier models*. Tourism Mgmt 80 (2020). https://www.sciencedirect.com/science/article/abs/pii/S0278431920301407
7. Chib, S. *Bayes inference in the Tobit censored regression model*. J. Econometrics (1992).
8. Orduz, J. C. *Demand Forecasting with Censored Likelihood*. https://juanitorduz.github.io/demand/
9. *Diffusion-Aware Censored Gaussian Processes for Demand Recovery* (arXiv:2501.12354, 2025). https://arxiv.org/abs/2501.12354
10. *Explainable Anomaly Detection in Retail Perpetual Inventory Systems Using SHAP-Enhanced Isolation Forests*. IJBAS. https://www.sciencepubco.com/index.php/IJBAS/article/view/36141
11. Truong, C. et al. *ruptures*: change-point detection in Python. https://centre-borelli.github.io/ruptures-docs/
12. `regimes` package — Bai-Perron and CUSUM extensions for statsmodels. https://github.com/knightianuncertainty/regimes
13. Coolr Group. *Cooler Occupancy & Empty Share of Shelf metrics*. https://docs.coolrgroup.com/docs/playbook/business-performance
14. Greco, S. et al. *On the Methodological Framework of Composite Indicators*. SSRN 4325522. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4325522
15. *Principal component analysis for constructing socio-economic composite indicators*. SN Soc Sci (2024). https://link.springer.com/article/10.1007/s43545-024-00920-x
