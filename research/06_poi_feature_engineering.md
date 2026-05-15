# 06 — POI Feature Engineering for Outlet Catchment

Research channel **6 of 10** for Data Storm 7.0 (Sri Lanka, 20,000 beverage retail outlets, January 2026 latent potential).

---

# TL;DR

- **Keep the team's BallTree-haversine spine. Bolt POI counts on top using the same tree, multiplied by a Gaussian decay (σ ≈ 750 m urban, 2,000 m rural).** Raw counts at 250 m / 500 m / 1 km / 2 km / 5 km plus one decay-weighted score per category beats either alone in retail catchment literature.
- **For 20k outlets in 4 provinces, a full Huff model is overkill. Use a one-shot 2SFCA-style accessibility score per POI category instead, and treat same-type / same-distributor counts as **cannibalization** rather than catchment.** Reilly/Converse breaking points are useful for sanity checks, not features.
- **The 240 invalid-coordinate rows are not "fix and predict" — they are predict-from-non-spatial-features only.** Build a parallel feature set so the geo branch never silently imputes them with the median (current notebook leaks median lat/lon into the model).

---

# Methodology Survey

## 1. Multi-radius counts — which radii and why

Retail-catchment work consistently uses **concentric "primary / secondary / tertiary" rings**, mapping roughly to 70 / 20 / 10 % of customers for convenience retail (RadiusMapper / Atlas trade-area guides). For *traditional trade* (kades, kiosks, pharmacies, eateries) the customer is almost always a pedestrian or a 2-wheeler trip, so urban-planning literature on convenience stores points at much smaller rings than the team's current 1/2/5 km spine.

Recommended radii **for this competition**:

| Ring | Use | Why |
| --- | --- | --- |
| **250 m** | Walk-in catchment for kiosk / grocery / pharmacy / bakery | ~3 min walk; the dominant trip mode for traditional trade. Missing today. |
| **500 m** | Local micro-market (eatery, hotel, SMMT) | ~6 min walk or 2 min tuk-tuk. Bridges 250 m and 1 km cleanly. |
| **1 km** | Already in pipeline (`outlet_count_1km`) | Standard "neighborhood" ring; also used by Google Places Insights. |
| **2 km** | Already in pipeline (`outlet_count_2km`, `same_type_count_2km`) | Approximates a tuk-tuk / motorbike trip. Good for SMMT / hotel pull. |
| **5 km** | Already in pipeline (`outlet_count_5km`, `same_distributor_count_5km`) | Captures distributor route geography, not consumer demand. Keep, but downweight. |

**Drop nothing**, but add 250 m and 500 m for *every POI category* you scrape. The marginal cost is one extra `tree.query_radius` call per radius (BallTree handles it in milliseconds for 20k points).

> Source: RadiusMapper *Catchment Area Analysis Guide*; Atlas *Draw 1 km Retail Catchment Areas*; QGIS Trade-Area chapter (gis4urbplan).

## 2. Distance-decay weighting

Four candidate forms:

| Form | Equation | When it wins | Notes |
| --- | --- | --- | --- |
| **Linear** | `w = max(0, 1 − d/R)` | Almost never. | Sharp cutoff hides tail. |
| **Power** | `w = d^(−β)` | Long tails, classical Reilly / Huff | β ∈ [1, 2] is the literature range; **β=2** is the original gravity exponent. Singular at d=0 — needs `d + ε` floor. |
| **Negative exponential** | `w = exp(−λ d)` | Within-city work | Used in ArcGIS Huff, retail micro-markets. |
| **Gaussian** | `w = exp(−d² / (2σ²))` | Pedestrian / walking catchments | Smooth, symmetric, no singularity. Used by aceso, Enhanced 2SFCA. **Recommended default here.** |

**Empirical anchor.** Shanghai commercial centres study (Power vs Exponential, 2024): both fit (R² > 0.6), power slightly better (~+0.05 R²) but not significant; β coefficient between 1 and 2; **smaller commercial centres → larger β** (faster decay). arxiv 1503.02915 also concludes power is theoretically grounded but exponential is fine inside cities.

**Recommended defaults for Sri Lanka traditional trade**:

```python
# Gaussian decay: w = exp(-d^2 / (2 * sigma^2))
SIGMA_URBAN = 0.75    # km — Western province, Colombo / Gampaha (>1,500 ppl/km²)
SIGMA_RURAL = 2.00    # km — North-Western, Central interior, Southern hinterland
SIGMA_MIXED = 1.25    # km — fallback when urban/rural label is uncertain
```

Justification: Western Province sits at **~1,615–1,731 ppl/km²** (2021 census), making 1 km already a multi-block footprint. Rural Central / NW district densities sit an order of magnitude lower, so a 2 km σ is needed before the decay weight collapses below 0.1.

**Urban/rural label** can be derived cheaply from `outlet_count_1km` itself: an outlet with > 30 neighbouring outlets in 1 km is effectively urban. No external dataset required.

## 3. Huff probabilistic catchment — worth it here?

Classical Huff: probability that consumer at origin `i` chooses store `j` is

`P_ij = (A_j / d_ij^β) / Σ_k (A_k / d_ik^β)`

where `A_j` is store attractivity (size, brand, SKU breadth).

**Use case in this comp.** Useful only if you have **demand origins** (e.g. residential population grid cells from WorldPop or HDX). Without origins you cannot compute `P_ij`.

**Verdict.** **Skip pure Huff for the 36-hour window.** Use the public `huff` Python package (`pip install huff`, paper arXiv:2602.17640) only if you have time to ingest a 1 km population raster. Instead implement a **2SFCA-style score** (Section 4) which is a one-pass simplification that works without explicit origins by treating every outlet as both demand and supply.

If you do go Huff: code skeleton —

```python
# huff_proxy.py — simplified Huff with no separate origins
import numpy as np
from sklearn.neighbors import BallTree

def huff_capture(outlets, attractivity, sigma_km=1.0):
    coords = np.radians(outlets[['Latitude', 'Longitude']].to_numpy())
    tree = BallTree(coords, metric='haversine')
    EARTH = 6371.0
    R = 5.0  # km cutoff
    ind, dist_rad = tree.query_radius(coords, r=R / EARTH, return_distance=True)
    capture = np.zeros(len(outlets))
    for i, (js, ds) in enumerate(zip(ind, dist_rad)):
        d_km = ds * EARTH
        w = np.exp(-(d_km ** 2) / (2 * sigma_km ** 2)) * attractivity[js]
        # exclude self from denominator AND numerator
        mask = js != i
        denom = w[mask].sum() + 1e-9
        capture[i] = attractivity[i] / denom  # share of local attractivity I capture
    return capture
```

`attractivity` for this comp = `Cooler_Count + 1` (or rank-based, like the existing `Outlet_Size_Score`).

## 4. Gravity / spatial-interaction models (Reilly, Converse)

**Reilly's Law (1931).** Indifference distance from town A toward town B: `d_A = D / (1 + sqrt(P_B / P_A))`. **Use as a feature only when you have town/city centroids with population.** Otherwise meaningless.

**Converse breaking point (1949).** Same idea, distance to indifference point. R has it as `REAT::converse(P_a, P_b, D_ab)`. No mainstream Python port — tiny function, easy to translate:

```python
def converse_breaking_point(P_a, P_b, D_ab):
    """Returns distance from A to the indifference point with B."""
    return D_ab / (1.0 + (P_b / P_a) ** 0.5)
```

**Practical use in this comp.** Take the 2SFCA accessibility score (below) over the 9 OSM POI categories — it subsumes Reilly/Converse for non-anchor retail.

**2SFCA (preferred).** Two-step floating catchment area (Luo & Wang 2003, generalized in `aceso` and `pysal/access`):

1. For every supply POI `j`, compute `R_j = S_j / Σ_i (D_i · w(d_ij))` over demand points within radius.
2. For every demand point `i`, compute `A_i = Σ_j R_j · w(d_ij)` over supply within radius.

For our problem the "demand" is the residential pull around an outlet (proxied by population raster or by other-outlet density) and "supply" is the POI category (school, hospital, bus_station). The `aceso` package (`pip install aceso`, numpy-only) implements gaussian / cosine / uniform decays out of the box.

## 5. K-nearest features

Beyond `nearest_outlet_distance_km`, add **k-th nearest distances** for every POI category, with k ∈ {1, 3, 5}:

```python
dist, _ = tree.query(coords_rad, k=5)
nearest_school_km   = dist[:, 0] * EARTH  # k=1
third_nearest_school_km = dist[:, 2] * EARTH
fifth_nearest_school_km = dist[:, 4] * EARTH
```

**Why k>1.** Single-nearest is brittle to coordinate noise (a single mis-geocoded school flips the value by km). **k=3 or k=5 averages out noise** — KNN-under-perturbation literature shows accuracy degrades only ~20 % even at high noise when k is moderate (Xing 2021 *Predictive Power of Nearest Neighbors under Random Perturbation*).

**Robustness rule of thumb.** Use **median of top-3** distances rather than min-1 whenever the POI source is OSM crowd data (which has ~50 m typical jitter).

## 6. Density vs raw count normalization

Raw count and density are not interchangeable. Pick by **what the model needs**:

| Form | When it wins |
| --- | --- |
| Raw count `N` in radius `R` | Tree-based models (HistGB, LGBM, XGB) — they handle non-linear monotonic transforms internally. The team's HistGradientBoostingRegressor benefits from raw counts. |
| Density `N / (π R²)` | Linear models, SHAP interpretation, cross-radius comparison ("3 schools per km² is dense regardless of which ring") |
| Log1p of count | When you mix urban (count > 100) and rural (count = 0) — current pipeline should `np.log1p` the existing `outlet_count_*` features for any model that isn't a tree. |

**Recommendation for this comp.** Keep raw counts for the HGB model. **Add a parallel `density_per_km2` column for every count** — costs nothing and helps the composite score. Also add `log1p_outlet_count_*` for the linear constraint-score blend.

## 7. Composite "catchment demand score"

The current `catchment_density_score` is a **percent-rank weighted sum** with hard-coded weights 0.35 / 0.25 / 0.20 / 0.10 / 0.10. That's a reasonable ad-hoc default but it has issues:

1. All weights pre-set without empirical anchor.
2. Same-type count is **competition / cannibalization**, not demand. Including it positively is wrong.
3. No POI categories yet.

**Recommended replacement**:

```python
# Step 1 — per-category demand scores using Gaussian decay
def decay_weighted_count(tree_target, outlet_coords_rad, sigma_km, R_km=5.0):
    EARTH = 6371.0
    ind, dist_rad = tree_target.query_radius(
        outlet_coords_rad, r=R_km / EARTH, return_distance=True)
    out = np.zeros(len(outlet_coords_rad))
    for i, (js, ds) in enumerate(zip(ind, dist_rad)):
        d_km = ds * EARTH
        out[i] = np.exp(-(d_km ** 2) / (2 * sigma_km ** 2)).sum()
    return out

# Step 2 — robust scaling per category (RobustScaler beats StandardScaler
# because outlet density is heavy-tailed)
from sklearn.preprocessing import RobustScaler
cat_scores = RobustScaler().fit_transform(np.column_stack([
    decay_weighted_count(school_tree,   coords_rad, SIGMA_URBAN),
    decay_weighted_count(hospital_tree, coords_rad, SIGMA_URBAN),
    decay_weighted_count(bus_tree,      coords_rad, SIGMA_URBAN),
    decay_weighted_count(market_tree,   coords_rad, SIGMA_URBAN),
    decay_weighted_count(office_tree,   coords_rad, SIGMA_URBAN),
    decay_weighted_count(eatery_tree,   coords_rad, SIGMA_URBAN),
    decay_weighted_count(religious_tree,coords_rad, SIGMA_URBAN),
    decay_weighted_count(hotel_tree,    coords_rad, SIGMA_URBAN),
    decay_weighted_count(supermarket_tree, coords_rad, SIGMA_URBAN),
]))

# Step 3 — category weights from business intuition,
# overridable by a quick correlation pass against observed_max_monthly_liters
W = np.array([0.18, 0.10, 0.18, 0.12, 0.10, 0.12, 0.08, 0.07, 0.05])
poi_demand_score = (cat_scores * W).sum(axis=1)
```

**Weight rationale.** Schools and bus stops are the strongest footfall drivers in Sri Lanka traditional-trade context (school finish + commute = beverage purchase peaks). Supermarkets get a small **negative** twin (see cannibalization in §9).

## 8. Co-location features (interaction terms)

