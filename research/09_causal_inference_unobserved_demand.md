# 09 — Causal Inference for Unobserved (Uncapped) Demand

Research channel 9 of 10 — Data Storm 7.0 (Sri Lanka), 36-hour hackathon.
Target: estimate *latent maximum monthly volume* (liters) for 20,000 retail outlets, January 2026,
where `observed_sales = min(true_demand, constraints)` and we want the counterfactual
`Y(do(constraints removed))`.

---

# TL;DR

- **The target is not point-identified from observational data alone.** With no exogenous variation in
  constraints (credit, stockouts, delivery cap, cooler space, execution quality), no single causal
  estimator can recover `E[Y | do(constraints=0)]` without untestable assumptions. Pretending otherwise
  is the most common methodology failure judges will look for.
- **Recommended defensible stack for a 36 h hackathon:** combine (a) **Manski-style worst-case bounds**
  as an honest interval, (b) a **stochastic-frontier / quantile-envelope point estimate** as the
  business number, and (c) **DML / Causal Forest (EconML)** for *partial* sensitivity to one or two
  observable constraints (credit limit, delivery frequency). Present (a) first, (b) second, (c) third.
- **DAG-first framing wins the methodology marks.** Draw the DAG, mark what is identifiable
  (constraint → observed sales given controls), what is not (demand → potential given only observed
  sales), and run a Manski + Rosenbaum-style sensitivity check on the final number. That single
  page is worth more than any tuned model.

---

# 1. Identification Analysis

## 1.1 The DAG

Nodes:

- `X` — outlet attributes (province, distributor, outlet type, POI catchment, population density, prior
  cooler count, credit tier).
- `D` — true latent demand for the outlet in January 2026 (unobserved).
- `C` — operational constraints (credit limit, stockout days, delivery cap, cooler capacity, route
  execution quality).
- `Y_obs` — observed monthly volume (liters). `Y_obs = min(D, C)`.
- `Y*` — counterfactual *uncapped* volume = `D` if constraints removed. **This is the prediction
  target.**

Edges (assumed):

```
X ──► D ──► Y_obs
X ──► C ──► Y_obs
X ──► C                (outlet type / distributor zone shape constraints)
U_d ──► D              (unobserved demand shifters: local taste, weather, events)
U_c ──► C              (unobserved supply shifters: distributor relationship)
U_dc ──► D, U_dc ──► C (lurking confounder: market attractiveness lifts demand AND attracts more
                        delivery / credit — this is the dangerous edge)
```

Critically, `Y_obs` is a *deterministic, non-smooth* function of `D` and `C` (a min). This is **type-1
censoring with an unobserved censor**, which is harder than standard Tobit (Tobit assumes the censor
is observed). [Heckman 1979; Amemiya 1985].

## 1.2 What is and isn't identifiable

| Quantity | Identifiable from data? | Why |
|---|---|---|
| `E[Y_obs \| X]` | Yes | Trivial regression. |
| `P(D > C \| X)` (constrained probability) | Approximately, *if* we have a measured `C` proxy (e.g. stockout flag, credit headroom) | Standard binary classification. |
| `E[D \| X, D ≤ C]` (demand among uncons­trained outlets) | Yes — those are the *fully-served* rows | Conditional regression on a selected sample. |
| `E[D \| X, D > C]` (demand among constrained) | **Not point-identified.** Pearl: the cut on `D > C` is a collider w.r.t. `D`, so conditioning re-introduces bias. | This is the actual hackathon target. |
| `E[Y* \| X] = E[D \| X]` | Identified **only** under (i) selection-on-observables given a measured `C`, or (ii) a valid IV, or (iii) a parametric Heckman/SFA distribution assumption. | None of these are clean here. |

The team should state this trade-off explicitly in the report. Judges value honesty about identification
more than a fragile point estimate.

## 1.3 What the team's "natural" method (regress observed sales on X) implicitly assumes

A vanilla GBM on `(X → Y_obs)` predicting January 2026 implicitly assumes one of:

1. **No censoring in expectation:** `P(D > C | X) ≈ 0` for relevant outlets. False here — that's the
   whole problem.
