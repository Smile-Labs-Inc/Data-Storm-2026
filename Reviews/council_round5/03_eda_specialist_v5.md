# EDA Specialist — Council Round 5

**Reviewer:** EDA Specialist (R5)
**Scope:** R4 EDA findings vs. what is now in the report + notebook 23 outputs
**Data on disk:** `Reports/figures/eda_*.png` (10 charts present), `data/gold/outlet_features.parquet`, `Results/validation_report.json`

---

# TL;DR

- **All 10 R4 EDA charts exist on disk** (`Reports/figures/eda_*.png`) — the notebook ran correctly. The analysis is real.
- **The report does NOT reference these charts.** `Reports/final_report.md` cites no `eda_*.png` figures. The PDF submission has the charts in the repo but not in the narrative.
- **Three R4 EDA insights must be in the PDF** or they don't count for the rubric: (1) cooler saturation at 3, (2) DIST_S_01/S_02 censoring hotspots, (3) POI signal is near-zero. If judges don't see them in the 5-page PDF, the EDA work is invisible.
- **POI "near-zero signal" needs a calibrated response in the report** — currently the report oversells POI and the EDA data contradicts it.

---

# EDA Charts vs. Report Integration Audit

| Chart file | Finding | In `Reports/final_report.md`? | Risk if missing |
|---|---|:---:|---|
| `eda_censoring_fingerprint.png` | 1.16% censored; Extra Large 4.45% | No | Judges may ask why censoring correction is cited with only 1.16% censored |
| `eda_distributor_volume.png` | DIST_S_01/02 censoring ~5x peer | No | Strong commercial insight left out of report |
| `eda_cooler_saturation.png` | Knee at 3 coolers; 3→4 = 0% lift | No | Misses a concrete, memorable EDA finding |
| `eda_poi_outlet_type.png` | All 7 outlet types: \|r\| ≤ 0.026 | No | **Credibility risk** — report claims POI drives signal, data says otherwise |
| `eda_yoy_stability.png` | 34.9% stable, 33.6% volatile; median Jan growth ≈ 1.000 | No | Supports Jan 2026 prediction rationale |
| `eda_province_seasonality.png` | W province Avurudu +43%; S peaks Feb | No | John Keells business insight not visible |
| `eda_top100_sanity.png` | Top-100 uplift outlets: 9.5× censoring enrichment | No | Business framing Slide 3 is weaker without this |
| `eda_frontier_gap.png` | 15.62% frontier < observed_max | No | Validates why V3b floor was needed |
| `eda_constraint_uplift.png` | Constraint→uplift mapping, V4 root cause | No | Methodology explanation missing data support |
| `eda_manski_band.png` | 6.3% at upper Manski bound; 0% at lower | No | Manski narrative unsupported |

**10 / 10 charts on disk; 0 / 10 referenced in the canonical report. This is the top EDA gap.**

---

# How to Close the Report Gap (15 minutes)

The 5-page report at `Reports/final_report.md` has room for inline figure references. The minimum viable additions:

1. **Section 1 (DE)** — Add one line: `\includegraphics{Reports/figures/eda_cooler_saturation.png}` with caption: *"Cooler count saturates at 3 — volumes at 3, 4, and 5 coolers are statistically indistinguishable (Figure 1)."*

2. **Section 2 (POI)** — Replace the current claim that POI drives signal with an honest disclosure: *"POI catchment score shows low correlation with outlet volume (max \|r\| = 0.026 across outlet types, Figure 2). The feature contributes to the catchment density composite but is not the dominant signal; the frontier residual and capacity components drive the constraint score."*

3. **Section 3 (Methodology)** — Add the top-100 sanity chart and the distributor finding: *"The top-100 highest-uplift outlets show 9.5× censoring enrichment vs. the population (Figure 3). DIST\_S\_01 and DIST\_S\_02 show 5× the censoring rate of other distributors, suggesting supply-side constraints as the primary mechanism in the Southern province."*

