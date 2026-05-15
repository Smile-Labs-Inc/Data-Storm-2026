# Channel 3 — Quantile Regression for Latent Potential

> **Mission.** Audit and upgrade the team's existing 90th-percentile GBM "frontier" used to predict latent maximum monthly volume (liters) for 20,000 Sri Lanka beverage outlets in January 2026. Observed sales are censored: `y_obs = min(true_demand, operational_constraints)`. Quantile regression on `y_obs` is a *lower bound* on the true ceiling — but a defensible one, with the right τ and the right calibration story.

---

# TL;DR

- **Keep the q90 anchor.** It is the most defensible single τ for a censored "frontier" given the 164 L median / 1,308 L 95-th-pct spread. Push to q95 only for Small/Medium where cell sizes are large; do **not** trust q95+ on Extra Large outlets (n≈943) — variance is too high.
- **Switch from one model per quantile to a multi-quantile model with monotonic post-fix + Conformalized Quantile Regression (CQR).** Recommended stack for a 36-h hackathon: **XGBoost ≥2.0 `reg:quantileerror` with `quantile_alpha=[0.5, 0.75, 0.9, 0.95]` + isotonic post-sort + split-CQR on a 20% holdout** (Romano, Patterson & Candès 2019). Gives a single ranked frontier, no crossing, and a rigorous 80%/90% interval to quote in the report.
- **Stay with one model + categorical features (`outlet_type × outlet_size`) rather than 28 separate group models.** Pooling lets sparse cells borrow strength; LightGBM/XGBoost split on the categoricals automatically. Only carve out a separate tail-stable estimator (e.g., empirical-Bayes or Weissman extrapolation) for Extra Large outlets if time permits.

---

# Key Findings

## 1. Why q90 is the right "frontier" for a censored ceiling

The pinball (check) loss

$$L_\tau(y, \hat q) = \begin{cases}\tau(y-\hat q) & y \ge \hat q \\ (\tau-1)(y-\hat q) & y < \hat q\end{cases}$$

is a **proper scoring rule uniquely minimised when** $\hat q = F^{-1}_{Y\mid X}(\tau)$, the conditional τ-quantile (scikit-learn, `mean_pinball_loss`; netcal docs). At τ=0.9 the asymmetry penalises under-prediction 9× harder than over-prediction, so the model is *forced upward* toward the realised top-decile of sales — an empirically observed lower bound on capacity, robust to outliers and to censoring on the *upper* side (where stockouts/route-truck caps clip the very largest months).

**Why not τ=0.99?** Tail-quantile estimators converge slowly. With $n_k$ observations in cell $k$, the asymptotic variance of $\hat q_\tau$ scales as $\tau(1-\tau)/[n_k f(q_\tau)^2]$. For τ=0.99 in a 943-outlet Extra-Large cell with ~36 monthly observations each (≈34k point-months), the *effective tail* is ~340 observations, and density $f(q_{0.99})$ is tiny — variance blows up. Extreme-value-theory papers (Daouia et al., Weissman estimators) explicitly warn this regime needs Hill / POT extrapolation, not naive empirical or GBM quantiles.

| τ | Pros | Cons | Verdict for this comp |
|---|---|---|---|
| **0.80** | Stable in every cell. | Sits well below realised peaks; under-states latent ceiling for fast-moving outlets. | Use as a **lower-bound check**, not as the answer. |
| **0.90** | Standard frontier proxy in capacity-utilisation work; stable down to ~50 obs/cell. | Slightly conservative for outlets that are heavily stocked-out. | **Primary choice.** Matches existing pipeline. |
| **0.95** | Closer to the true peak. | Variance ~2× q90; sensitive to one or two big months in small cells. | Use **only for Small/Medium**; ensemble-blend with q90 for Large. |
| **0.99** | Almost the empirical max. | Effectively noise on Extra Large (n=943) and any size×type cell with <500 outlets. | **Avoid.** Replace with the empirical max within `outlet_type × outlet_size × distributor` cells if you really want a tail anchor. |

**Spread sanity-check.** Median outlet-max ≈164 L; 95-th-pct outlet-max ≈1308 L → ratio ≈8×. Capping a q90 frontier at 3–4.5× the median (your current size cap) is consistent with this — but the cap is biting on *some* Extra-Large outlets. Suggest letting the cap be 5× for `Extra Large` and 4× for `Large`; the 90-th-pct of `outlet_max / median(outlet_max)` is about 8 globally but ~4–5 within size class — that's the right reference distribution.

