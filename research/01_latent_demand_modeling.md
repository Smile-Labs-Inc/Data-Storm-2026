# Latent Demand Modeling — Research Channel 01

> Channel 01 of the parallel research swarm (Data Storm 7.0).
> Target: Estimate **uncapped monthly volume potential** for 20k Sri Lanka
> beverage outlets when observed sales are `min(true_demand, constraint)`.
> Audience: hackathon team that already has a 90th-pct quantile-GBM frontier
> + constraint_score blend, needs to defend methodology against judges
> (Data Engineering 40%, Methodology 40%, GenAI 20%).

---

## TL;DR

- The data is **right-censored from below** on true demand (`observed ≤ truth`
  when constraint binds) — *not* "left-censored" as the brief stated. Treat the
  observed monthly max as a **lower bound** and model the gap to the true
  ceiling. Get the framing right and you already score points on Methodology.
- **Best ROI for 36 h:** keep the QGB frontier, but **(a)** wrap it with a
  **Tobit-style censored MLE** on a small parametric head over GBM features,
  **(b)** add a **Powell / Chernozhukov-Hong censored 0.90-quantile check**,
  and **(c)** report **Manski worst-case bounds** as an honesty band around
  your point estimate. That trio = forensics narrative judges love.
- **Reject for this comp:** Heckman/Tobit Type II (no exclusion restriction,
  no truly unselected rows), full 2-tier SFA (overkill, no clear `w` signal),
  bespoke deep censored nets (overfit risk at 20k outlets, no held-out truth).

---

## Problem Framing (read this first)

Let `y_it` = observed monthly volume for outlet *i* in month *t*, `D_it` =
latent (true) demand, `C_it` = operational ceiling (credit, stockout, route
caps).

```
y_it = min(D_it, C_it)
```

We want `max_t E[D_i,Jan2026]` — the *uncapped* monthly demand ceiling.

Two random variables, one observed. Standard **Type-I censoring** terminology:

| Convention | What's censored | Direction |
|---|---|---|
| Classical Tobit (wage = 0) | Outcome at a floor | **Left** |
| Survival / our case | Outcome from above by a cap | **Right** |

So the right mental model is **right-censored regression** with an *unknown,
outlet-specific* censoring point `C_it`. That unknown-`C` part is what makes
the textbook Tobit not directly applicable and why the team's
`constraint_score` is a defensible heuristic for `P(censored)`.

**Censoring indicator we can build (without ground truth):**
`δ_it = 1` (censored) if any of:
- observed = stockout_flag (zero-sales rows after non-zero history)
- observed within ε of historical_max for 2+ consecutive months (**plateau**)
- credit_limit_proxy / catchment-density z-score > threshold
- delivery_cap_proxy hit (route SKU sum near distributor cap)

Once we have `δ`, every classical censored-regression tool unlocks.

---

## Key Findings — method by method

### 1. Tobit Type I (single-equation censored MLE)

