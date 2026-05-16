# EDA Specialist -- Council Round 4 (v4 review)

**Notebook:** `Notebooks/23_v2_eda.ipynb` (12 new cells, A--J).
**Charts:** all PNGs saved to `Reports/figures/eda_*.png`.
**Data probed:** silver transactions (2.37M rows), gold features (20k outlets), predictions_v2, quantile_predictions_v2, POI features, outlet master + coordinates.

---

# TL;DR

- **The "censoring" story is small.** Only **232 / 20 000 outlets (1.16 %)** show a real plateau fingerprint (>=3 months at >=95 % of personal max **and** a plateau >=2 months in a row). The whole frontier-uplift machinery is being asked to do work for a tiny minority (`eda_censoring_fingerprint.png`).
- **V3b's "27.92 % below historical max" comes straight from the data.** In `predictions_v2` the same arithmetic gap (`frontier_q90 < observed_max`) still affects **3 124 outlets (15.62 %)**, and **32.24 %** of *Extra Large* outlets. Any version that ships `frontier_q90` as the prediction without a `max(., observed_max)` floor inherits that bias (`eda_frontier_gap.png`).
- **V4's "median uplift = 1.0" is structural, not a bug.** `constraint_score` is tightly bell-shaped around 0.50 (sd 0.128). 55.32 % of outlets land at `uplift_ratio == 1.0`, **including 9.75 % of the top constraint decile** (`eda_constraint_uplift.png`). The mapping from constraint to uplift collapses the middle of the distribution to a no-op.

---

# 10 Key Findings

1. **Censoring is rare and concentrated.** 1.16 % of outlets are "likely censored". Skew is by size: Extra Large 4.45 %, Large 1.56 %, Medium 1.02 %, Small 0.81 %. Plateau lengths are short -- the median outlet's longest near-max run is **1 month**. Reference: `eda_censoring_fingerprint.png`.

2. **Two distributors have outsized censoring rates.** `DIST_S_01` (3.32 %) and `DIST_S_02` (4.01 %) -- both Southern -- run ~5x the censoring rate of the next worst (~0.85 %). `DIST_W_02` is an outlier on the *opposite* side: median outlet volume **104.9 L** vs **55--62 L** for every other distributor. So DIST_W_02 serves bigger customers, the Southern duo squeezes smaller ones. Reference: `eda_distributor_volume.png`.

3. **Cooler-count saturation knee is at 3.** Median monthly volume jumps 0->1: +44.5 %, 1->2: +133.7 %, 2->3: +291 %, then **3->4: 0.0 %, 4->5: 0.0 %**. Outlets with 3, 4, or 5 coolers all sit at ~566 L median. Cooler counts above 3 are decorative -- they don't predict more volume. Reference: `eda_cooler_saturation.png`.

4. **POI catchment doesn't help any outlet type.** Per-type Pearson r between `poi_catchment_score` and `observed_mean_monthly_liters`: Bakery -0.021, Eatery -0.007, Grocery 0.001, Hotel 0.000, Kiosk 0.008, Pharmacy -0.026, SMMT -0.016. **All effectively zero**, two are negative. The POI scoring as engineered carries near-zero predictive signal for outlet volume. Reference: `eda_poi_outlet_type.png`.

5. **Year-on-year January is bimodal in stability.** Of the 5 871 outlets observed in all three Januaries, **34.9 %** have CV < 0.20 (stable) but **33.6 %** have CV > 0.50 (volatile). Median Jan growth 2023->2024 = **1.0006**, 2024->2025 = **1.0000** -- there is no organic growth trend, so a naive lag-1 prediction is unbiased on average but blind to the volatile third. Reference: `eda_yoy_stability.png`.

6. **Most outlets have <3 Januaries.** Only **5 871 / 20 000** outlets have January observed in all three years; **14 129** are entered the panel later or are missing data. Any model relying on January history must handle a sparse, ragged panel, not a clean 3-year stack.

7. **Avurudu and December tourism are real but province-specific.** Normalised heatmap shows December lift over region mean: W +0.43, NW +0.36, S +0.32, C +0.31. April: W +0.43, NW +0.35, S +0.31, C +0.29. Peak month: **W = April, C = December, NW = December, S = February**. The Western province responds most to Avurudu; Southern peaks in February (post-NY tourism, not December). Reference: `eda_province_seasonality.png`.

