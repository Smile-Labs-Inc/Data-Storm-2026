# Research Brief — Data Storm 7.0 Latent Demand Estimation

**Synthesised from 10 parallel premium-model research channels.**
**Date:** 2026-05-15 (T-30h to comp start at 06:00).
**Hackathon length:** 36 hours.
**Judging:** 40% DE/Forensics + 40% Methodology + 20% GenAI Workflow.

---

## 1. The Problem in One Line

`observed_volume = min(true_demand, operational_constraint)` — right-censored, **not point-identified** from observational data alone. The job is to build the **most defensible** uncapping framework, not to "win" a number.

---

## 2. Convergent Findings (where multiple channels agree)

These are independent recommendations from 2+ channels — high confidence.

| # | Recommendation | Channels | Why |
|---|---|---|---|
| C1 | **Use Stochastic Frontier Analysis (SFA) as the core econometric story** | 1, 2, 7, 9 | `y = f(X) − u, u ≥ 0` literally separates frontier from constraint. `TE = exp(−E[u\|ε])` *is* the constraint score with 50 years of theory behind it. |
| C2 | **Pair SFA with Conformalized Quantile Regression for the prediction interval** | 1, 3 | Quantile GBM gives the upper edge; CQR gives calibrated coverage. Cite Romano et al. NeurIPS 2019. |
| C3 | **Use Manski-style worst-case bounds for honest identification disclosure** | 1, 9 | Reports `[lower_bound, point_estimate, upper_bound]`. Methodology-rubric gold. |
| C4 | **Switch q90 fit from sklearn QuantileGB to XGBoost 2.0 `reg:quantileerror` with `quantile_alpha=[0.5, 0.75, 0.9, 0.95]`** | 3 (with 1, 7 supporting) | Single fit, multiple quantiles, monotone constraints, faster. |
| C5 | **Apply Chernozhukov-Hong 3-step censored quantile regression** | 1 | Train δ-propensity on censoring proxies → refit q90 only on rows with `P(censored) < 0.10` → corrects the bias from training on capped sales. |
| C6 | **Drop live Overpass for 720k calls; download Geofabrik Sri Lanka PBF (~136 MB) once, run pyrosm + geopandas locally** | 4, 6 | 10–25 min wall-clock vs days. |
| C7 | **Use Two-Tier SFA (Polachek-Yoon 1987) variant if time permits** | 2, 1 | `ε = v + w − u` directly mirrors `min(true, constraint)`. Strongest fit, but no mature Python lib (~150 lines hand-rolled). |
| C8 | **Drop the team's current rank-sum `constraint_score`; replace with PCA-decorrelated + frontier-residual + plateau-gate composite** | 7 | Current method double-counts correlated capacity ranks and uses `valid_coordinate_rank` (a DQ flag, not a constraint signal). Calibrate via supervised proxy label, not the hard-coded `^1.25` exponent. |

---

## 3. Critical Bugs Found in Existing Codebase

These need fixing **before** any further modelling. Discovered by channels 6 (POI), and cross-referenced with what we read in `Docs/`.

| Bug | Severity | Source | Fix |
|---|---|---|---|
| **Submission column is `row_id` not `Outlet_ID`** | BLOCKER | Official PDF says `Outlet_ID`; current `Results/teamname_predictions.csv` uses `row_id` | rename column |
| **Submission has 914 rows; brief asks for 20,000** | BLOCKER | Official PDF mentions no row-count limit; the 914 came from "platform validator" assumption that we cannot verify | use `teamname_predictions_full_20000.csv` as the platform CSV |
| **240 invalid coordinates silently median-imputed** | MAJOR | Channel 6 read the notebook; current code teleports them to one fake location | Use NaN + tree-native handling, or distributor-median imputation of *derived* features |
| **`same_type_outlet_count_2km` sign is wrong** | MAJOR | Channel 6 | It's currently positive (treated as catchment); same-type outlets are *cannibalisation*. Flip sign or split into "same-type within 200m" (negative) and "all-type within 2km" (positive). |
| **`valid_coordinate_rank` in constraint_score** | MODERATE | Channel 7 | A data-quality flag is not a demand-constraint signal. Remove. |