**Model.** Latent `D* = xβ + ε`, `ε ~ N(0, σ²)`. Observed
`y = D*` if `D* < C`, else `y = C`. Log-likelihood mixes a Normal pdf for
uncensored rows and `1 − Φ((C−xβ)/σ)` for censored rows. With *known*
outlet-specific `C_i`, MLE is straightforward
([CRAN `censReg` vignette](https://cran.r-project.org/web/packages/censReg/vignettes/censReg.pdf),
[Microeconometrics with R, ch. 11](https://ycroissant.github.io/micsr_book/chapters/tobit.html)).

**For this comp.**
- *Strength:* directly answers the question — predicts `E[D*|x]`, not
  `E[y|x]`. Gives a clean story for judges.
- *Weakness:* needs `C_i`. We don't observe it. Workaround: pseudo-`C_i`
  using the team's `constraint_score`. Eg.
  `C_i = observed_max_i / max(0.4, 1 − constraint_score_i^α)`.
- *Weakness:* Normal errors. Volume is positive-skewed
  (median 164 L, p95 1308 L → ratio ~8). **Log-transform first**, fit Tobit
  on `log(y+1)`, exponentiate back. Trivial.
- *Python:* `lifelines.WeibullAFTFitter` with right-censoring works,
  or hand-rolled MLE in `scipy.optimize.minimize` (~30 lines).

**Verdict: USE as the parametric head over engineered features.** It is the
single most defensible thing you can put in the report next to "Tobit".

---

### 2. Tobit Type II (a.k.a. Heckman selection)

**Model.** Two equations: a *selection* probit (`z* = wγ + u`, observed if
`z* > 0`) and an *outcome* regression (`D* = xβ + ε`), with `corr(u, ε) = ρ`.
Heckman's two-step adds an Inverse Mills Ratio to OLS
([statsmodels Heckman impl](https://github.com/statsmodels/statsmodels/blob/92ea62232fd63c7b60c60bee4517ab3711d906e3/statsmodels/regression/heckman.py),
[bookdown selection guide](https://bookdown.org/christopherpadams/heckman/)).

**For this comp.**
- Type II is for **endogenous selection** ("who chooses to report wages?").
  Every outlet here sells *something* — there is no "unsold" sub-population
  to model with a probit. So no clear `z*` decision.
- Heckman *also* requires an **exclusion restriction**: a variable in `w`
  but not in `x`. We have no obvious candidate.
- 2018 lit shows Heckman 2-step can be **worse than OLS** without a valid
  exclusion ([Stats StackExchange #38853](https://stats.stackexchange.com/questions/38853/heckman-selection-model-with-difference-in-differences-specification)).

**Verdict: REJECT.** Wrong tool. Mentioning Type II only to explain why
Type I (Tobit) is the right fit scores narrative points.

---

### 3. Two-Tier Stochastic Frontier (2TSF; Polachek–Yoon)

**Model.** `y = xβ + v + w − u`, with `v ~ N(0,σ²)` symmetric noise,
`w ≥ 0` upward shock (here: temporary demand spikes), `u ≥ 0` downward
inefficiency (here: constraint loss). Classical refs: Polachek & Yoon 1996
([Wiley](https://onlinelibrary.wiley.com/doi/10.1002/%28SICI%291099-1255%28199603%2911%3A2%3C169%3A%3AAID-JAE373%3E3.0.CO%3B2-%23)),
Kumbhakar & Parmeter 2009; modern Stata `sftt`
([Stata Journal 2023](https://ideas.repec.org/a/tsj/stataj/v23y2023i1p197-229.html));
2024 het-distribution extension
([ResearchSquare](https://www.researchsquare.com/article/rs-4437203/v1.pdf)).

**Why 2TSF *seems* perfect for us.** We have two-sided unobserved
distortions: stockouts compress sales (the `u` term), promo months /
festivals inflate them (the `w` term). The model literally decomposes them.

**Why it isn't.**
- 2TSF likelihood is fragile; identification depends on **scaling property**
  ([Lai & Kumbhakar 2018](https://ideas.repec.org/a/kap/jproda/v49y2018i1d10.1007_s11123-017-0520-8.html))
  and distributional choices (half-normal vs exponential vs gamma).
- Python tooling is thin. `pysfa`
  ([PyPI](https://pypi.org/project/pysfa/)) covers one-sided SFA only;
  `depp-sfa` ([PyPI](https://pypi.org/project/depp-sfa/0.1.3/)) and FronPy
  ([GitHub](https://github.com/AlexStead/FronPy)) likewise. You'd port Stata
  `sftt` math yourself.
- **36 h budget** — every hour debugging a custom MLE is an hour not
  building the feature pipeline that judges grade on Data-Forensics 40%.

**Verdict: SUPPLEMENT (light).** Use the *one-sided* SFA (`y = xβ + v − u`,
`u ≥ 0` ≈ constraint loss) via `pysfa` as a **second opinion** on the
constraint_score. Cite Polachek-Yoon as the inspiration but don't ship full
2TSF. Big methodology win for low effort.

---

### 4. Censored Quantile Regression (Powell 1986 / Chernozhukov-Hong 2002)

**Model.** Estimate the τ-th conditional quantile of `D*` under right
censoring. Powell's CLAD minimises
`Σ ρ_τ(y_i − min(x_iβ, C_i))` — a quantile loss applied to the *clipped*
prediction, robust to censoring as long as
`P(C_i > Q_τ(D*|x_i)) > 0`
([Powell lecture notes](https://eml.berkeley.edu/~powell/e242_f04/powell.pdf)).

Chernozhukov & Hong 2002 give a **three-step** estimator: (1) flexibly
predict `P(censored | x)`, (2) keep rows with prob < 1−τ, (3) run standard
quantile regression on those — same asymptotic efficiency as Powell, *much*
easier to compute
([JASA 2002 PDF](https://www.mit.edu/~vchern/papers/Chernozhukov%20and%20Hong%20(JASA%202002)%20Three%20Step%20Censored%20Quantile%20Regression.pdf)).

**For this comp.** This is **gold**. Why:
- We *already* fit a 90th-pct quantile-GBM. Right now it sees censored
  rows as "real" data — it learns `Q_0.9(y)`, not `Q_0.9(D*)`. CH 3-step
  fixes that with one extra propensity model on δ_it.
- No distributional assumption (vs Tobit needing Normal errors).
- R `quantreg::crq` is reference impl
  ([CRAN vignette](https://cran.r-project.org/web/packages/quantreg/vignettes/crq.pdf));
  in Python use `statsmodels.QuantReg` on the CH-filtered subset. ~50 LOC.
- 2023 advances: **gradient boosting for extreme quantiles** with
  GP-tail extrapolation (Velthoen et al., Springer *Extremes*)
  ([article](https://link.springer.com/article/10.1007/s10687-023-00473-x))
  — directly relevant: lets you push beyond observed 95th pct (1308 L) into
  the latent tail.

**Verdict: USE (this is the upgrade to the team's current QGB frontier).**

Concrete recipe:
1. Train `δ_hat = P(censored | x)` with LightGBM logistic on the indicators
   listed in *Problem Framing*.
2. Keep rows with `δ_hat < 0.10` ("clearly uncensored").
3. Refit the 90th-pct quantile GBM on that subset → cleaner `Q_0.9(D*|x)`.
4. Optional: bolt on a GP-tail (POT) layer for the top 5% to extrapolate
   beyond 1308 L for Extra-Large + dense-catchment outlets.

---

### 5. Latent-variable / EM approaches (retail stockout literature)

**Model.** Treat `D_it` as latent, alternate
- E-step: `D_it | y_it, x_i, θ` (impute, conditional on observation +
  current model)
- M-step: refit `θ` on imputed dataset

Anupindi, Dada & Gupta 1998 — classical vending-machine paper showing
EM on MNL + Poisson choices
([INFORMS](https://ideas.repec.org/a/inm/ormksc/v17y1998i4p406-423.html)).
Vulcano, van Ryzin, Ratliff 2012 — "Estimating Primary Demand for
Substitutable Products" (still the most cited unconstraining paper)
([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1923711)).
Reported impact: **23% RMSE reduction vs naive sales-as-demand**.

**For this comp.**
- Pure EM needs an arrival/choice model. We have no within-month customer
  arrivals — just monthly aggregates per outlet. Misses the substitution
  story.
- BUT: a *simplified* EM is cheap and useful:
  - Step 1: fit Tobit on uncensored rows.
  - Step 2: impute `D̂_it` for censored rows from truncated-Normal tail.
  - Step 3: refit Tobit (or quantile GBM) on `(uncensored y) ∪ (imputed D̂)`.
  - Iterate 2-3 times. This is the classical *unconstraining* trick.

**Verdict: SUPPLEMENT.** Lightweight EM-over-Tobit gives the team a
robustness check + a sentence in the report: *"We applied an iterative
imputation procedure consistent with the unconstraining literature
(Anupindi et al. 1998; Vulcano et al. 2012)."*

---

### 6. Manski-style worst-case bounds (partial identification)

**Idea.** Don't try to point-identify the true demand. Instead, derive a
*set* `[D_lo, D_hi]` consistent with what's observed, *without* any
distributional assumption about `C` or `D*`. Classic ref: Manski 1989,
Manski & Tamer 2002; modern primer:
[*Causal Review* article on Manski bounds](https://www.causalreview.com/articles/partial-identification-and-manski-bounds-how-much-can-we-learn-without-strong-assumptions).

**Bounds for this comp.**
- `D_lo_i = max(y_it)` — the largest sale we ever saw is a lower bound on
  the true monthly ceiling.
- `D_hi_i = max(y_it) × multiplier(size, density)` — a structurally
  motivated cap (the team's 3x/3.5x/4x/4.5x already does this). Manski
  framing makes this a *defensible bound*, not an arbitrary cap.
- Mid-point or Bayes-credible interior is your point estimate; **report the
  interval** in the final write-up.

**Verdict: USE (presentation layer).** Costs almost nothing. Gives the team
an "honesty band" — when judges ask *"how confident are you?"* you point at
the bounds. Matches the no-ground-truth reality of the comp.

---

### 7. Deep censored regression (Tobit-loss neural nets, deep AFT)

**Refs.**
- *Deep Tobit* (PubMed/Stat Med 2024, Lin et al.) — Tobit log-likelihood
  as loss, with feature selection
  ([PubMed](https://pubmed.ncbi.nlm.nih.gov/41571915/)).
- Pattern Analysis & Apps 2024 — three losses compared (Tobit-NLL,
  censored MSE, censored MAE); Tobit-NLL wins; supports heteroscedastic σ
  via a second head
  ([Springer](https://link.springer.com/article/10.1007/s10044-024-01216-9)).
- Variational Tobit GP regression
  ([Springer Stats & Computing 2023](https://link.springer.com/article/10.1007/s11222-023-10225-3)).

**For this comp.**
- Tobit-NLL loss is literally **30 lines of PyTorch** if we already have a
  censoring indicator δ. Plug into any tabular MLP.
- But: 20k outlets × 36 months ≈ 720k panel rows after aggregation; not big
  enough to crush GBMs on tabular features. Risk of overfit + judges asking
  *"why neural net?"* without a clean answer.
- Useful **only** if we want to model interactions GBMs miss (eg.
  cooler_count × catchment_density × distributor_season) or want
  uncertainty via heteroscedastic σ head.

**Verdict: SUPPLEMENT (stretch goal, hour 28+).** Add a small Tobit-NLL MLP
as a **stacking-layer second opinion** to the QGB frontier. Skip if running
short on time — pure win-rate-vs-effort, GBM stack is better.

---

### 8. Monotonic neural nets / monotonic GBMs

**Refs.** Constrained Monotonic NNs (ICML 2023, Runje & Shankaranarayana)
([PMLR](https://proceedings.mlr.press/v202/runje23a.html));
[arxiv 2205.11775](https://arxiv.org/pdf/2205.11775).
XGBoost `monotone_constraints`
([docs](https://xgboost.readthedocs.io/en/stable/tutorials/monotonic.html));
`sklearn.IsotonicRegression` with bounded
([sklearn docs](https://scikit-learn.org/stable/modules/generated/sklearn.isotonic.IsotonicRegression.html)).

**For this comp.**
- The latent-demand ceiling should be **non-decreasing** in: cooler_count,
  catchment_density, SKU breadth, outlet_size_ordinal. Enforcing this on
  the GBM frontier with `monotone_constraints` is **free regularisation**
  and looks great to judges ("we encoded domain monotonicity").
- Same trick on a deep Tobit head (Runje 2023 monotonic activations).

**Verdict: USE (cheap, immediate).** Set `monotone_constraints` on the
QGB frontier *today*. Sub-15-minute change.

---

### 9. DEA / Data Envelopment Analysis (peer frontier check)

**Refs.** Donthu & Yoo 1998
([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167811698000214));
Cherchye et al. (book chapter, 2018)
([Springer](https://ideas.repec.org/h/spr/isochp/978-3-319-99304-1_1.html));
Vyt et al. 2020 GIS+DEA loyalty supermarkets
([VGTU](https://journals.vilniustech.lt/index.php/JBEM/article/view/12393)).

**For this comp.** DEA already underpins the team's "peer frontier" idea.
Make it explicit: cluster by (size × type × province × distributor-season),
take the **upper envelope** of `volume / cooler_count` (or similar
intensity ratio) inside each cluster, use that as a peer ceiling. Python:
`pyDEA`, or roll-your-own with `scipy.spatial.ConvexHull` on (cooler,
volume).

**Verdict: USE as a cross-check.** Cite DEA literature in the report — it
turns the heuristic "peer frontier" into a named technique.

---

## Concrete Recommendations Table

| # | Method | Use? | Why (1 line) | Cost (h) |
|---|---|---|---|---|
| 1 | Tobit Type I (right-censored MLE on log-volume) | **USE** | Direct latent-demand head; pseudo-C from `constraint_score`; defendable as the canonical baseline. | 2-3 |
| 2 | Tobit Type II / Heckman | REJECT | No exclusion restriction, no unselected sub-population; can be worse than OLS. | 0 |
| 3 | Two-Tier SFA (Polachek-Yoon) | SUPPLEMENT (1-sided only) | Decomposes constraint loss `u`; full 2TSF tooling thin in Python, identification fragile. | 3-4 |
| 4 | Censored quantile regression (Powell / CH 2002) | **USE (key upgrade)** | Fixes current 90th-pct GBM bias from censored rows; CH 3-step is one propensity model. | 3-4 |
| 5 | EM unconstraining (Anupindi/Vulcano-style) | SUPPLEMENT | Iterative impute-and-refit, gives a robustness loop on Tobit/QGB. | 2-3 |
| 6 | Manski worst-case bounds | **USE (reporting)** | Honesty band around point estimate; turns size-uplift caps into a defensible interval. | 1 |
| 7 | Deep Tobit-NLL MLP | SUPPLEMENT (stretch) | Stacking second opinion + heteroscedastic σ; risk of overfit at 20k outlets. | 4-6 |
| 8 | Monotonic constraints (XGBoost / NN) | **USE** | Free regularisation + judge-friendly; one line of code change on QGB. | 0.25 |
| 9 | DEA peer envelope | **USE (cross-check)** | Names + cites what the team already does as a "peer frontier"; cheap presentation win. | 1 |

**Recommended execution order (36 h budget):**
1. (h 0-1) Build censoring indicator `δ_it` and pseudo-`C_i`.
2. (h 1-2) Add `monotone_constraints` to the existing QGB frontier (#8).
3. (h 2-5) CH 3-step censored quantile regression (#4) — refit QGB on
   `δ_hat < 0.1` subset. **This is the biggest single-method gain.**
4. (h 5-8) Tobit Type-I MLE on log-volume (#1) as a parallel head.
5. (h 8-9) DEA peer-envelope cross-check (#9) + Manski bounds (#6).
6. (h 9-12) Light 1-sided SFA via `pysfa` for `u`-decomposition (#3).
7. (h 12-15) One EM unconstraining loop (#5) on the Tobit head.
8. (h 15+) Deep Tobit-NLL MLP stacking layer (#7) if time allows.

The final point estimate is a **stacked blend** of (a) QGB-CH frontier,
(b) Tobit-Type-I head, (c) DEA peer envelope; reported alongside a
Manski [lo, hi] interval. Score-card mapping:

- **Data Forensics 40%** ← censoring indicator construction + plateau
  detection + EM imputation diagnostics.
- **Methodology 40%** ← Tobit + Censored Quantile + SFA + Manski names
  in the report, monotone constraints, sensitivity to pseudo-`C` choice.
- **GenAI 20%** ← orchestrate the swarm + GenAI-authored EDA + model-card
  generation (handled by other channels).

---

## References

Tobit / censored regression (Type I & II)
- *Microeconometrics with R*, Ch. 11 — Censored & truncated models
  https://ycroissant.github.io/micsr_book/chapters/tobit.html
- CRAN `censReg` vignette
  https://cran.r-project.org/web/packages/censReg/vignettes/censReg.pdf
- Cameron & Trivedi transparencies (Tobit / Type-II)
  https://cameron.econ.ucdavis.edu/mmabook/transparencies/ct16_tobit.pdf
- statsmodels Heckman impl
  https://github.com/statsmodels/statsmodels/blob/92ea62232fd63c7b60c60bee4517ab3711d906e3/statsmodels/regression/heckman.py
- Bookdown — Estimating Selection Models (Type-II)
  https://bookdown.org/christopherpadams/heckman/

Two-tier stochastic frontier
- Polachek & Yoon (1996), *J Appl Econometrics* 11(2) 169-178
  https://onlinelibrary.wiley.com/doi/10.1002/%28SICI%291099-1255%28199603%2911%3A2%3C169%3A%3AAID-JAE373%3E3.0.CO%3B2-%23
- Lai & Kumbhakar (2018), *J Productivity Analysis* — scaling property
  https://ideas.repec.org/a/kap/jproda/v49y2018i1d10.1007_s11123-017-0520-8.html
- Stata Journal (2023), `sftt` command
  https://ideas.repec.org/a/tsj/stataj/v23y2023i1p197-229.html
- 2TSF with heterogeneous error distributions (2024 preprint)
  https://www.researchsquare.com/article/rs-4437203/v1.pdf
- Python SFA packages: pysfa https://pypi.org/project/pysfa/ ;
  depp-sfa https://pypi.org/project/depp-sfa/0.1.3/ ;
  FronPy https://github.com/AlexStead/FronPy

Censored quantile regression
- Powell (1986) — censored LAD, Berkeley lecture notes
  https://eml.berkeley.edu/~powell/e242_f04/powell.pdf
- Chernozhukov & Hong (2002) *JASA* — Three-Step CQR
  https://www.mit.edu/~vchern/papers/Chernozhukov%20and%20Hong%20(JASA%202002)%20Three%20Step%20Censored%20Quantile%20Regression.pdf
- Koenker `quantreg::crq` vignette
  https://cran.r-project.org/web/packages/quantreg/vignettes/crq.pdf
- Velthoen et al. (2023) — gradient boosting for extreme quantiles,
  *Extremes* https://link.springer.com/article/10.1007/s10687-023-00473-x

EM / unconstraining literature
- Anupindi, Dada, Gupta (1998) — vending-machine stockout demand,
  *Marketing Science* 17(4)
  https://ideas.repec.org/a/inm/ormksc/v17y1998i4p406-423.html
- Vulcano, van Ryzin, Ratliff (2012) — Primary demand from sales
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1923711

Manski / partial identification
- *Causal Review* — Manski bounds primer
  https://www.causalreview.com/articles/partial-identification-and-manski-bounds-how-much-can-we-learn-without-strong-assumptions
- HIV non-response partial identification (medRxiv 2023)
  https://www.medrxiv.org/content/10.1101/2023.06.03.23290936v1

Deep censored regression
- Lin et al. (2024) — Deep Tobit, PubMed
  https://pubmed.ncbi.nlm.nih.gov/41571915/
- Friedman & Wilm (2024) — *Pattern Analysis and Applications*, three
  censored losses compared
  https://link.springer.com/article/10.1007/s10044-024-01216-9
- Variational Tobit GP regression (2023), *Stats & Computing*
  https://link.springer.com/article/10.1007/s11222-023-10225-3
- Deep learning for interval-censored data (2024), *EJS*
  https://projecteuclid.org/journals/electronic-journal-of-statistics/volume-18/issue-2/Deep-learning-for-regression-analysis-of-interval-censored-data/10.1214/24-EJS2298.full

Monotonic networks / GBMs
- Runje & Shankaranarayana (2023) — Constrained Monotonic NNs, ICML
  https://proceedings.mlr.press/v202/runje23a.html
  arxiv: https://arxiv.org/pdf/2205.11775
- XGBoost monotone_constraints
  https://xgboost.readthedocs.io/en/stable/tutorials/monotonic.html
- sklearn `IsotonicRegression`
  https://scikit-learn.org/stable/modules/generated/sklearn.isotonic.IsotonicRegression.html
- Bounded isotonic regression (Wu, Meyer 2017, *EJS*)
  https://projecteuclid.org/journals/electronic-journal-of-statistics/volume-11/issue-2/Bounded-isotonic-regression/10.1214/17-EJS1365.full

DEA / peer-frontier benchmarking
- Donthu & Yoo (1998) — restricted DEA for retail
  https://www.sciencedirect.com/science/article/abs/pii/S0167811698000214
- Cherchye et al. (2018) — DEA for post/banking branches
  https://ideas.repec.org/h/spr/isochp/978-3-319-99304-1_1.html
- Vyt et al. (2020) — DEA + GIS supermarkets
  https://journals.vilniustech.lt/index.php/JBEM/article/view/12393

Extreme value / POT for out-of-sample quantiles
- Ferreira et al. (2003) — POT for out-of-sample quantiles
  https://www.sciencedirect.com/science/article/abs/pii/S0167947301000871
- Girard & Stupfler (2010) — Frontier estimation & EVT
  https://projecteuclid.org/journals/bernoulli/volume-16/issue-4/Frontier-estimation-and-extreme-value-theory/10.3150/10-BEJ256.full

---

## Appendix — minimal Python sketches

**Tobit Type-I on log-volume (right-censored)**

```python
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm

def neg_loglik_tobit_right(params, y, X, delta):
    """delta=1 censored (we only know D > C_i, observation = C_i)."""
    p = X.shape[1]
    beta, log_sigma = params[:p], params[p]
    sigma = np.exp(log_sigma)
    mu = X @ beta
    z = (y - mu) / sigma
    ll_uncens = norm.logpdf(z) - log_sigma
    ll_cens   = norm.logsf(z)
    return -np.sum((1 - delta) * ll_uncens + delta * ll_cens)

X = np.column_stack([np.ones(n), feats])
p0 = np.concatenate([np.zeros(X.shape[1]), [0.0]])
res = minimize(neg_loglik_tobit_right, p0, args=(np.log1p(y), X, delta),
               method="L-BFGS-B")
```

**Chernozhukov-Hong 3-step CQR (τ = 0.90)**

```python
import lightgbm as lgb
import statsmodels.api as sm

prop = lgb.LGBMClassifier(objective="binary").fit(X_all, delta_all)
keep = prop.predict_proba(X_all)[:, 1] < 0.10
qr   = sm.QuantReg(y_all[keep], sm.add_constant(X_all[keep])).fit(q=0.90)
```

**Monotone constraints on existing quantile-GBM**

```python
mono = {"cooler_count": 1, "sku_breadth": 1, "catchment_density": 1,
        "outlet_size_ord": 1}
model = lgb.LGBMRegressor(
    objective="quantile", alpha=0.90,
    monotone_constraints=[mono.get(c, 0) for c in X.columns],
    monotone_constraints_method="advanced",
)
```

**Manski-style bounds (per outlet)**

```python
D_lo = obs_max_i
D_hi = obs_max_i * uplift_cap_by_size[outlet_size_i]
D_point = D_lo + constraint_score_i**1.25 * (peer_frontier_i - D_lo)
report = (D_lo, D_point, D_hi)
```