Single counts under-estimate footfall when **multiple anchor categories overlap**. Three high-value interactions worth adding:

| Feature | Definition | Why |
| --- | --- | --- |
| `transit_school_synergy` | `1` if `nearest_bus_stop_km < 0.2` AND `nearest_school_km < 0.5` | Captures the "after-school stall" pattern |
| `office_eatery_cluster` | `office_count_500m * eatery_count_500m` | Lunchtime corridor; multiplicative not additive |
| `religious_market_corridor` | `1` if both within 500 m | Weekend / poya day footfall |
| `triple_anchor_500m` | sum of indicators across {school, bus, market} > 1 | Generic multi-anchor density boost |

CARTO's *Spatial Scoring* and Google Places Insights both note that **POI co-location terms outperform single-category counts** for site-selection ML.

## 9. Cannibalization features

Current pipeline counts `same_type_outlet_count_2km` as **positive** input to `catchment_density_score`. **This is backwards** — same-type peers within 500 m steal share.

Fix:

| Feature | Sign | Logic |
| --- | --- | --- |
| `n_same_type_500m` | **negative** | Direct competitor density |
| `n_same_type_1km` | **negative, weaker** | Indirect competitor density |
| `n_supermarket_500m` | **strong negative** | Modern trade cannibalizes traditional trade volume |
| `n_same_distributor_2km` | **near-zero** | Distributor route density — neutral, **already misnamed as catchment** |
| `share_of_local_coolers` | **positive** | `Cooler_Count_self / (Cooler_Count_self + Σ neighbour Cooler_Count within 500 m)` — captures relative dominance |

Empirical anchor: Targomo cannibalization study and aicrelabs *Retail Gravity Equation* report S-curve clustering — coffee shops *gain* up to a point, but **grocery stores are nearly always harmed by over-clustering**. SMMT and supermarket categories should always carry a negative coefficient in this model.

## 10. Library recommendations

| Library | Use | Trade-off |
| --- | --- | --- |
| `scikit-learn BallTree(metric='haversine')` | Already in pipeline. Stay with it. | O(n log n) builds in <1s for 20 k outlets; **must pass radians, never degrees**; convert results by × 6371 km. |
| `geopandas` | Vector ops, joins, GeoJSON I/O for OSM exports | 4× slower than raw numpy for nearest-neighbour but mandatory for spatial joins. |
| `shapely` | Buffer geometry for area-based density | Use `geom.buffer(R / 111.32 / 1000)` only for cartography, not for distance — projects to flat earth. |
| `pyrosm` | Parse the **HDX OSM Sri Lanka PBF** offline | Cython-fast (2-4× pyrobuf). Needed because Overpass API will rate-limit a 20 k-outlet scrape. |
| `osmnx` | Backup for live Overpass queries with retry logic | Slower but easier; cap to ≤100 outlets per call to avoid 429s. |
| `H3 (uber/h3-py)` | Hex-bin counts (resolution 8 ≈ 460 m edge, resolution 9 ≈ 174 m edge) | Excellent for **groupby aggregation** of POIs. Good complement to BallTree but not a replacement — use H3 for "POIs per hex" features and BallTree for distance-based features. Resolution 8 is the right grain for SL traditional trade. |
| `aceso` | 2SFCA / gravity scores | Numpy-only, no GIS dependency. Best path to a defensible accessibility number quickly. |
| `huff` | Full Huff / MCI calibration | Use only if there's >6 hours and a population raster. |
| `pysal/access` | Production-grade 2SFCA | Heavier; use only if `aceso` does not have your variant. |

## 11. Avoiding leakage

Three concrete rules:

1. **Self-exclusion in counts.** The current notebook subtracts 1 from `tree.query_radius(..., count_only=True)` — correct. Keep that pattern for every POI tree where the outlet itself is in the index. For external POI trees (schools, hospitals), `−1` is wrong since the outlet is not in those trees.
2. **No target encoding by neighbour group.** Tempting to compute "mean observed liters of outlets within 1 km" — that **leaks the target through neighbours**. If you must, compute it out-of-fold using `KFold(shuffle=True)` per outlet group, then drop self.
3. **Spatial cross-validation.** Standard `KFold` will put neighbouring outlets in train and test. For honest validation use **`GroupKFold` keyed on a coarse grid** (e.g. H3 resolution 5 ≈ 8.5 km hex) so a hex is entirely train or entirely held-out. This is documented in Ledesma 2023 *Spatial Cross-Validation Using scikit-learn*.

