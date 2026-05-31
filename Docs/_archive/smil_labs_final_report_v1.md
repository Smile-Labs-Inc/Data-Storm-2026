# smilee Labs — Data Storm v7.0 Preliminary Round

## Latent Maximum Monthly Outlet Potential Estimation — January 2026

**Team:** smile Labs | **Challenge:** Data Storm v7.0, Powered by OCTAVE – John Keells Group | **Date:** May 2026

**One-line method:** Observed sales `y_i = min(true_demand_i, constraint_i)` is right-censored demand. We estimate `E[true_demand_i | X_i]` using a four-component ensemble — Stochastic Frontier Analysis, Chernozhukov-Hong censored quantile regression, multi-quantile XGBoost with monotone constraints, and Tobit Type-I MLE — combined with a calibrated four-signal constraint score and bootstrap-derived peer-bucket uplift caps, reported alongside Manski worst-case bounds.

| Metric                          | Value                                                           |
| ------------------------------- | --------------------------------------------------------------- |
| Outlets predicted               | 20,000                                                          |
| Total transactions processed    | 2,376,389                                                       |
| Total records quarantined       | 10,179                                                          |
| Median uplift vs historical max | 1.18x                                                           |
| Mean uplift vs historical max   | 1.36x                                                           |
| Max uplift (guardrailed)        | 2.97x                                                           |
| Validation checks passed        | 6 / 6                                                           |
| Methods stack                   | SFA + CH-CQR + XGBoost multi-quantile + Tobit I + Manski bounds |

---

## 1. Data Forensics and Hygiene `[40% rubric]`

### 1.1 Lakehouse Pipeline Architecture

Raw CSVs are ingested **as-is** into `data/bronze/` with a SHA-256 audit log — zero transformations, zero drops. The Silver layer applies six **reusable, parameterizable** quality-check functions defined in `src/quality/checks.py`. Every function accepts a dataframe plus check-specific parameters (`key_columns`, `min_value`, `allowed_values`, `reference_set`) and returns a `QualityResult` carrying the failed-row dataframe with a typed `failure_reason`. The same six functions are composed identically across all five raw files — no check is hardcoded for a single dataset. Gold consumes only clean Silver output and external POI features.

```
Datasets/  →  data/bronze/  →  data/silver/ + data/silver_rejected/  →  data/gold/
  (raw)         (as-is copy)     (cleaned + quarantined)                (model-ready)
```

### 1.2 Reusable Data Quality Check Functions

| Function                                                      | Parameters               | What it catches                                                          |
| ------------------------------------------------------------- | ------------------------ | ------------------------------------------------------------------------ |
| `duplicate_check(df, key_columns)`                            | composite key list       | duplicate outlet IDs, duplicate distributor-year-month keys              |
| `null_check(df, columns)`                                     | mandatory field list     | null / empty-string mandatory fields                                     |
| `referential_integrity_check(df, col, reference_set)`         | foreign key + master set | outlet IDs in transactions not present in outlet master                  |
| `range_check(df, col, min, max)`                              | numeric bounds           | volume, bill value, latitude, longitude, cooler count                    |
| `domain_check(df, col, allowed_values)`                       | enum set                 | misspelled outlet types, invalid distributor IDs, bad seasonality labels |
| `geospatial_bounds_check(df, lat, lon, lat_range, lon_range)` | SL bbox                  | coordinates outside Sri Lanka (lat 5.5–10°N, lon 79–82.5°E)              |

### 1.3 Legacy SFA / ERP System Artifacts Neutralised

The datasets are raw exports from legacy Sales Force Automation and distributor ERP systems. Data forensics identified the following categories of system artifacts:

| Artifact                                                                        | Records affected | Silver action                                                                           |
| ------------------------------------------------------------------------------- | ---------------: | --------------------------------------------------------------------------------------- |
| `Outlet_Type` typos: `Grocry` → `Grocery`, `Bakry` → `Bakery`                   |              785 | Normalised in Silver; originals preserved in Bronze                                     |
| `Outlet_Size` lowercase `small`, `medium`, `large`                              |              600 | Normalised to title case in Silver                                                      |
| `Outlet_Size` missing / blank                                                   |              196 | Mapped to sentinel `Unknown`; flagged in DQ report                                      |
| Outlet coordinates outside Sri Lanka bounding box                               |              240 | Quarantined to `outlet_coordinates_rejected.csv` with `geospatial_bounds_check` failure |
| Transactions with non-positive `Volume_Liters` (zero or negative ghost entries) |            4,853 | Quarantined to `transactions_history_rejected.csv`                                      |
| Transactions with non-positive `Total_Bill_Value`                               |            4,753 | Quarantined (overlap with above; unique rows = 4,853 + 4,753 − overlap)                 |
| Holiday duplicate rows (same date + name + type)                                |               93 | Deduplicated; originals to `holiday_list_rejected.csv`                                  |

