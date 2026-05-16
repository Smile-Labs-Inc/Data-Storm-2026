# EDA Specialist — Council Round 6

**Reviewer:** EDA Specialist (R6)
**Scope:** R5 EDA findings vs. report integration status + new analyses needed
**Data on disk:** `Reports/figures/eda_*.png` (10 charts present), `data/gold/outlet_features.parquet`, `Results/validation_report.json`

---

# TL;DR

- **All 10 R4 EDA charts still exist on disk** — the analysis is real and reproducible.
- **The report STILL does not reference these charts.** R5 T2.2 was not executed. `Reports/final_report.md` has zero `\includegraphics` references to any `eda_*.png`. The 10 charts are invisible to judges.
- **Three new EDA gaps identified for R6:** (1) no outlet-level uplift distribution by distributor, (2) no January-specific seasonality validation, (3) no POI coverage map of Sri Lanka with outlet overlay. These would strengthen the viva pitch materially.

---

# EDA Charts vs. Report Integration Audit (R6 — same gap as R5)

| Chart file | Finding | In `Reports/final_report.md`? | Risk if missing |
|---|---|---|:---:|---|
| `eda_censoring_fingerprint.png` | 1.16% censored; Extra Large 4.45% | **NO** | Judges question why censoring correction cited with 1.16% censored |
| `eda_distributor_volume.png` | DIST_S_01/02 censoring ~5x peer | **NO** | Strong commercial insight invisible |
| `eda_cooler_saturation.png` | Knee at 3 coolers; 3→4 = 0% lift | **NO** | Most actionable EDA finding not in report |
| `eda_poi_outlet_type.png` | All 7 outlet types: \|r\| ≤ 0.026 | **NO** | Credibility risk — report oversells POI, data contradicts |
| `eda_yoy_stability.png` | 34.9% stable, 33.6% volatile; median Jan growth ≈ 1.000 | **NO** | Jan 2026 prediction rationale unsupported |
| `eda_province_seasonality.png` | W province Avurudu +43%; S peaks Feb | **NO** | Business insight invisible |
| `eda_top100_sanity.png` | Top-100 uplift outlets: 9.5× censoring enrichment | **NO** | Viva Slide 3 weaker without this |
| `eda_frontier_gap.png` | 15.62% frontier < observed_max | **NO** | V3b floor rationale missing data support |
| `eda_constraint_uplift.png` | Constraint→uplift mapping, V4 root cause | **NO** | Methodology explanation missing data support |
| `eda_manski_band.png` | 6.3% at upper Manski bound; 0% at lower | **NO** | Manski narrative unsupported |

**Status: 10/10 charts on disk; 0/10 referenced in the canonical report. Same gap as R5.**

---

# New EDA Gaps for R6

## Gap 1: Uplift distribution by distributor

The R4 EDA found DIST_S_01/02 have ~5× censoring rate. But we don't have a chart showing **uplift distribution by distributor**. This would directly support the business recommendation to investigate Southern province supply allocation.

**New chart:** Boxplot of `uplift_ratio` by `Distributor_ID`, with DIST_S_01/02 highlighted in red.

## Gap 2: January-specific seasonality validation

The model predicts for January 2026. We have YoY stability charts but no **January-only** analysis: what was the median Jan volume vs annual median? Is January systematically higher or lower? This defends the January-specific prediction.

**New chart:** Bar chart of median monthly volume by month (all years pooled), with January highlighted.

## Gap 3: POI coverage map of Sri Lanka

The report mentions "denser tags in Colombo/Kandy/Galle, sparser in rural North-Western" but has no map. A Sri Lanka map with outlet locations colored by POI catchment score would be visually compelling for the viva.

**New chart:** Scatter plot of outlet lat/lon colored by `poi_catchment_score`, overlaid on Sri Lanka outline.

---

# How to Close the Report Gap (same as R5 T2.2, still needed)

1. **Section 1 (DE)** — Add: `\includegraphics{Reports/figures/eda_cooler_saturation.png}` with caption: *"Cooler count saturates at 3 — volumes at 3, 4, and 5 coolers are statistically indistinguishable."*

2. **Section 2 (POI)** — Replace POI claims with honest disclosure: *"POI catchment score shows low correlation with outlet volume (max |r| = 0.026 across outlet types). The feature contributes to the catchment density composite but is not the dominant signal."* Add `\includegraphics{Reports/figures/eda_poi_outlet_type.png}`.

3. **Section 3 (Methodology)** — Add: `\includegraphics{Reports/figures/eda_top100_sanity.png}` with caption: *"Top-100 highest-uplift outlets show 9.5× censoring enrichment. DIST_S_01 and DIST_S_02 show 5× the censoring rate of other distributors."*

4. **Section 3 (Methodology)** — Add: `\includegraphics{Reports/figures/eda_frontier_gap.png}` with caption: *"frontier_q90 < observed_max for 15.62% of outlets, validating the max(potential, observed_max) floor."*

---

# 5 EDA Findings That Must Be in the Final PDF

1. **Cooler saturation at 3** — Concrete, data-driven, memorable. Shows the team looked at the data.
2. **DIST_S_01 / DIST_S_02 censoring hotspots** — Converts statistical model into business action.
3. **POI near-zero correlation + honest framing** — Pre-empts hostile Q3. Shows maturity.
4. **Top-100 uplift sanity check** — 9.5× censoring enrichment proves model found right outlets.
5. **YoY January stability** — Median growth = 1.000 grounds the prediction in last observed January.

---

# Notebook 23 Status

All 10 R4 charts on disk. Notebook not re-run needed unless new charts added.

**Recommended R6 additions to notebook 23 (new cells, append-only):**
- Cell N+1: Uplift distribution by distributor (boxplot → `eda_uplift_by_distributor.png`)
- Cell N+2: January-specific monthly median volume (bar chart → `eda_january_seasonality.png`)
- Cell N+3: Sri Lanka POI coverage map (scatter → `eda_poi_coverage_map.png`)
- Cell N+4: Summary table cell generating `eda_summary_table.csv` (as specified in R5)