2. **MAR / unconfoundedness of `C`:** `D ⊥ C | X`. Plausible only if `X` captures all common drivers
   of demand and constraints. Probably violated because market attractiveness drives both.
3. **Linear, additive constraint effect** that the GBM can implicitly net out. No basis for that.

Saying this out loud in the report turns a weakness into a methodology strength.

---

# 2. Method Survey (ranked by 36-h feasibility × defensibility)

## 2.1 Manski worst-case bounds — *use this, always present*

Reference: Manski (1990) "Nonparametric Bounds on Treatment Effects", AER P&P; Manski (2003)
*Partial Identification of Probability Distributions*.

**Idea.** Without assumptions, for each outlet:

- Lower bound on `Y*`: outlet's historical maximum monthly sales (last 24 m), because we know it
  *did* sell that much, so `D ≥ Y_obs_max`.
- Upper bound on `Y*`: the maximum monthly sales achieved by any "comparable" unconstrained outlet
  in the same catchment / POI cluster / cooler-tier — because no outlet in that strata is known
  to exceed that. Or a theoretical upper bound from POI catchment population × per-capita beverage
  consumption. [Manski 1990].

**Tightening assumptions you *can* defend:**

- **Monotone Treatment Response (MTR):** removing constraints can only increase volume, never
  decrease. Tightens the lower bound only — sets `Y* ≥ Y_obs`. Trivially true here.
- **Monotone Instrument (MIV):** if an instrument like distributor delivery frequency is
  *believed* to be monotonically related to `C` but not `D`, you can tighten the upper bound
  using outlets at the high-frequency tier. [Manski-Pepper 2000].

**Verdict.** Present the `[lower, upper]` Manski interval as a credible band around the point estimate.
This is the single highest-leverage methodology move for a 5-page judged report. It costs ~30 lines of
pandas.

## 2.2 Stochastic Frontier Analysis (SFA) — *recommended point estimate*

References: Aigner, Lovell, Schmidt (1977); Battese & Coelli (1995); Kumbhakar & Lovell (2003).

**Why it fits this problem better than Heckman.** SFA was designed for exactly the structure
`Y_obs = frontier(X) − inefficiency`, i.e. observed output ≤ a latent maximum. Map:

- `frontier(X) ≡ Y*(X)` (latent maximum potential).
- `inefficiency ≡ shortfall caused by C` (credit, stockout, execution).
- Two-sided noise stays as Gaussian.

**Spec.**
`log(Y_obs) = f(X) + v − u`, with `v ~ N(0, σ_v²)` (noise, can go either way) and
`u ~ N⁺(0, σ_u²)` or truncated normal (one-sided, ≥ 0, captures constraint shortfall).

The "uncapped" prediction is `exp(f(X̂) + v̂)`, i.e. set `u = 0`. This is the **operational counterfactual**
the business actually wants.

**Strengths.** Built-in latent ceiling; per-outlet efficiency score `E[exp(−u) | ε]` (Jondrow et al.
1982) is a free *constraint diagnostic*; reduces to a single GLM/MLE — fast.

**Weaknesses.** Distributional assumption on `u` is unverifiable; mis-specification can bias the
frontier. Mitigate by reporting SFA point estimate sandwiched inside the Manski band.

**Python.** `linearmodels` does not ship SFA. Use `frontier` package from R via `rpy2`, or implement
the half-normal MLE directly (~40 lines with `scipy.optimize`). There is also `pystoned` (PyPI) for
non-parametric stochastic semi-non-parametric envelope.

**This is my recommended primary number.**

## 2.3 Quantile envelope ("poor man's frontier") — *fastest fallback*

Train a GBM with quantile loss for τ = 0.90 or 0.95 of `Y_obs` given `X` (LightGBM
`objective="quantile", alpha=0.95`). The conditional 95th percentile of *observed* sales among similar
outlets is a defensible proxy for the upper envelope of demand at that profile.

**Why it works.** If at least 5% of outlets in each `X`-cell are essentially unconstrained, the
conditional p95 of `Y_obs` ≈ conditional max of `D`. [Hardle & Korostelev 1992; Daouia et al. on quantile
frontiers].