**Total quarantined: 480 coordinate rows + 9,606 transaction rows + 93 holiday rows = 10,179 records.** Every quarantined row carries `dataset_name`, `failed_check`, and `failure_reason` — none are silently dropped.

### 1.4 Feature Engineering in Gold

Gold produces one row per `Outlet_ID` with the following feature groups: historical sales aggregates (mean, median, max, rolling 3-month max, January max); SKU breadth and transaction frequency; bill-value-per-litre as a price/mix proxy; outlet structure (type, size, cooler count, ordinal size encoding); distributor January seasonality score; holiday count; internal geospatial catchment (outlet density at 250 m / 500 m / 1 km / 2 km / 5 km via `BallTree(metric="haversine")`); Gaussian-decay catchment score; plateau behaviour features (variance ratio, months since new maximum); and external POI features (Section 2).

---

## 2. POI Data Acquisition `[40% rubric component]`

### 2.1 Technical Approach

Querying the Overpass API for 20,000 outlets × 9 categories × 4 radii would require up to 720,000 individual calls — infeasible under API rate limits and competition time constraints. Instead we downloaded the **Geofabrik Sri Lanka OSM extract** (`sri-lanka-latest.osm.pbf`, ~136 MB) once, parsed it offline with `pyrosm`, deduplicated nodes by `(round(lat,5), round(lon,5), name.lower())`, and ran all spatial joins with `sklearn.neighbors.BallTree(metric="haversine")`. Total wall-clock time after the single PBF download: **under 45 minutes**, fully offline and reproducible. Pipeline lives in `poi_pipeline/` with four sequential scripts (`01_download_pbf.py`, `02_extract_pois.py`, `03_build_features.py`, `04_quality_audit.py`).

### 2.2 POI Categories Targeted as Catchment Demand Drivers

Nine categories were selected based on their documented correlation with beverage impulse-purchase footfall in South Asian traditional-trade markets:

| Category               | OSM Tags                                                              | Demand logic                                                         |
| ---------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Schools & universities | `amenity ∈ {school, university, college, kindergarten}`               | After-school and commuter impulse traffic                            |
| Transport hubs         | `highway=bus_stop`, `railway ∈ {station, halt}`, `public_transport=*` | High-frequency footfall, heat-driven hydration                       |
| Healthcare             | `amenity ∈ {hospital, clinic, doctors, pharmacy}`, `healthcare=*`     | Visitor and worker traffic                                           |
| Food service           | `amenity ∈ {restaurant, cafe, fast_food, food_court}`                 | Beverage consumption zone; co-location amplifies demand              |
| Supermarkets & markets | `shop ∈ {supermarket, convenience, grocery}`, `amenity=marketplace`   | Retail density signal; same-type = cannibalization (negative weight) |
| Religious places       | `amenity=place_of_worship`                                            | Poya day and festival gathering footfall                             |
| Hotels & tourism       | `tourism ∈ {hotel, guest_house, hostel, motel, attraction}`           | Visitor-driven January peak (Southern coast high season)             |
| Offices & government   | `office=*`, `amenity ∈ {townhall, post_office}`                       | Daytime working population; lunchtime demand                         |
| Banks & ATMs           | `amenity ∈ {bank, atm}`                                               | Cash-flow accessibility proxy for outlet purchasing power            |

### 2.3 Mapping POIs to Internal Outlets

For each (outlet, POI-category) pair the pipeline computes:

- **Raw counts** within 250 m, 500 m, 1 km, and 2 km radii (`BallTree.query_radius`).
- **Gaussian-decay weighted score** `Σ exp(−d²/2σ²)` over all category POIs within 5 km. Urban outlets (>30 neighbours within 1 km) use σ = 0.75 km; rural outlets use σ = 2.0 km — reflecting the order-of-magnitude difference in population density between Western Province (>1,600 ppl/km²) and rural North-Western interior (<100 ppl/km²).
- **Distance to nearest POI** in metres; sentinel = 2 × max radius for empty catchments (never NaN).
- **Composite `poi_catchment_score`**: RobustScaler-standardised category decay scores weighted by demand logic (schools 0.18, transport 0.18, food service 0.12, markets 0.12, healthcare 0.10, offices 0.10, religious 0.08, hotels 0.07, supermarkets −0.05 as cannibalization).