## 12. Handling the 240 invalid coordinates

Current notebook silently does:

```python
features['Latitude']  = features['Latitude'].fillna(features['Latitude'].median())
features['Longitude'] = features['Longitude'].fillna(features['Longitude'].median())
```

**This is a leakage / drift bug.** It teleports 240 outlets to the geographic median (somewhere in Central province) and then computes catchment from there. They will look identical to each other and very dense.

**Fix in three lines**:

```python
features['has_valid_coordinates'] = features['Outlet_ID'].isin(valid_geo['Outlet_ID'])
# Compute every spatial feature ONLY on has_valid_coordinates == True
# For invalid rows, set spatial features to np.nan (HistGB handles NaN natively)
# OR fall back to distributor-level median feature value, NOT median lat/lon
```

Better: **distributor-level imputation**. For each `Distributor_ID`, take the median value of every spatial feature across that distributor's valid outlets, and use that as the imputed value for invalid-coord outlets in the same distributor. This preserves regional structure.

Even better: drop invalid-coord outlets from the spatial feature path entirely and rely on the existing `Outlet_Size`, `Outlet_Type`, `Cooler_Count`, distributor seasonality, and SKU breadth features. The judging rubric explicitly rewards quarantining bad records — make this visible.

---

# Concrete Feature Pipeline for THIS Comp

Build order: each row's "Priority" column is **P0 (must ship before submission)**, **P1 (ship if 6 + hours left)**, **P2 (nice to have)**.

| Feature | Formula | Library | Priority |
| --- | --- | --- | --- |
| `outlet_count_250m`, `..._500m` | `tree.query_radius(R, count_only=True) - 1` | sklearn `BallTree` | P0 |
| `density_outlet_per_km2_{250m,500m,1km,2km}` | `count / (π R²)` | numpy | P0 |
| `nearest_school_km`, `..._hospital_km`, `..._bus_km`, `..._market_km`, `..._supermarket_km`, `..._office_km`, `..._religious_km`, `..._eatery_km`, `..._hotel_km` | `BallTree.query(k=1)` per category from OSM Overpass / pyrosm | sklearn + pyrosm | P0 |
| `kth_nearest_school_km` (k=3, k=5) | `BallTree.query(k=5)[:, 2]` and `[:, 4]` | sklearn | P1 |
| `school_count_{250,500,1000,2000}m` (and same for hospital, bus, market, supermarket, office, religious, eatery, hotel) | `tree.query_radius` per category | sklearn | P0 |
| `school_decay_score` (and per category) | `Σ exp(-d² / (2σ²))` over POIs in 5 km, σ from urban/rural label | numpy | P0 |
| `urban_rural_label` | `1 if outlet_count_1km > 30 else 0` | numpy | P0 |
| `poi_demand_score` | `Σ_c W_c · RobustScaler(category_decay_score)_c` | sklearn `RobustScaler` | P0 |
| `huff_capture_share` | simplified Huff with `Cooler_Count + 1` as attractivity | numpy + sklearn `BallTree` | P1 |
| `n_same_type_500m`, `..._1km` | `BallTree` per outlet type | sklearn | P0 |
| `n_supermarket_500m` | from POI tree (negative cannibalization) | sklearn | P0 |
| `share_of_local_coolers` | `Cooler_self / (Cooler_self + Σ Cooler_neighbours_500m)` | numpy | P1 |
| `transit_school_synergy` | `(nearest_bus_km < 0.2) & (nearest_school_km < 0.5)` | numpy | P1 |
| `office_eatery_cluster` | `office_count_500m * eatery_count_500m` | numpy | P1 |
| `triple_anchor_500m` | `(school_count_500m > 0) + (bus_count_500m > 0) + (market_count_500m > 0) >= 2` | numpy | P1 |
| `h3_res8_cell`, `h3_res9_cell` | `h3.latlng_to_cell(lat, lng, res)` | uber `h3` | P1 (target-encoded out-of-fold) |
| `accessibility_2sfca_score` | `aceso.GravityModel(decay='gaussian').calculate_accessibility(...)` over composite POI weights | `aceso` | P1 |
| `has_valid_coordinates` (already in pipeline) | bool flag | pandas | P0 (must remain in feature list as documented signal) |
| `spatial_features_imputed_flag` | True for the 240 invalid-coord outlets | pandas | P0 |
| `density_road_intersections_500m` | OSM highway nodes via pyrosm | pyrosm | P2 |
| `population_within_1km_worldpop` | sum WorldPop 100 m raster within 1 km | rasterio | P2 |