---

## 4. Top-5 Action Plan for the 36 Hours (ranked ROI × hours)

| Rank | Task | Hours | Rubric weight | Expected lift |
|---|---|---|---|---|
| **1** | **Bug fixes above (sub +Outlet_ID, 20k rows, sign flip, coord fix)** | 1 h | basic correctness | unblocks everything |
| **2** | **POI pipeline via Geofabrik PBF + pyrosm + geopandas** | 4–6 h | DE 40% + Method 40% | biggest single lift; mandatory per rubric |
| **3** | **Replace constraint_score with PCA + frontier-residual + plateau-gate composite** | 3–4 h | Method 40% | makes core model defensible |
| **4** | **Add SFA fit via `pySFA` / `FronPy` as a second methodology track** | 2–3 h | Method 40% | cite Aigner-Lovell-Schmidt 1977; gives report a peer-reviewed econometric narrative |
| **5** | **Switch q90 to XGBoost 2.0 multi-quantile + Conformalized QR (MAPIE)** | 1–2 h | Method 40% | calibrated intervals → stronger report |
| 6 | Manski bounds + DAG section in report | 2 h | Method 40% | causal sophistication |
| 7 | Sri Lanka domain features (April Avurudu, Poya days, distance-to-depot) | 1 h | Method 40% | cheap wins from channel 5 |
| 8 | Auto-built GenAI transparency log per phase | ongoing | GenAI 20% | partial freebie |

**Critical path:** start (1) immediately, kick off (2) in background, do (3) and (4) in parallel, finalise with (5)+(6)+(7).

---

## 5. Open Methodology Debates (council should resolve)

| Debate | Channel A says | Channel B says | Decision needed |
|---|---|---|---|
| Heckman selection model | REJECT — no exclusion restriction (ch 1) | USE as part of stack (ch 9) | Lean REJECT for 36h; revisit only if a clean exclusion is found |
| DEA on 20k DMUs | USE as named cross-check (ch 1) | REJECT — too slow, no noise term, outlier-sensitive (ch 7) | Lean REJECT in pipeline; fine to MENTION in report as an alternative considered and discarded |
| Quantile τ for Extra Large (n=943) | q90 safe (ch 3) | q95 unsafe with sparse cells (ch 3) | Use q90 across the board; q95 only as a sanity comparison |
| Two-Tier SFA (worth 150 LOC?) | "best variant" (ch 2) | not mentioned by ch 1 | Time-box: 2h prototype; if results are coherent, ship; else fall back to standard SFA |
| Same-type outlet counts | Cannibalisation (ch 6) | Catchment (current code) | Cannibalisation. Flip sign. |

---

## 6. Sri Lanka Domain Notes (channel 5)

- Data source is almost certainly **Elephant House / Ceylon Cold Stores** (John Keells beverage subsidiary).
- Province sales drivers: **Western** = urban purchasing power; **Central** = tourist + tea estates; **North-Western** = agri; **Southern** = tourism + fishing.
- Calendar features to ADD beyond the holiday list:
  - **April Sinhala/Tamil New Year (Avurudu)** — biggest annual consumption spike.
  - **December tourist peak + Christmas**.
  - **Poya days** (monthly Buddhist full-moon; some are *alcohol-restricted* — affects beverage mix; relevant if SKU mix matters).
  - **Vesak** (May).
  - **Ramadan/Eid + Deepavali** for relevant communities.
- Constraint patterns specific to LK retail: 3–30 day credit cycles; 1–3x/week distributor delivery; cooler-placement competition (Coca-Cola vs Elephant House vs Pepsi); election-period restrictions.

---

## 7. POI Acquisition Playbook (channel 4 — execute first)