8. **Top-100 uplift outlets pass a sanity check.** Median `constraint_score` 0.623 vs population 0.467. Median `observed_max` **87 L vs 164 L** -- they are smaller-than-typical outlets, exactly the "headroom is large in % terms" cohort you'd expect. **11 %** of the top-100 are "likely censored" (vs 1.16 % population) -- a 9.5x enrichment. SMMT (27 of 100) and Kiosk (14) are over-represented. The list is defensible. Reference: `eda_top100_sanity.png`.

9. **frontier_q90 < observed_max for 15.62 % of outlets**, and it's the largest outlets that are most affected: 32.24 % of Extra Large vs 10.50 % of Large. The frontier estimator is biased low for the volume-heavy tail. **1 803 outlets** have a gap worse than -5 %, **227** worse than -25 %. Only **10** are "double-bad" (gap < 0 *and* likely censored), so the remaining 3 114 with negative gaps are mostly *not* censored -- they are simply outlets the frontier model under-prices. Reference: `eda_frontier_gap.png`.

10. **Manski band is wide and the prediction lives mostly in the middle, but pinned at the upper edge in 6 % of cases.** Of 20 000 outlets: 79.9 % middle, 13.0 % upper quarter, 6.3 % *at* the upper bound, 0.8 % lower quarter, 0 at the lower bound. Median band width = **90.4 L**, ~55 % of the median Maximum (164.3 L) -- bands are wide, so there is room to interpolate, but **1 262 outlets** are pegged at the ceiling and **0** at the floor, indicating an asymmetric clipping. Reference: `eda_manski_band.png`.

---

# Root cause of V3b

V3b shipped `Maximum = frontier_q90`. The data shows:

- In `predictions_v2`, **3 124 outlets (15.62 %) have `frontier_q90` < `observed_max`**. In V3b's predecessor (without the post-hoc `max(., observed_max)` floor) that same arithmetic gap is what produced the **27.92 %** "below historical max" failure.
- The bias is **size-skewed**: 32.24 % of Extra Large, 16.85 % of Medium, 14.92 % of Small. The frontier estimator under-prices the long-volume tail because it pools peer outlets (POI/coords-based neighborhoods) where most peers are smaller.
- It is **not** primarily a censoring artefact: only 10 of 3 124 affected outlets are "likely censored". The fix is therefore not "lift the frontier higher for censored outlets"; the fix is `Maximum := max(frontier_q90, observed_max)` as a hard floor, applied universally. v2 already does this -- the 0 of 20 000 with `Maximum < observed_max` confirms it.

**One-line root cause:** `frontier_q90` is a peer-pooled estimator with downward bias for the largest outlets; without an `observed_max` floor it under-predicts on ~16 % of the panel and ~32 % of Extra Large.

**Reference chart:** `eda_frontier_gap.png`.

---

# Root cause of V4

V4 ships `Maximum = observed_max * uplift_ratio` and the median `uplift_ratio` lands at **exactly 1.0**. The data tells us why:

- `constraint_score` is tightly distributed: mean 0.501, sd 0.128, range 0.077--0.984. The middle 50 % of outlets sit between 0.425 and 0.573 -- a **15-point band that the uplift formula treats as "no signal"**.
- Decile-by-decile uplift response (Spearman r = 0.479, Pearson 0.346):

  | constraint decile | mean uplift | median uplift | % at uplift==1.0 |
  |---|---|---|---|
  | 0 (low constraint)  | 1.000 | 1.000 | 99.55 % |
  | 4--5 (middle) | 1.071 / 1.077 | 1.036 / 1.002 | 40.75 / 49.60 % |
  | 9 (high constraint) | 1.103 | 1.078 | 9.75 % |

  Even in the **top decile of constraint_score, 9.75 % of outlets get zero uplift**, and the mean uplift is only 1.103. The mapping from constraint to uplift is too conservative everywhere except the very top.
- 55.32 % of all outlets get uplift_ratio == 1.0. Once that majority sits at 1.0, the **median is mathematically forced to 1.0** regardless of the formula's slope on the tails.

**One-line root cause:** the constraint-to-uplift mapping is dead on the middle two-thirds of the constraint_score distribution, so most of the panel inherits no uplift and the median collapses.

**Reference charts:** `eda_constraint_uplift.png`, `eda_manski_band.png`.