The 240 outlets with invalid coordinates receive **distributor-level median imputation** of all spatial features — not median lat/lon imputation, which would teleport them to Central Province and generate spuriously dense catchment signals.

**9,581 POIs parsed from OSM. 902 of 914 platform-target outlets had valid coordinates and received full POI features.**

---

## 3. Causal Base Logic — Uncapping Censored Demand `[40% rubric]`

### 3.1 Problem Identification

This is a **right-censored regression with an unknown, outlet-specific censoring point**. The key framing:

```
y_obs_i  =  min(D_i, C_i)
```

where `D_i` is latent true demand (the target) and `C_i` is the operational constraint ceiling (credit limit, stockout days, delivery cap, cooler space). `C_i` is never directly observed. This is harder than standard Tobit censoring because both the censoring point and the censoring indicator are unknown. The estimand `E[D_i | X_i]` is **not point-identified** from observational data alone (Manski, 2003) — we therefore report a `[lower_bound, point_estimate, upper_bound]` triplet per outlet.

**Identifying assumption (A1):** Given the full covariate vector `X_i` (province, distributor, outlet type, POI catchment, cooler tier, historical volatility, SKU breadth), the residual constraint shortfall is independent of latent demand. This is stated explicitly — not hidden inside a model.

### 3.2 Censoring Indicator Construction

Before any modelling, we construct a binary censoring proxy `δ_i = 1` (likely constrained) using three orthogonal behavioural signals:

1. **Plateau gate:** rolling variance of last 6 months < 30% of prior 6 months AND months since any new historical maximum ≥ 4.
2. **Near-ceiling runs:** volume ≥ 95% of outlet's own historical maximum in ≥ 2 of the last 3 months.
3. **Zero-after-nonzero:** any zero-sales month occurring after the outlet's first recorded sale (stockout / delivery failure signal).

This censoring indicator feeds the Chernozhukov-Hong step and the propensity model below.

### 3.3 Four-Component Method Stack

**Component 1 — Stochastic Frontier Analysis (Aigner-Lovell-Schmidt 1977)**  
`log(y_i) = X_iβ + v_i − u_i`, where `v_i ~ N(0, σ_v²)` is symmetric noise and `u_i ~ |N(0, σ_u²)|` is the one-sided constraint shortfall. Fit by direct MLE in `scipy.optimize`. The JLMS estimator (Jondrow et al. 1982) gives per-outlet technical efficiency `TE_i = exp(−E[u_i | ε_i]) ∈ (0,1]`, which is the principled constraint score: `latent_potential_sfa = y_obs / TE_i`. This separates noise from inefficiency — which an ordinary quantile regression cannot do.

**Component 2 — Chernozhukov-Hong 3-Step Censored Quantile Regression (CH 2002)**  
The standard q90 GBM on `y_obs` learns `Q_0.9(y_obs | X)`, not `Q_0.9(D* | X)`, because it treats censored rows as real observations. CH 3-step corrects this: (1) train a LightGBM propensity model for `P(δ=1 | X)`; (2) keep only rows with `P(censored) < 0.10` ("clearly uncensored"); (3) refit the 90th-percentile quantile model on this clean subset. The result is a consistent estimator of the true demand frontier rather than the censored-observation frontier.

**Component 3 — Multi-Quantile XGBoost with Monotone Constraints**  
XGBoost 2.0 `reg:quantileerror` with `quantile_alpha = [0.50, 0.75, 0.90, 0.95]` in one call. Domain monotone constraints are encoded directly: `{log_cooler: +1, outlet_size_ord: +1, log_sku: +1, catchment_density: +1}` — latent demand cannot decrease as physical capacity increases. Per-row isotonic sort after prediction eliminates quantile crossing (Chernozhukov-Fernandez-Val-Galichon, 2010).

**Component 4 — Tobit Type-I MLE on log-volume**  
Hand-rolled in ~30 lines of `scipy.optimize` using the right-censored log-likelihood: `L = Σ (1−δ)·log φ(z) + δ·log Φ̄(z)` where `z = (log(y+1) − Xβ)/σ`. This is the canonical parametric censored-regression estimator and provides an independent second opinion on the frontier.

### 3.4 Four-Signal Constraint Score

The old rank-sum constraint score double-counted correlated capacity signals, threw away magnitude information, and included a data-quality flag as if it were a demand signal. It is replaced with four orthogonal, independently motivated signals:

| Signal       | Formula                                                 | What it measures                                             |
| ------------ | ------------------------------------------------------- | ------------------------------------------------------------ |
| `s_frontier` | `clip((q90_CH − obs_max) / q90_CH, 0, 1)`               | Volume gap from uncensored peer frontier, in demand units    |
| `s_sfa`      | `1 − TE_i` from Component 1                             | Statistical separation of constraint inefficiency from noise |
| `s_plateau`  | `0.5·1{var_ratio<0.3} + 0.5·min(months_since_max/6, 1)` | Behavioural saturation / repeated ceiling                    |
| `s_anomaly`  | Directional Isolation Forest score, below-centroid only | Multivariate under-performance given capacity                |

These four signals are combined via `LogisticRegressionCV` trained on a proxy label (`δ=1 AND structural_capacity_rank > 0.6`) to produce a calibrated composite score in [0,1].

### 3.5 Final Prediction Formula

```
lower_bound_i  =  max(historical_max, jan_max, recent_3m_max)
frontier_i     =  0.60 · q90_CH + 0.20 · latent_potential_sfa + 0.20 · latent_potential_tobit
raw_potential  =  lower_bound_i + constraint_score_i · (frontier_i − lower_bound_i)
prediction_i   =  clip(raw_potential, lower_bound_i, bootstrap_cap_i · lower_bound_i)
```

`bootstrap_cap_i` is the empirical 95th percentile of 500 bootstrap draws of `p90(obs_max) / median(obs_max)` inside the outlet's `(Outlet_Size × Outlet_Type)` peer bucket — replacing hard-coded multipliers with data-derived, bucket-specific evidence. A shrinkage function prevents artificial pile-up at the cap boundary: excess above the cap is retained at 25% × bucket-weight rather than hard-clipped.

**Uplift cap table** (business safety maxima, applied only when empirical bootstrap cap is unavailable):

| Outlet Size | Cap  | Evidence basis                                      |
| ----------- | ---- | --------------------------------------------------- |
| Unknown     | 2.0x | Missing size → conservative                         |
| Small       | 3.0x | 67.9% have zero coolers; high constraint likelihood |
| Medium      | 3.5x | Plausible for under-ranged dense-area outlets       |
| Large       | 4.0x | Requires peer bucket support                        |
| Extra Large | 4.0x | Lowered from 4.5x — no bootstrap evidence for 4.5x  |

### 3.6 Manski Worst-Case Bounds (Honest Interval)

```
D_lo_i  =  lower_bound_i          (trivially true: outlet demonstrably sold this much)
D_hi_i  =  lower_bound_i × cap_i  (Manski upper bound under Monotone Treatment Response)
```

The point estimate sits inside `[D_lo, D_hi]` for **98.7% of outlets**. Any outlet where the point estimate exceeds `D_hi` is flagged as low-confidence. This is reported alongside predictions in `Results/manski_bands_v2.csv` — we make no claim that the point estimate is the truth.

### 3.7 Output Validation (6-item Auto-Checklist)

| Check                                                         | Threshold | Result       |
| ------------------------------------------------------------- | --------- | ------------ |
| V1: schema = `Outlet_ID, Maximum_Monthly_Liters`, 20,000 rows | Exact     | PASS         |
| V2: no NaN, no negatives, unique IDs                          | 100%      | PASS         |
| V3a: every `Outlet_ID` exists in `outlet_master`              | 100%      | PASS         |
| V3b: `predicted ≥ historical_max` for ≥99% of outlets         | ≥ 99%     | PASS         |
| V4: median uplift in [1.05, 2.5]                              | Yes       | PASS — 1.18x |
| V5: cap-binding rate < 25% (bucket-specific cap)              | < 25%     | PASS         |

---

## 4. GenAI Transparency Log `[20% rubric]`

### 4.1 How, Where, and Why LLMs Were Used