**Implementation ordering tip.** The team's existing `BallTree` cell can be refactored into a single function `build_features_for(category_coords_rad, outlet_coords_rad, radii_km, sigma_km)` and called 9 times — once per POI category — without rewriting the spine.

---

# Pitfalls to Avoid

1. **Median-imputing lat/lon.** Current notebook does this; it gives 240 outlets identical fake catchment. Switch to NaN + tree-model native handling, or distributor-median imputation of derived features.
2. **Same-type peer count counted as positive demand.** Current `catchment_density_score` adds `same_type_outlet_count_2km` with positive weight. It is competition, not demand. Flip the sign or move it to a separate `cannibalization_score`.
3. **Forgetting `radians()` before BallTree.** Haversine in sklearn requires radians; mixing degrees gives wildly wrong distances.
4. **Forgetting to multiply by Earth radius.** `tree.query` returns radians; `dist_km = dist_rad * 6371.0`.
5. **Self-counted outlet.** When the outlet itself is in the tree, always subtract 1. When using an *external* POI tree, do NOT subtract 1.
6. **Using `geom.buffer(R)` on lon/lat geometries** without re-projecting. A 1 km buffer in degrees becomes a kilometre at the equator and ~110 m at the poles. For SL it's close to right but still ~0.5 % off — use BallTree distance, not buffer area, for catchment counts.
7. **Standard KFold validation.** Spatial autocorrelation will inflate validation R² by 10-30 % vs honest spatial CV. Use H3-grouped folds.
8. **Hard-coded β/σ across the country.** Western Province at >1,500 ppl/km² and rural Central interior at <100 ppl/km² need different decay parameters. Switch on `urban_rural_label`.
9. **Overpass rate-limiting.** A 20 k-outlet scrape via Overpass will hit `429 Too Many Requests`. Download the **HDX OSM Sri Lanka PBF** once and parse offline with pyrosm.
10. **POI duplicates from polygon + node.** OSM tags amenities both as nodes and as building polygons. Dedupe on `(name, rounded lat 4 dp, rounded lon 4 dp)` before counting.
11. **Mixing CRS.** Stay in EPSG:4326 (WGS84) for everything spatial. Reproject to EPSG:5234 (Sri Lanka grid) only if you need true area in m².
12. **Leakage via target-encoded H3 cells.** Tempting to encode H3 cell with mean observed liters. Compute *out-of-fold* only.

---

# References

**Catchment / trade area**

- RadiusMapper. *Catchment Area Analysis: The Complete Guide* — https://radiusmapper.com/blog/catchment-area-analysis-complete-guide
- Atlas. *Draw 1 km Retail Catchment Areas and Compare Parcels* — https://atlas.co/blog/draw-1-km-retail-catchment-areas-and-compare-parcels/
- QGIS for Urban Planning, Ch.6 *Trade Area Analysis* — https://gis4urbplan.netlify.app/hands-on_ex05

**Distance decay / gravity**

- Chen Y. (2015). *The Distance-Decay Function of Geographical Gravity Model.* arXiv:1503.02915 — https://arxiv.org/pdf/1503.02915
- *Spatial Decay of Patronizing Behavior in Trade Areas: Power Law or Exponential Law* — http://geoscien.neigae.ac.cn/EN/abstract/article/1000-0690/49609
- ArcGIS. *How Original Huff Model works* — https://desktop.arcgis.com/en/arcmap/latest/tools/business-analyst-toolbox/how-original-huff-model-works.htm
- Wikipedia. *Reilly's law of retail gravitation* — https://en.wikipedia.org/wiki/Reilly's_law_of_retail_gravitation
- REAT R package — *Converse / Reilly* functions — https://search.r-project.org/CRAN/refmans/REAT/html/converse.html