4. **Section 4 (GenAI)** — Reference the `eda_frontier_gap.png` to back the V3b floor rationale: *"EDA confirmed `frontier\_q90 < observed\_max` for 15.62\% of outlets (32.24\% of Extra Large), validating the necessity of the `max(potential, observed\_max)` floor applied in `src/modeling/predict.py`."*

---

# POI Signal: How to Handle in the Report

The EDA found POI catchment scores are near-zero predictors of outlet volume. The **current report text** (Section 2 in both `Reports/final_report.md` and `Docs/smil_labs_final_report.md`) implies POI is a meaningful demand driver. This is a viva trap.

**Recommended honest framing** (replaces or supplements current Section 2 conclusion):

> *"POI features extracted from the Geofabrik Sri Lanka OSM dump confirm 80.9% of outlets have at least one POI within 2 km, providing catchment-density context. However, per-outlet Pearson correlation between `poi_catchment_score` and observed monthly volume is effectively zero across all seven outlet types (max |r| = 0.026). This is consistent with the known OSM coverage gap for informal kades and small grocers in Sri Lanka — the outlets most likely to be capacity-constrained are precisely those with sparse OSM tagging. POI features contribute to the `catchment_density_score` composite, but the dominant signals in the constraint score remain the frontier residual z-score (weight 0.50) and the plateau gate (weight 0.30). We flag this limitation honestly: the POI infrastructure is in place and idempotent; richer tagging in future OSM snapshots would improve signal without any pipeline changes."*

This framing is honest AND demonstrates methodological maturity — both score positively with experienced judges.

---

# 5 EDA Findings That Must Be in the Final PDF

Ranked by rubric impact if present vs. absent:

1. **Cooler saturation at 3** — Concrete, data-driven, memorable. Shows the team looked at the data rather than assumed linearity. *"The 3-cooler ceiling is the most actionable finding in this dataset."*

2. **DIST_S_01 / DIST_S_02 censoring hotspots** — Converts a statistical model into a business action recommendation. John Keells judges love this. *"Investigate supply allocation to the Southern province distributors."*

3. **POI near-zero correlation + honest framing** — Pre-empts the hostile Q3 (*"Why use POI if it's uncorrelated?"*). A team that knows its own limitations and frames them as OSM coverage issues sounds mature.

4. **Top-100 uplift sanity check** — Validators that the model output makes business sense. The 9.5× censoring enrichment in the top-100 is concrete evidence the model found the right outlets. Belongs on Slide 3 of the viva pitch.

5. **YoY January stability** — Defends the Jan 2026 extrapolation. Median growth = 1.000 means the prediction is grounded in the last observed January, not speculative growth.

---

# Notebook 23 Status

All 10 charts from R4's EDA specialist spec are on disk. The notebook is not re-run needed unless data changes. The gap is in the **report**, not the notebook.

**Recommended notebook 23 addition (optional, 10 min):**
Add a summary cell at the end that generates a single-page `eda_summary_table.csv` citing all 10 findings with their values:

| Finding | Statistic | Chart | Report section |
|---|---|---|---|
| Censoring rate | 1.16% | eda_censoring_fingerprint.png | §3 |
| Cooler knee | 3 coolers | eda_cooler_saturation.png | §1 |
| POI signal | max \|r\| = 0.026 | eda_poi_outlet_type.png | §2 |
| DIST_S* elevated | 5× peer rate | eda_distributor_volume.png | §3 |
| Top-100 enrichment | 9.5× | eda_top100_sanity.png | §3 |
| Jan median growth | 1.000 | eda_yoy_stability.png | §3 |
| Province peak | W=April, S=Feb | eda_province_seasonality.png | §3 |
| frontier < obs_max | 15.62% | eda_frontier_gap.png | §3 |
| Manski upper binding | 6.3% | eda_manski_band.png | §3 |
| constraint→uplift corr | Pearson 0.346 | eda_constraint_uplift.png | §3 |

This table gives a judge navigating the repo a single reference for every quantitative EDA claim.