**Why judges will accept it.** Cite stochastic-frontier / quantile-frontier literature (Bernini et al.
2022; Daouia et al. 2014). Frame it as a "non-parametric upper-envelope estimator".

**Code budget.** ~10 lines. Pair with the Manski interval as a robustness check.

## 2.4 Heckman two-step (sample selection) — *use only if you have a constraint flag*

Reference: Heckman (1979) "Sample Selection Bias as a Specification Error", *Econometrica*.

**Structure.**
- Stage 1 (selection): probit of `Z = 1{outlet is unconstrained}` on `X` plus an **exclusion
  restriction** `W` that drives selection but not the demand outcome.
- Stage 2 (outcome): regress `Y_obs` on `X` plus the inverse Mills ratio λ from stage 1, fit on
  unconstrained outlets only. Predict for all 20,000 outlets, plugging in λ = 0 to recover the
  unconditional demand.

**Identification cost.** You *must* have a credible exclusion restriction `W` — something that shifts
constraint but not demand. Candidates (see §2.5 IV): distributor delivery frequency dummy, distance
to depot.

**Risk.** Without `W`, the Heckman model is only identified off the non-linearity of the Mills ratio —
fragile and routinely criticised [Puhani 2000 "The Heckman correction for sample selection and its
critique", JES]. Be explicit about this in the report.

**Verdict.** Worth a *secondary* run if you can get distance-to-depot from the distributor list.
Don't lead with it.

## 2.5 Instrumental Variables — *the dream, probably not delivered in 36h*

Reference: Imbens & Angrist (1994); Angrist & Pischke *Mostly Harmless Econometrics* ch. 4; Wooldridge
*Econometric Analysis of Cross Section and Panel Data* ch. 5.

**Valid IV requirements:** relevance (IV → C), exogeneity (IV ⊥ U_d), exclusion (IV → Y only through C).

**Candidate IVs in this dataset:**

| Candidate | Relevance | Exogeneity | Exclusion | Verdict |
|---|---|---|---|---|
| Distributor delivery frequency (`DIST_*` assigned schedule) | Strong (caps `C`) | Weak — distributors target high-volume zones (`U_dc`) | Weak — frequent visits also raise visibility/promo execution → affect `D` | Tainted, but the best you'll get |
| Distance to distributor depot | Medium (more distance → less frequent delivery) | Decent if outlet locations are sticky | Decent if no demographic gradient with distance | **Best candidate.** Worth a 2SLS attempt |
| Credit-cycle phase (early vs late month) | Strong on credit-driven stockouts | Plausibly exogenous *within* outlet | Possibly violated if customers shop by payday | Use for within-outlet variation only |
| Holiday / weather shocks | Could affect delivery routes | Yes | Violated — directly shifts demand | **No, exclusion fails** |

**Python.** `linearmodels` (`from linearmodels.iv import IV2SLS`) supports just-identified and
over-identified 2SLS with weak-IV diagnostics (first-stage F, Anderson-Rubin). `DoWhy` lets you encode
the IV in the DAG and run a refutation test (placebo, random common cause).

**Verdict.** Mention 2SLS in the report as the *ideal* approach, present results with distance-to-depot
as IV, but explicitly flag that the F-stat or exclusion is borderline. Use it for sensitivity, not as
the headline.

## 2.6 Regression Discontinuity (RD) — *probably not applicable*

References: Imbens & Lemieux (2008); Calonico, Cattaneo, Titiunik (2014).

**Search for sharp policy cutoffs in the dataset:**

- Cooler placement thresholds: if the distributor places a cooler when the outlet exceeds a sales
  threshold (e.g. >300 L/month qualifies for a free cooler), that creates an RD on cooler ownership —
  but the question is whether cooler *causes* extra sales, which is a side-quest, not the latent
  potential question.
- Credit limit tiers: if outlets at >X L/month historical get a higher credit ceiling, again RD
  identifies the *constraint relaxation*, not the unconstrained potential directly.
- Outlet-size bands (small/medium/large): unlikely to be set by sharp deterministic rules in this
  data; almost certainly continuous.

**Verdict.** Don't expect a clean RD. If the dataset reveals a cooler-placement or credit-tier
rule with a deterministic cutoff, that's a great robustness paragraph: cooler/credit
caused an X-liter lift at the threshold, scale up to imagine "all outlets at unconstrained tier".
But don't plan on it.

## 2.7 Causal Forest / DML (Athey-Wager, Chernozhukov) — *for HTE sensitivity only*

References: Wager & Athey (2018) "Estimation and Inference of Heterogeneous Treatment Effects using
Random Forests", JASA. Chernozhukov et al. (2018) "Double/Debiased Machine Learning", *Econometrics
Journal*. Athey, Tibshirani, Wager (2019) GRF.

**What it can do here.** *If* you treat a single observable constraint as the "treatment" (e.g.
`T = 1{has_cooler}`, or `T = delivery_frequency`), you can estimate CATE: how much more an outlet would
sell with the constraint relaxed, conditional on X. EconML `CausalForestDML` fits
`E[Y|X,W]` and `E[T|X,W]` via cross-fit ML, then a forest on the residuals; provides asymptotic CIs
and per-outlet CATE.

**What it cannot do here.** It still needs **unconfoundedness given `(X, W)`**. For the full
multi-constraint counterfactual `Y(do(C=0))` it would need a multi-dimensional treatment, which DML
supports in principle but compounds the identification burden.

**Recommended use.** Pick ONE concrete observable constraint (cooler presence, or distributor delivery
frequency tier). Estimate CATE: "removing this constraint adds θ̂(x) liters to outlet x". Add θ̂(x) to
the current observed sales as a *lower-bound on uncap*. Frame as a partial answer.

**Python.**

```python
from econml.dml import CausalForestDML
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier

est = CausalForestDML(
    model_y=GradientBoostingRegressor(),
    model_t=GradientBoostingClassifier(),  # if T binary; Regressor if continuous
    discrete_treatment=True,
    n_estimators=500, min_samples_leaf=10,
    random_state=42,
)
est.fit(Y=df["Y_obs"], T=df["has_cooler"], X=df[X_cols], W=df[W_cols])
cate = est.effect(df[X_cols])         # per-outlet CATE
ci_lower, ci_upper = est.effect_interval(df[X_cols], alpha=0.05)
```

## 2.8 Synthetic Control — *use a "donor-pool" *aggregator*, not the textbook version*

Reference: Abadie, Diamond, Hainmueller (2010) "Synthetic Control Methods for Comparative Case
Studies", JASA. Abadie (2021) "Using Synthetic Controls: Feasibility, Data Requirements, and
Methodological Aspects", JEL.

**Why textbook SCM doesn't fit.** Classical SCM is for *one* treated unit followed over time, with
many donor units in a clean pre-period. We have 20,000 outlets, mostly cross-section.

**Useful adaptation: matched-donor uncapping.** For each *constrained* outlet:

1. Identify the set of "comparable" outlets (same province × distributor × outlet type × POI density
   bucket).
2. Among that set, restrict to outlets where the constraint of interest is **slack** (e.g. credit
   headroom > 0, no stockouts last 6 m, has cooler). These are the *donors*.
3. The latent potential for the constrained outlet = weighted mean (or max) of donors, where weights
   minimise pre-period (covariate-space) distance to the focal outlet. This is essentially
   matching-on-X with a donor-pool restriction — explicitly framed as the *unconstrained* analog of
   the focal outlet.

**Python.** `causalpy` (PyMC-Labs) supports SCM cleanly. Or simply NN matching with `scikit-learn`'s
`NearestNeighbors` on a covariate Mahalanobis distance.

**Verdict.** Good "intuitive" methodology paragraph — judges understand it without econometrics
training. Adds little to a well-specified SFA but is great for *explainability*.

---

# 3. Recommended Causal Story for the Report (5 pages, ~600 words on methodology)

A defensible, judge-pleasing narrative arc:

1. **Frame the problem causally.** `Y_obs = min(D, C)`. We want `E[Y* | X] := E[D | X]`. State up
   front that this is a censored-with-unobserved-censor problem.

2. **Show the DAG.** One small figure. Annotate which arrows are identifiable and which are not.
   This alone is rare in hackathon submissions.

3. **State the identifying assumption explicitly.** We assume:
   - (A1) **Conditional independence of constraint shortfall:** given the full covariate vector `X`
     (province, distributor, outlet type, POI catchment, cooler tier, credit tier, historical
     volatility), the *residual* constraint shortfall is independent of latent demand.
   - (A2) **No reverse causality** from anticipated demand to credit/cooler allocation within the
     January 2026 horizon (delivery routes are pre-scheduled).
   - (A3) **Stable unit-treatment value** (one outlet's uncapping does not change another's demand
     within January).
   Justify each in plain language. Then estimate.

4. **Headline number.** Stochastic-Frontier point estimate of `Y*(X)`. Report per-outlet efficiency
   score `E[exp(−u) | ε]` as a sanity check.

5. **Honest interval.** Manski bounds `[max(Y_obs_hist), min(POI_catchment_cap, p95_envelope_X)]`
   for each outlet. Show that the SFA point estimate sits inside the bound for ≥ 95% of outlets;
   any outlet where it doesn't is flagged as low confidence.

6. **Sensitivity.** Pick the strongest unverifiable assumption (A1). Quantify how the headline
   answer moves if we allow a small unmeasured confounder. See §4.

7. **One CATE result for narrative.** Using EconML, "removing cooler constraint lifts volume by
   18 ± 4 L/month for medium-density outlets" — concrete, business-friendly, methodologically
   solid. Don't try to combine multiple causal effects.

8. **GenAI transparency.** Note that the causal stack was scoped with LLM assistance, every
   estimator was hand-validated, identifying assumptions were chosen by the team.

---

# 4. Sensitivity Plan

Three layers, listed by effort.

## 4.1 Rosenbaum-style sensitivity bound (one-page result)

Reference: Rosenbaum (2002) *Observational Studies*; Cinelli & Hazlett (2020) "Making Sense of
Sensitivity: Extending Omitted Variable Bias", *JRSS-B*.

For the SFA point estimate, ask: *how strong would an unmeasured confounder `U_dc` (market
attractiveness) have to be — measured in partial R² with both `D` and `C` — to flip the conclusion
that outlet `i` has uncapped potential above its current volume?* If even a confounder with R² = 0.5
on both sides doesn't change the verdict, the answer is robust.

**Python.** `dowhy.causal_estimators.RobustnessTest` or `sensemakr` (port to Python via `sensemakr-py`).

## 4.2 E-value (epidemiology import)

Reference: VanderWeele & Ding (2017) "Sensitivity Analysis in Observational Research: Introducing
the E-Value", *Annals of Internal Medicine*. Easy single number expressing the minimum
confounder strength needed to nullify the estimate. Mention in the report.

## 4.3 Bound-tightening experiments

- Re-run the SFA with `u` distribution swapped: half-normal vs truncated-normal vs exponential.
  Report point-estimate dispersion.
- Re-run quantile envelope at τ ∈ {0.85, 0.90, 0.95, 0.99}. Report dispersion.
- Re-run with the strictest Manski-Pepper monotone-IV assumption on distance-to-depot and the
  loosest no-assumption bound. Report the *interval width*.

If all three layers produce overlapping bands around the SFA estimate, the headline is defensible.

---

# 5. Python Library Recommendations (in priority order)

| Library | Use here | Cite version |
|---|---|---|
| `lightgbm` (quantile loss) | Conditional p95 envelope (§2.3) | latest |
| `scipy.optimize` | Hand-rolled SFA half-normal MLE (§2.2) | stdlib |
| `econml` (Microsoft ALICE) | `CausalForestDML` for CATE on one observable constraint (§2.7) | 0.16+ |
| `dowhy` (PyWhy) | Encode DAG, run identification + refutation checks (§1.2, §4.1) | 0.11+ |
| `linearmodels` | `IV2SLS` for distance-to-depot IV (§2.5) | 6.x |
| `causalpy` (PyMC-Labs) | Matched-donor synthetic control (§2.8) | 0.4+ |
| `pystoned` | Optional non-parametric stochastic envelope (§2.2 fallback) | 0.7+ |
| `sensemakr-py` | Cinelli-Hazlett sensitivity (§4.1) | 0.1+ |

Avoid hand-rolling Heckman; both `statsmodels` (via `Heckman` external package) and `R::sampleSelection`
through `rpy2` are more reliable.

---

# 6. References

**Causal identification / DAGs**
- Pearl J. (1995) "Causal diagrams for empirical research", *Biometrika* 82(4).
- Pearl J. (2009) *Causality: Models, Reasoning, and Inference* (2nd ed.), CUP.
- Hernán M. & Robins J. (2020) *Causal Inference: What If*, CRC.

**Selection bias / censored demand**
- Heckman J. (1979) "Sample Selection Bias as a Specification Error", *Econometrica* 47(1).
- Puhani P. (2000) "The Heckman Correction for Sample Selection and Its Critique", *Journal of
  Economic Surveys* 14(1).

**Partial identification**
- Manski C. (1990) "Nonparametric Bounds on Treatment Effects", *American Economic Review P&P* 80(2).
- Manski C. (2003) *Partial Identification of Probability Distributions*, Springer.
- Manski C. & Pepper J. (2000) "Monotone Instrumental Variables: With an Application to the Returns
  to Schooling", *Econometrica* 68(4).

**Instrumental variables**
- Imbens G. & Angrist J. (1994) "Identification and Estimation of Local Average Treatment Effects",
  *Econometrica* 62(2).
- Angrist J. & Pischke J.-S. (2009) *Mostly Harmless Econometrics*, Princeton.

**Stochastic Frontier**
- Aigner D., Lovell K., Schmidt P. (1977) "Formulation and Estimation of Stochastic Frontier
  Production Function Models", *Journal of Econometrics* 6(1).
- Kumbhakar S. & Lovell K. (2003) *Stochastic Frontier Analysis*, CUP.
- Jondrow J., Lovell K., Materov I., Schmidt P. (1982) "On the Estimation of Technical Inefficiency
  in the Stochastic Frontier Production Function Model", *Journal of Econometrics* 19.

**ML-augmented causal inference**
- Wager S. & Athey S. (2018) "Estimation and Inference of Heterogeneous Treatment Effects using
  Random Forests", *JASA* 113(523).
- Chernozhukov V., Chetverikov D., Demirer M., Duflo E., Hansen C., Newey W., Robins J. (2018)
  "Double/Debiased Machine Learning for Treatment and Structural Parameters", *Econometrics Journal*
  21(1).
- Athey S., Tibshirani J., Wager S. (2019) "Generalized Random Forests", *Annals of Statistics*
  47(2).

**Synthetic control**
- Abadie A., Diamond A., Hainmueller J. (2010) "Synthetic Control Methods for Comparative Case
  Studies", *JASA* 105(490).
- Abadie A. (2021) "Using Synthetic Controls: Feasibility, Data Requirements, and Methodological
  Aspects", *Journal of Economic Literature* 59(2).

**Regression Discontinuity**
- Imbens G. & Lemieux T. (2008) "Regression Discontinuity Designs: A Guide to Practice", *Journal of
  Econometrics* 142(2).
- Calonico S., Cattaneo M., Titiunik R. (2014) "Robust Nonparametric Confidence Intervals for
  Regression-Discontinuity Designs", *Econometrica* 82(6).

**Sensitivity analysis**
- Rosenbaum P. (2002) *Observational Studies* (2nd ed.), Springer.
- VanderWeele T. & Ding P. (2017) "Sensitivity Analysis in Observational Research: Introducing the
  E-Value", *Annals of Internal Medicine* 167(4).
- Cinelli C. & Hazlett C. (2020) "Making Sense of Sensitivity: Extending Omitted Variable Bias",
  *JRSS-B* 82(1).

**Software**
- Microsoft ALICE — EconML docs: https://econml.azurewebsites.net/
- PyWhy — DoWhy docs: https://www.pywhy.org/dowhy/
- `linearmodels` docs: https://bashtage.github.io/linearmodels/
- `causalpy` (PyMC-Labs): https://github.com/pymc-labs/CausalPy

---

*Channel 9 / 10 — `causal_inference_unobserved_demand`. Bias toward stating identification limits
rather than overclaiming. The team's most defensible result for the methodology 40% is a
**Manski-bounded SFA point estimate + DML sensitivity on one observable constraint + explicit
DAG**, not a tuned regressor on observed sales.*