**Huff & 2SFCA Python implementations**

- Wieland T. (2026). *huff: A Python package for Market Area Analysis.* arXiv:2602.17640 — https://www.arxiv.org/pdf/2602.17640
- huff package on PyPI — https://pypi.org/project/huff/
- aceso (lightweight 2SFCA) — https://github.com/tetraptych/aceso, docs at https://aceso.readthedocs.io/en/latest/api/
- PySAL `access.fca.two_stage_fca` — https://pysal.org/access/generated/access.fca.two_stage_fca.html

**Co-location & cannibalization**

- Google Maps Platform. *Analyze Site Performance with Places Insights and BigQuery ML* — https://developers.google.com/maps/architecture/places-insights-analyze-site-performance-ml
- CARTO. *Spatial Scoring: Measuring merchant attractiveness and performance* — https://academy.carto.com/creating-workflows/step-by-step-tutorials/spatial-scoring-measuring-merchant-attractiveness-and-performance
- aicrelabs. *The Retail Gravity Equation: How Close Is Too Close to Competitors?* — https://aicrelabs.com/research/retail-gravity-equation
- Targomo. *Cannibalization Analysis for Retail Networks* — https://targomo.com/introducing-cannibalization-analysis-examine-impact-competitors-network-branches-catchment-areas
- Pancras J. (2022). *Demand Expansion and Cannibalization Effects from Retail Store Entry.* Management Science — https://ideas.repec.org/a/inm/ormnsc/v68y2022i12p8829-8856.html

**KNN / robustness**

- Xing Z. et al. (2021). *Predictive Power of Nearest Neighbors Algorithm under Random Perturbation.* PMLR 130 — https://proceedings.mlr.press/v130/xing21a.html
- *A Machine Learning Approach Using Spatially Explicit K-Nearest Neighbors for House Price Predictions.* MDPI ISPRS IJGI 2026 — https://www.mdpi.com/2220-9964/15/1/46

**Libraries**

- scikit-learn `BallTree` — https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.BallTree.html
- scikit-learn `haversine_distances` — https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.haversine_distances.html
- Hanson C. *Using Scikit-learn's Binary Trees to Efficiently Find Lat/Long Neighbors* — https://coreyhanson.com/blog/using-scikit-learns-binary-trees-to-efficiently-find-latitude-and-longitude-neighbors/
- pyrosm benchmarks — https://pyrosm.readthedocs.io/en/stable/benchmarking.html
- pyrosm GitHub — https://github.com/pyrosm/pyrosm
- Uber H3 Python — https://github.com/uber/h3-py and https://uber.github.io/h3-py/intro.html
- Spatial Thoughts. *Fast Point-in-Polygon Analysis with GeoPandas and Uber's H3* — https://spatialthoughts.com/2020/07/01/point-in-polygon-h3-geopandas/

**Data sources for Sri Lanka POIs**

- HDX. *Sri Lanka Points of Interest (OpenStreetMap Export)* — https://data.humdata.org/dataset/hotosm_lka_points_of_interest
- HDX. *Sri Lanka Populated Places (OpenStreetMap Export)* — https://data.humdata.org/dataset/hotosm_lka_populated_places
- OSMtoday Sri Lanka layers — https://osmtoday.com/asia/sri_lanka.html
- OpenStreetMap Wiki *Key:amenity* — https://wiki.openstreetmap.org/wiki/Amenities

**Leakage / spatial CV**

- MetricGate. *Feature Engineering for Machine Learning* (target-encoding leakage) — https://metricgate.com/blogs/feature-engineering-for-machine-learning/
- Ledesma C. *Spatial Cross-Validation Using scikit-learn* — https://medium.com/data-science/spatial-cross-validation-using-scikit-learn-74cb8ffe0ab9
- Sp.4ML. *Feature Engineering with Spatial Flavour* — https://ml-gis-service.com/index.php/2021/03/19/data-science-feature-engineering-with-spatial-flavour/

**Sri Lanka context**

- Wikipedia. *Western Province, Sri Lanka* (population, density figures) — https://en.wikipedia.org/wiki/Western_Province,_Sri_Lanka
- WP Provincial Land Authority data — https://pla.chiefsec.wp.gov.lk/si/provincial-data/