## 2. Library shoot-out (quantile loss, 20k outlets, ~2.4M txns)

| Library | API | Multi-q in one fit | Speed (rough, 20k×~30 feats, 4 quantiles) | Crossing-safe? | Notes |
|---|---|---|---|---|---|
| **LightGBM** `objective='quantile'` | one model per τ | No (must loop) | ~1–3 s per τ × 4 = ~10 s | No | Mature, fast, but historically reported under-coverage on noisy data (issue #1182). Use `min_data_in_leaf ≥ 100`, `num_leaves ≤ 63`, `max_bin = 255`. |
| **XGBoost ≥2.0** `reg:quantileerror` | **Yes** via `quantile_alpha=[..]` (PR #8758) | ~5–15 s for 4 quantiles together | No (docs explicitly warn) | **Recommended.** Use `tree_method='hist'` + `QuantileDMatrix`. Internally it trains separate boosters per α but in one call → much cleaner code. |
| **CatBoost** `loss_function='Quantile:alpha=…'` | per-τ | No | ~5–10 s per τ | No | Good with raw categorical features (great for `outlet_type` × `distributor_id`). |
| **CatBoost** `loss_function='MultiQuantile:alpha=0.5,0.75,0.9,0.95'` | **Yes** | ~10–20 s | **No — explicitly non-monotonic** (issue #2317) | Trains *one* tree structure with multiple leaf outputs (true multi-output). Cleanest API but you still need a post-sort. |
| **sklearn** `GradientBoostingRegressor(loss='quantile')` | per-τ | No | **Slow.** 30 s – several minutes per τ on 20k rows. `HistGradientBoostingRegressor(loss='quantile')` is the LightGBM-style fast variant — use that instead if you stay in sklearn. | No | Calibration is good (sklearn issue #1182 contrast). |
| **NGBoost** | dist outputs (Normal/LogNormal) | quantiles via inverse CDF | Slow (~minutes for 20k rows × 1k boosts) | Yes by construction | Gives a *parametric* posterior; quantiles never cross. Use as a **secondary calibration model**, not primary. |
| **`lightgbm-quantile-regression`** (third-party PyPI) | wraps stacked-α-as-feature trick | Yes | Comparable to LightGBM × 1 | Yes (monotone constraint on α) | Implements Issue #5727 trick. Useful if you must stay in LightGBM. |

**Headline recommendation:** **XGBoost 2.0 `reg:quantileerror` with a list of alphas** is the best fit for a 36-h hackathon — one call, hist+QuantileDMatrix is GPU-friendly, and the API exactly matches what the report needs (median + intervals).

```python
import xgboost as xgb, numpy as np
alphas = np.array([0.5, 0.75, 0.9, 0.95])
Xy = xgb.QuantileDMatrix(X_train, y_train)
Xy_val = xgb.QuantileDMatrix(X_val, y_val, ref=Xy)
booster = xgb.train(
    {
        "objective": "reg:quantileerror",
        "quantile_alpha": alphas,
        "tree_method": "hist",
        "learning_rate": 0.04,
        "max_depth": 6,
        "min_child_weight": 50,   # protects Extra Large cells
        "subsample": 0.8,
        "colsample_bytree": 0.8,
    },
    Xy, num_boost_round=2000,
    evals=[(Xy, "tr"), (Xy_val, "va")],
    early_stopping_rounds=50,
)
preds = booster.inplace_predict(X_test)   # shape (n, 4)
q50, q75, q90, q95 = preds.T
```

Source: [XGBoost docs — Quantile Regression](https://xgboost.readthedocs.io/en/stable/python/examples/quantile_regression.html) and [PR #8758](https://github.com/dmlc/xgboost/pull/8758).

## 3. Multi-quantile training in one model — the three real options

1. **XGBoost `quantile_alpha=[..]`** — internally one booster per α but trained jointly with shared validation. *Crossing risk: yes.*
2. **CatBoost `MultiQuantile`** — *one* tree, multiple leaf outputs, gradient is the stacked pinball gradient. Faster than (1) at moderate `iterations`, but [GitHub #2317 confirms outputs are not monotone in α](https://github.com/catboost/catboost/issues/2317).
3. **Stacked-α-as-feature trick (LightGBM Issue #5727)** — duplicate every row K times, append the α value as a feature, set `monotone_constraints` so the model is monotone in α, and use a custom composite-pinball objective. Guarantees no crossing **and** smooths the quantile function. The `lightgbm-quantile-regression` PyPI package implements this. Heavier on memory (×K rows) — for 2.4M txns × 4 alphas you need ~10M training rows; if you train on the *outlet-month grain* (~720k rows) it is fine.

**For this hackathon: pick (1) for speed, then (2) or (3) only if there's time.** The crossing problem from (1) is fixed cheaply in §6 below.

## 4. Conformalized Quantile Regression (Romano et al. 2019) — yes, do this

[Romano, Patterson & Candès, NeurIPS 2019](https://arxiv.org/abs/1905.03222). One-paragraph version:

1. Train any quantile regressor for τ_lo (e.g., 0.05) and τ_hi (e.g., 0.95) on `D_train`.
2. On a held-out calibration set `D_cal` (~20% of outlets), compute the conformity score
$$E_i = \max\bigl(\hat q_{\tau_{lo}}(x_i)-y_i,\;y_i-\hat q_{\tau_{hi}}(x_i)\bigr)$$
3. Let $Q_{1-\alpha}$ be the $\lceil(1-\alpha)(n_{cal}+1)\rceil/n_{cal}$ empirical quantile of $\{E_i\}$.
4. Final interval: $\bigl[\hat q_{\tau_{lo}}(x) - Q_{1-\alpha},\; \hat q_{\tau_{hi}}(x) + Q_{1-\alpha}\bigr]$.

This gives **finite-sample, distribution-free coverage of at least $1-\alpha$** (under exchangeability), while inheriting the heteroscedastic interval *width* from quantile regression. For a censored-demand setting the upper bound after CQR is exactly the kind of "we are 90 % sure latent capacity is at least X" statement judges of the Methodology / GenAI sections will reward.

Practical implementation: [MAPIE `SplitConformalRegressor` and `ConformalizedQuantileRegressor`](https://mapie.readthedocs.io/en/stable/examples_regression/2-advanced-analysis/plot_main-tutorial-regression.html). MAPIE wraps any sklearn-compatible base estimator.

```python
from mapie.regression import ConformalizedQuantileRegressor
from mapie.utils import train_conformalize_test_split
X_tr, X_cal, X_te, y_tr, y_cal, y_te = train_conformalize_test_split(
    X, y, train_size=0.6, conformalize_size=0.2)
cqr = ConformalizedQuantileRegressor(
    estimator=xgb_reg_q005, estimator_high=xgb_reg_q095,  # see MAPIE docs
    confidence_level=0.9,
).fit(X_tr, y_tr).conformalize(X_cal, y_cal)
preds, intervals = cqr.predict_interval(X_te)
```

**Caveat for this comp:** CQR coverage is for the *observed* censored target. The true latent ceiling is by construction ≥ y_obs, so a CQR upper bound is a *valid lower bound* on the latent quantile — phrase it that way in the report.

## 5. Group-wise quantile estimation (4 sizes × 7 types = 28 cells)

**Don't fit 28 separate models.** Reasons:

- Cells are very unbalanced (Extra Large × certain types may have <100 outlets). High-quantile variance scales as $1/n$.
- A pooled model with `outlet_type` and `outlet_size` as **native categorical** features (`categorical_feature=` in LightGBM, `cat_features=` in CatBoost, or `enable_categorical=True` in XGBoost ≥1.6) lets the tree learn type/size interactions implicitly and *shares* slope information across cells.
- The econometrics literature on **panel quantile regression with grouped fixed effects** (Gu & Volgushev 2019; Chen 2024) confirms that pooled estimation with group-membership features is consistent and **strictly more efficient than cell-wise estimation when groups are unbalanced** — exactly your situation.

**What to do instead:**

- Train one global model on all 20k outlets.
- Add features: `outlet_type` (cat), `outlet_size` (cat), `outlet_type × outlet_size` (interaction id), distributor id (cat), region/lat-lon, seasonality.
- Add **monotonic constraints** in the tree boosters where signs are known (e.g., higher size class ↔ higher capacity; more nearby competitors ↔ lower capacity). LightGBM `monotone_constraints=[1,…,−1,…]`.
- Optional: shrink per-cell predictions toward the global model with empirical-Bayes (James-Stein-ish): $\hat q_k = \lambda_k \cdot \hat q_k^{\text{cell}} + (1-\lambda_k)\cdot \hat q^{\text{global}}$, with $\lambda_k = n_k/(n_k + \kappa)$. For Extra-Large × small types this drops cell weight to near-zero and falls back on the global model — exactly what you want.

## 6. Crossing quantiles — the cheap fix nobody does

Single-model and multi-model quantile fits **routinely cross** (XGBoost docs, LightGBM #5727, CatBoost #2317): you'll see rows where $\hat q_{0.95} < \hat q_{0.9}$. Three fixes, in increasing strength:

| Fix | Cost | Strength | When to use |
|---|---|---|---|
| **Per-row sort** of `[q50, q75, q90, q95]` (i.e., isotonic in α direction) | Free | Rearranges → still consistent in expectation (Chernozhukov, Fernandez-Val & Galichon 2010) | **Always do this. Adds 5 lines of code.** |
| **Pool-Adjacent-Violators (PAV) on the predicted quantile function**, per row | Free | Stronger than sort (also handles plateau cases) | If you need monotone, smoothed function. |
| **Stacked-α-as-feature with `monotone_constraints` on α** (Issue #5727 trick) | Heavier training | Crossings cannot occur by construction | If you need a guaranteed-monotone deliverable. |

The Chernozhukov et al. (2010) paper proves that simple rearrangement (sort) **strictly improves the L_p estimation error** of the quantile function vs the unsorted estimator. So this is not just cosmetic — it improves accuracy.

```python
preds = np.sort(preds, axis=1)   # one-line crossing fix; safe and statistically improves loss
```

For deep models or if you really want non-crossing by construction: **MCQRNN** (Cannon 2018, [paper](https://link.springer.com/article/10.1007/s00477-018-1573-6)) — a small NN that simultaneously fits multiple non-crossing quantiles. Python implementation: [RektPunk/mcqrnn](https://github.com/RektPunk/mcqrnn). Too heavy for 36 h.

## 7. Crossing diagnostic — add this to the QA notebook

Add to your validation report:

```python
def crossing_rate(preds, alphas):
    """Fraction of rows where q_τ is non-monotone in τ."""
    # preds: (n, K), alphas sorted ascending
    diffs = np.diff(preds, axis=1)        # (n, K-1)
    return (diffs < 0).any(axis=1).mean()
print(f"Quantile-crossing rate: {crossing_rate(preds, alphas):.2%}")
```

A rate >1 % is a smell test — re-train with stronger regularization or use the stacked-α trick. For the deliverable you should report a **post-sort crossing rate of 0 %** (because sorting fixes everything).

Also report **empirical coverage** on the holdout:

```python
def coverage(y, lo, hi):  return ((y>=lo)&(y<=hi)).mean()
print(coverage(y_val, q05, q95))   # should be ≈0.90 for well-calibrated PI
```

If empirical coverage on `y_obs` is below the nominal level, the *true* coverage on latent ceiling is even worse — a strong argument for the CQR step in §4.

## 8. Stability of high quantiles in sparse cells

Extra Large outlets ≈ 943. If you also stratify by `outlet_type` (7) and `distributor` (10) the smallest cells will have <20 outlets — useless for q95. Three defenses:

1. **Bootstrap-CI on the quantile estimator itself.** For each cell with $n_k<200$, run 200 bootstrap resamples, refit the quantile, and report the bootstrap SE. Cells with bootstrap SE > 30 % of the point estimate get **shrunk to the global model** (empirical-Bayes, §5).
2. **Weissman / POT extrapolation** ([Weissman 1978; Refined Weissman, Albert et al. 2022](https://link.springer.com/article/10.1007/s10687-022-00452-8)) — fit a Generalized Pareto distribution to the top 10–20 % of observations within `outlet_size`, then extrapolate to q95. This is the standard EVT trick when the tail is sparse and is well-known in capacity-frontier work. Library: [`scikit-extremes`](https://github.com/kikocorreoso/scikit-extremes) or `pyextremes`.
3. **Smoothed q90 with kernel weights across `outlet_size × outlet_type`.** Use the q90 from neighbouring cells (Large × same type; Extra Large × adjacent type) as a Bayesian prior; combine with the cell estimate weighted by $1/SE^2$.

For a 36-h hackathon the fastest and most defendable move is (1) + the empirical-Bayes shrinkage in §5.

## 9. How to quote a defensible uncertainty interval in the final report

The judges' Methodology score (40 %) will reward language like:

> "Our point estimate of latent monthly potential is the **conditional 90-th percentile** of historical realised sales given outlet, distributor and seasonal features (LightGBM/XGBoost quantile regressor, pinball loss). To turn this into a defensible interval we apply **Conformalized Quantile Regression (Romano et al., NeurIPS 2019)** on a 20 % outlet-level holdout. The reported [q05, q95] interval has empirical coverage of XX % on the holdout (target 90 %); on Extra-Large outlets (n=943, sparse tail) we additionally regularise with empirical-Bayes shrinkage toward the global frontier. We explicitly note that this interval is for *observed* sales, which is a censored lower bound on true demand; therefore the upper end of the CQR interval is a *defensible lower bound on the latent ceiling*, not a true upper bound on demand."

Short, technically correct, and bounds-aware. That last sentence — being honest about what CQR can and cannot guarantee under censoring — is what differentiates a top-3 submission from a marketing-y one.

If you also want a single number to quote per outlet, recommend:

- **Point estimate:** `clip(q90 (CQR-adjusted), lower_bound, size_cap)` — this is essentially your current pipeline + the CQR adjustment.
- **Interval:** `[q05_CQR, q95_CQR]` for 90 % nominal coverage.

---

# Concrete Recommendations for THIS Comp (ranked by impact)

### R1 (must-do, 30 min, big win) — Switch to one-model multi-quantile + post-sort.
Replace the single q90 GBM with **XGBoost 2.0 `reg:quantileerror` with `quantile_alpha=[0.5, 0.75, 0.9, 0.95]`**. After predict, `preds = np.sort(preds, axis=1)`. You now have a richer probabilistic forecast for free, and the median can serve as a sanity-check anchor. Code in §2 above; ~30 min including refit.

### R2 (must-do, 1 h, methodological gold) — Add Conformalized Quantile Regression.
Hold out 20 % of outlets *before* any feature engineering. After step R1, run MAPIE's `ConformalizedQuantileRegressor` for 80 % and 90 % nominal coverage. Report empirical coverage in the docs/methodology section. This is a *paper-citable*, peer-reviewed calibration step — exactly what 40 % Methodology + 20 % GenAI judges look for.

### R3 (must-do, free) — Add crossing-rate + coverage diagnostics to `data_quality_report.md`.
Two functions in §6 and §7. Reporting these numbers (crossing rate before/after sort; empirical coverage of CQR interval on holdout) is the cheapest possible "defensibility moat" for the methodology section.

### R4 (high impact, 1–2 h) — Pooled model with `outlet_type × outlet_size` categorical, *not* 28 group models.
Add `outlet_type`, `outlet_size`, and an interaction id as native categorical features. Add monotone constraints where physics is known: `outlet_size` ↑ → ceiling ↑ (set `monotone_constraints` accordingly). Cite Gu & Volgushev (2019) for grouped-fixed-effects panel quantile regression.

### R5 (high impact, 2 h) — Empirical-Bayes shrinkage for sparse tail cells (Extra Large × thin types).
For any `(size × type × distributor)` cell with $n_k < 200$, blend the cell-specific q90 with the global-model q90 via $\lambda_k = n_k/(n_k+200)$. Reduces variance of the most error-prone predictions; near-trivial code; defensible in writeup.

### R6 (medium, 30 min) — Replace the hard `3–4.5×` size cap with a percentile-of-median cap.
Compute `cap_k = 5 × median(outlet_max | outlet_size=k)` (or similar) per `outlet_size` rather than a global multiplier. Use the `outlet_size`-stratified 95-th-pct of `outlet_max / median` as the multiplier — empirically derived rather than guessed.

### R7 (medium, 1 h) — Lower-bound check via q80 model.
Add a q80 quantile model as a **lower-bound sanity check** on the ceiling. Any outlet whose final point-estimate is below its own q80 prediction triggers a flag in the QA notebook (likely an over-shrunk prediction).

### R8 (nice-to-have, 2–3 h) — Tail-stable q95 only on Small/Medium; use q90 + EVT extrapolation on Extra Large.
Within `outlet_size = 'Extra Large'` use a generalized-Pareto fit on the top 10 % of sales-months per outlet (library: `pyextremes`) to extrapolate a q95 instead of trusting the GBM tail.

### R9 (nice-to-have, 2 h) — Stacked-α-as-feature trick for guaranteed monotone quantiles.
If R1 + post-sort doesn't satisfy reviewers, implement the LightGBM Issue #5727 trick: row-duplicate ×K, append `alpha` as a feature with `monotone_constraints=1`, train with custom composite-pinball gradient. Guaranteed crossing-free at inference.

### R10 (skip for hackathon) — NGBoost / MCQRNN.
Both are good methods but slow to train and tune; not worth the time for a 36-h sprint when XGBoost+CQR achieves the same goals.

---

# References

**Quantile regression — fundamentals**

- Koenker, R., & Bassett, G. (1978). *Regression Quantiles*. Econometrica 46(1), 33–50.
- Chernozhukov, V., Fernandez-Val, I., & Galichon, A. (2010). *Quantile and Probability Curves Without Crossing*. Econometrica 78(3), 1093–1125. — sort/rearrange is statistically optimal.
- scikit-learn, `mean_pinball_loss` documentation: https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_pinball_loss.html

**Library docs**

- XGBoost — Quantile Regression example (multi-α `quantile_alpha`): https://xgboost.readthedocs.io/en/stable/python/examples/quantile_regression.html and PR #8758: https://github.com/dmlc/xgboost/pull/8758
- LightGBM Parameters (`objective='quantile'`, `alpha`): https://lightgbm.readthedocs.io/en/latest/Parameters.html
- LightGBM Issue #5727 — multiple quantile regression with monotonicity: https://github.com/lightgbm-org/LightGBM/issues/5727
- LightGBM Issue #1182 — calibration of quantile regression: https://github.com/lightgbm-org/LightGBM/issues/1182
- CatBoost MultiQuantile non-monotonicity (Issue #2317): https://github.com/catboost/catboost/issues/2317
- scikit-learn `GradientBoostingRegressor` (loss='quantile'): https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html
- `lightgbm-quantile-regression` PyPI: https://pypi.org/project/lightgbm-quantile-regression/

**Conformal quantile regression**

- Romano, Y., Patterson, E., & Candès, E. (2019). *Conformalized Quantile Regression*. NeurIPS 2019. https://arxiv.org/abs/1905.03222
- MAPIE (Python) — split + conformalized quantile regression: https://mapie.readthedocs.io/en/stable/examples_regression/2-advanced-analysis/plot_main-tutorial-regression.html

**Non-crossing quantiles**

- Bondell, H. D., Reich, B. J., & Wang, H. (2010). *Noncrossing Quantile Regression Curve Estimation*. Biometrika 97(4), 825–838. https://academic.oup.com/biomet/article-abstract/97/4/825/241506
- Cannon, A. J. (2018). *Non-crossing nonlinear regression quantiles by monotone composite quantile regression neural network, with application to rainfall extremes.* Stochastic Environmental Research and Risk Assessment 32, 3207–3225. https://link.springer.com/article/10.1007/s00477-018-1573-6
- MCQRNN Python implementation: https://github.com/RektPunk/mcqrnn

**Probabilistic & multi-quantile boosting**

- Duan, T., Avati, A., Ding, D. Y., et al. (2020). *NGBoost: Natural Gradient Boosting for Probabilistic Prediction*. ICML 2020. https://proceedings.mlr.press/v119/duan20a.html

**Group-wise / panel quantile**

- Gu, J., & Volgushev, S. (2019). *Panel data quantile regression with grouped fixed effects*. Journal of Econometrics 213(1), 68–91. https://www.sciencedirect.com/science/article/pii/S0304407619300612
- Chen, L. (2024). *Quantile estimation of heterogenous panel quantile model with group structure*. Economics Letters 241. https://ideas.repec.org/a/eee/ecolet/v241y2024ics0165176524002829.html

**High / extreme quantiles & sparse tails**

- Weissman, I. (1978). *Estimation of parameters and large quantiles based on the k largest observations*. JASA 73(364), 812–815.
- Albert, C., Dutfoy, A., Gardes, L., & Girard, S. (2022). *A refined Weissman estimator for extreme quantiles*. Extremes 25, 257–290. https://link.springer.com/article/10.1007/s10687-022-00452-8
- Daouia, A., Gardes, L., Girard, S. (2013). *Frontier estimation in nonparametric location-scale models*. Journal of Econometrics 178(2), 728–740. https://www.sciencedirect.com/science/article/abs/pii/S0304407613001504

**Censored demand & frontier in retail**

- FreshRetailNet-50K (2025). *Stockout-annotated censored demand dataset for latent demand recovery*. arXiv:2505.16319. https://arxiv.org/html/2505.16319v2
- Sakhuja, R. (2017). *A new approach to estimating a profit frontier using the censored stochastic frontier model*. Research in International Business and Finance 39, 68–77. https://econpapers.repec.org/RePEc:eee:ecofin:v:39:y:2017:i:c:p:68-77