```
Step 1: Download Geofabrik LK PBF (one shot, ~136 MB)
        wget https://download.geofabrik.de/asia/sri-lanka-latest.osm.pbf

Step 2: Use pyrosm to extract POIs by category
        pip install pyrosm geopandas h3 sklearn
        # categories: amenity (school, hospital, place_of_worship, bus_station,
        #             restaurant, cafe), shop (supermarket, bakery, convenience),
        #             tourism (hotel, attraction), railway (station), highway=bus_stop,
        #             office, healthcare

Step 3: For each POI category, build BallTree(haversine) on POI coords
        For each outlet, compute:
          - count within 250m, 500m, 1km, 2km
          - Gaussian-decay weighted score (sigma=0.75km urban / 2.0km rural)
          - distance to nearest

Step 4: 9 categories x (4 counts + 1 score + 1 distance) = ~54 new features
        Write to data/silver/poi_features.parquet

Step 5: Defaults for sparse outlets:
          dist_nearest = 2 * max_radius (NOT NaN)
          count = 0

Step 6: Coverage caveat for the report:
          schools / hospitals / banks / hotels well-mapped in LK
          small kades / independent grocers thinly mapped — flag honestly
```

Wall-clock estimate: ~25 min PBF processing + ~30 min spatial joins for 19,760 valid-coord outlets.

---

## 8. Per-Channel Quick References

| File | Headline takeaway |
|---|---|
| `01_latent_demand_modeling.md` | Treat as right-censored. Use Chernozhukov-Hong 3-step censored QR. Manski bounds for honesty. |
| `02_stochastic_frontier_analysis.md` | SFA is *the* textbook fit. Truncated-normal `u` beats half-normal for LK. Use FronPy. |
| `03_quantile_regression_for_potential.md` | XGBoost 2.0 multi-quantile + Conformalized QR via MAPIE. Pool model with type×size as cats + monotone constraints. |
| `04_osm_overpass_for_sri_lanka.md` | Geofabrik PBF >> live Overpass. Show Overpass QL for the rubric, execute via PBF. |
| `05_sri_lanka_fmcg_market.md` | Elephant House / CCS. Avurudu, Poya, Vesak, Deepavali, December tourism. 10 LK-specific feature ideas. |
| `06_poi_feature_engineering.md` | Keep BallTree spine. Add 250/500m rings + Gaussian decay. Flip same-type sign. Fix coord-imputation bug. |
| `07_constraint_likelihood_methods.md` | Drop rank-sum constraint score. Use PCA + frontier-residual + plateau gate, calibrated via proxy label. |
| `08_past_data_storm_winners.md` | Past judges valued business framing + report quality + viva pitch over pure modelling. |
| `09_causal_inference_unobserved_demand.md` | Not point-identified — say so. Manski bounds + SFA + EconML CausalForestDML stack. Add Rosenbaum/E-value sensitivity. |
| `10_defensible_uplift_caps.md` | Lower Extra Large cap from 4.5x → 4.0x unless bootstrap supports higher. Estimate caps from data, don't hardcode. |

---

## 9. The Methodology Story for the Report (skeleton)

A good 5-page report should follow this arc, anchored in cited methods:

1. **Problem framing**: right-censored latent variable, not point-identified (Manski 2003).
2. **Identification strategy**: Manski bounds for honesty + SFA point estimate (Aigner-Lovell-Schmidt 1977, Battese-Coelli 1995) + Conformalized QR interval (Romano et al. 2019).
3. **Data forensics**: B/S/G pipeline, rejected records (480 coord + 9606 txn), reusable DQ checks.
4. **POI acquisition**: Geofabrik PBF + pyrosm pipeline; honest LK coverage caveats.
5. **Feature engineering**: outlet structural + historical + LK-domain (Avurudu, Poya, distributor depot distance) + POI catchment + cannibalisation.
6. **Latent potential method**: lower_bound + (SFA + q90) frontier with constraint-score weighting + size-bucket bootstrap caps.
7. **Validation without ground truth**: residual diagnostics, monotonicity checks, Manski-band sanity, peer-frontier reasonableness, top-uplift manual audit.
8. **GenAI transparency**: per-phase log + critical-evaluation principles.

---

**Next step:** the AI Council (4 critics) will now audit the team's *current* methodology against this brief and produce a hit-list. Output to `competition/Reviews/`.