**Concrete fixes:**
1. Re-scale `constraint_score` to a percentile within Outlet_Type x Outlet_Size before mapping to uplift, so the middle of each bucket is no longer a flat zone.
2. Apply uplift to *every* outlet whose `months_near_max >= 1` instead of only those above a constraint threshold (the censoring fingerprint, even weak, beats a global cutoff).
3. Sanity-cap uplift at the bucket-level `cap_uplift` (already in `cap_table_v2.csv`) -- 1.69--6.0x by Type x Size -- but stop emitting uplift_ratio = 1.0 for high-constraint outlets.

---

# 5 Insights for the 5-page PDF report

1. **"Cooler count saturates at 3."** Beyond 3 coolers, median outlet volume is flat (566 L). Recommend: *don't* use `cooler_count` as a continuous feature above 3; use `min(cooler_count, 3)` and let outlet_type/size carry the rest.

2. **"POI features as engineered carry no signal for any outlet type."** All 7 per-type Pearson r values fall in [-0.026, 0.008]. Either re-engineer POI (try category counts at 250/500m only, or competitor density), or drop POI from the predictive stack and keep only `cannibalisation_count_200m` from features.

3. **"Two Southern distributors are constraint hotspots."** `DIST_S_01` (3.32 %) and `DIST_S_02` (4.01 %) censoring rates are 5x the rest. The biggest concrete commercial action is to investigate supply allocation to `DIST_S_*`, not to chase a model fix.

4. **"April Avurudu lift is real and Western-province-led (+43 % vs region mean), December tourism is universal (+31 to +43 %), Southern peaks in February."** This grounds the "seasonality is real" claim with a concrete normalised heatmap rather than aggregate seasonality indices.

5. **"V3b vs V4 are opposite failure modes from the same data weakness."** V3b *under*-predicts because `frontier_q90 < observed_max` for 15.62 % of outlets (no floor). V4 *under*-uplifts because the constraint_score mapping is flat on the middle two-thirds. Both fixes are mechanical (apply `max(., observed_max)` and percentile-rescale `constraint_score`); neither needs a model rebuild.

---

# Notebook 23 cell index

(Indices below match the `EditNotebook` write order.)

| Cell | Type | Topic |
|---|---|---|
| 0 | md | (existing) Title and purpose |
| 1 | py | **Setup** -- imports, paths, load all 9 dataframes, build `monthly` and `Region` |
| 2 | md | A. Censoring fingerprint -- intro |
| 3 | py | A. Per-outlet near-max counter + plateau detector + size/type breakdown -> `eda_censoring_fingerprint.png` |
| 4 | md | B. Distributor effects -- intro |
| 5 | py | B. Per-outlet mean volume by distributor + censoring rate by distributor -> `eda_distributor_volume.png` |
| 6 | md | C. Cooler saturation -- intro |
| 7 | py | C. Cooler-count curve, knee detector via relative deltas -> `eda_cooler_saturation.png` |
| 8 | md | D. POI x Outlet_Type -- intro |
| 9 | py | D. Per-type slope + best POI category per type -> `eda_poi_outlet_type.png` |
| 10 | md | E. YoY stability -- intro |
| 11 | py | E. Jan 2023/24/25 CV per outlet, growth ratios -> `eda_yoy_stability.png` |
| 12 | md | F. Province x month seasonality -- intro |
| 13 | py | F. Region x month heatmap normalised within region -> `eda_province_seasonality.png` |
| 14 | md | G. Top-100 uplift sanity -- intro |
| 15 | py | G. Top-100 vs population medians, censoring enrichment -> `eda_top100_sanity.png` |
| 16 | md | H. frontier_q90 vs observed_max -- intro |
| 17 | py | H. Gap distribution + size/type breakdowns + double-bad count -> `eda_frontier_gap.png` |
| 18 | md | I. constraint_score vs uplift -- intro |
| 19 | py | I. Pearson/Spearman, decile uplift table, top-decile uplift==1 share -> `eda_constraint_uplift.png` |
| 20 | md | J. Manski band coverage -- intro |
| 21 | py | J. Position of Maximum within [lower, upper], width vs Maximum -> `eda_manski_band.png` |
| 22 | md | Summary linking findings to V3b / V4 |

All numbers in this review come from a parallel run of the same code on the same parquet files; executing the notebook should reproduce them exactly (small float drift only).