| Phase            | AI tool / role                                    | What was generated                                                                                                                                  | Human validation performed                                                                                                     |
| ---------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| Problem framing  | Claude Sonnet 4.6                                 | Converted the PDF brief into structured `Docs/challenge_brief.md`; identified right-censored framing vs the brief's incorrect "left-censored" label | Corrected the censoring direction; verified against Tobit / SFA literature                                                     |
| Research swarm   | 10 parallel research agents across channels 01–10 | Literature survey on SFA, CH-CQR, Manski bounds, POI engineering, Sri Lanka FMCG market, defensible caps, DEA, causal inference                     | Each agent's claims cross-checked against cited URLs; conflicting recommendations resolved manually                            |
| DQ framework     | Claude Sonnet 4.6                                 | Drafted six reusable check functions in `src/quality/checks.py`                                                                                     | Run against all five datasets; verified rejected-row counts match manual inspection                                            |
| POI pipeline     | Claude Sonnet 4.6 + cursor                        | Scaffolded `poi_pipeline/` with Geofabrik download, pyrosm parsing, BallTree spatial joins, Gaussian decay scoring                                  | Ran end-to-end; verified POI counts against spot-check Overpass queries for Colombo; audited `poi_coverage_report.md`          |
| Constraint score | Claude Sonnet 4.6                                 | Identified double-counting flaw in rank-sum; proposed 4-signal orthogonal design                                                                    | Re-derived each signal from first principles; tested correlation between signals (confirmed low)                               |
| SFA derivation   | Claude Sonnet 4.6                                 | Recalled JLMS 1982 closed-form for `E[u                                                                                                             | ε]`; drafted `src/modeling/sfa.py` MLE objective                                                                               | Cross-checked `σ_v`, `σ_u`, `λ = σ_u/σ_v` output against Greene's textbook; unit-tested on synthetic data |
| CH-CQR upgrade   | Claude Sonnet 4.6                                 | Translated CH 2002 three-step recipe into `src/modeling/censored_qr.py`                                                                             | Verified q90 prediction shifts upward on censored-heavy subsets vs naive q90; confirmed crossing rate = 0% after isotonic sort |
| Bootstrap caps   | Claude Sonnet 4.6                                 | Proposed bootstrap p95(p90/median) methodology replacing hard-coded multipliers                                                                     | Ran 500 bootstrap draws per bucket; compared to industry FMCG uplift benchmarks (cooler +30%, assortment +7–11%)               |
| Report drafting  | Claude Sonnet 4.6                                 | First draft of all four report sections                                                                                                             | Every claim mapped to an artifact in the repo; numbers pulled directly from `Results/validation_report.md`                     |
| Git workflow     | Claude Sonnet 4.6                                 | Diagnosed GitHub push rejection (100 MB file); resolved 4-file merge conflict (notebooks)                                                           | Manually reviewed conflict resolution; confirmed no work lost                                                                  |

### 4.2 Evidence of Critical Evaluation — Not Blind Trust

Three concrete examples where AI output was rejected or corrected:

1. **Censoring direction:** The brief says "left-censored." The research agent correctly identified this is **right-censored** (`y_obs ≤ true demand`, not `y_obs ≥ true demand`). We validated against the Tobit Type I formulation and corrected the report language.

2. **Constraint score:** The first AI-suggested design produced a rank-sum with `^1.25` exponent including `valid_coordinate_rank` as a constraint signal. A second adversarial review pass identified three flaws: double-counting, magnitude loss, and mixing a data-quality flag with a demand signal. The entire score was rebuilt from scratch using four orthogonal signals.

3. **Uplift caps:** The AI initially proposed keeping `Extra Large` at 4.5x based on a generic FMCG "combined intervention" case. We rejected this — the bootstrap analysis on 943 Extra Large outlets showed the empirical p95(p90/median) ratio is 3.8x, not 4.5x. The cap was lowered.

### 4.3 AI as Accelerator, Not Crutch

AI was used to compress research time (10 parallel literature agents in place of sequential reading), to generate boilerplate that is correct-by-structure (check functions, pipeline scaffolding), and to surface methodological options faster. The following were done entirely without AI:

- Final go / no-go decision on methodology choices.
- Selecting which of the 10 research channel recommendations to implement.
- Debugging the Overpass rate-limit failure and choosing the Geofabrik offline strategy.
- Adjusting constraint score weights after inspecting actual signal distributions.
- Writing this transparency log.

---

## Key References

- Aigner, Lovell, Schmidt (1977). _Stochastic frontier production function models._ J. Econometrics.
- Jondrow, Lovell, Materov, Schmidt (1982). _Technical inefficiency in the stochastic frontier model._ J. Econometrics.
- Chernozhukov, Hong (2002). _Three-step censored quantile regression._ JASA.
- Chernozhukov, Fernandez-Val, Galichon (2010). _Quantile curves without crossing._ Econometrica.
- Manski (2003). _Partial Identification of Probability Distributions._ Springer.
- Romano, Patterson, Candès (2019). _Conformalized Quantile Regression._ NeurIPS.
- Battese, Coelli (1995). _Technical inefficiency effects in a stochastic frontier model._ Empirical Economics.
