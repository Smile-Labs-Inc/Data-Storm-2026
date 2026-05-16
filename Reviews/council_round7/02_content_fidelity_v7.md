# TL;DR

- Audited 91 material numeric/formula claims from `Reports/final_report_v3.tex` against rendered pages, ground-truth artifacts, CSV row counts, and code.
- Found 8 hard numeric/formula failures: rejected-row totals are mislabeled, one sensitivity range is wrong, the final formula is incomplete vs code, POI feature-column claims do not match the feature CSV, and "four critics per round" is wrong for R4. Path failures are listed separately.
- Fidelity grade: **7 / 10**. Strong core submission numbers, but the failures are viva-risky because they are visible headline/method claims.

# Numeric Claim Audit

| Claim in PDF (page, location) | Number stated | Source file | Source value | Match? |
|---|---:|---|---:|---|
| P1 headline: outlets predicted | 20,000 | `Results/smil_labs_predictions.csv` | 20,000 rows; columns `Outlet_ID`, `Maximum_Monthly_Liters` | OK |
| P1 headline: POI categories | 9 categories | `poi_pipeline/data/pois/_extraction_summary.csv` | 9 rows/categories | OK |
| P1 headline: external POIs scraped | 42,386 | `poi_pipeline/output/poi_coverage_report.md`; `_extraction_summary.csv` | 42,386 total | OK |
| P1 headline: outlets with POI within 2 km | 80.9% | `poi_pipeline/output/poi_coverage_report.md` | 80.9% | OK |
| P1 headline: POI radius | 2 km | `poi_pipeline/output/poi_coverage_report.md` | 2 km coverage threshold | OK |
| P1 headline: coord rejected records | 480 | `data/silver_rejected/quality_summary.csv`; rejected CSV row count | 480 failed check records, but only 240 unique `outlet_coordinates_rejected.csv` rows | **FAIL** - label says records quarantined |
| P1 headline: transaction rejected records | 9,606 | `data/silver_rejected/quality_summary.csv`; rejected CSV row count | 9,606 failed check records, but only 4,853 unique `transactions_history_rejected.csv` rows | **FAIL** - label says records quarantined |
| P1 headline: holiday rejected records | 93 | `data/silver_rejected/holiday_list_rejected.csv` | 93 rows | OK |
| P1 headline: median uplift | 1.250x | `Results/validation_report.md`; `validation_report.json` | `median_uplift=1.250` | OK |
| P1 headline: automated checks | 6 checks | `Results/validation_report.md`; `src/reporting/validation.py` | 6 checks | OK |
| P1 headline: submission preflight | 6 / 6 PASS | `Results/validation_report.md`; `validation_report.json` | 6 rows, all `OK`; `all_passed=true` | OK |
| P1 build trail: council rounds | 4 rounds | `Reviews/` | R1 root review + `council_round2`, `council_round3`, `council_round4` | OK |
| P1 build trail: critics per round | 4 per round | `Reviews/` file inventory | R1=4, R2=4, R3=4, R4=5 individual critic files | **FAIL** - R4 had 5 |
| P2 lakehouse: DQ function count | 6 functions | `Docs/data_quality_report.md`; `src/quality/checks.py` | 6 named checks in PDF table | OK |
| P2 lakehouse: raw dataset count | 5 raw datasets | `Docs/data_quality_report.md`; `quality_summary.csv` | 5 datasets named | OK |
| P2 diagram: rejected rows | 10,179 rows | `data/silver_rejected/*.csv`; `quality_summary.csv` | 10,179 failed-check total; unique rejected rows are 5,186 (`240 + 4,853 + 93`) | **FAIL** - not rows |
| P2 diagram: DQ checks | 6 DQ checks | `src/quality/checks.py`; PDF table | 6 check functions listed | OK |
| P2 table: all six functions parameterized | 6 functions | `src/quality/checks.py` | six callable check functions are present | OK |
| P2 artifact: `Outlet_Type` typos total | 785 | `Reports/final_report.md`; v1 archive | 390 `Grocry` + 395 `Bakry` = 785 | OK |
| P2 artifact: lowercase `small` | 600 | `Reports/final_report.md`; v1 archive | 600 | OK |
| P2 artifact: missing `Outlet_Size` | 196 | `Reports/final_report.md`; v1 archive | 196 | OK |
| P2 artifact: bad coordinate rows | 240 | `Docs/data_quality_report.md`; rejected CSV row count | 240 | OK |
| P2 artifact: latitude bounds | 5.5-10 N | `Docs/data_quality_report.md` | lat=(5.5, 10.0) | OK |
| P2 artifact: longitude bounds | 79-82.5 E | `Docs/data_quality_report.md` | lon=(79.0, 82.5) | OK |
| P2 artifact: non-positive `Volume_Liters` | 4,853 | `Docs/data_quality_report.md`; `quality_summary.csv` | 4,853 | OK |
| P2 artifact: non-positive `Total_Bill_Value` | 4,753 | `Docs/data_quality_report.md`; `quality_summary.csv` | 4,753 | OK |
| P2 artifact: holiday duplicates | 93 | `data/silver_rejected/holiday_list_rejected.csv` | 93 | OK |
| P3 Overpass request math: outlets | 20,000 | `Results/smil_labs_predictions.csv` | 20,000 rows | OK |
| P3 Overpass request math: categories | 9 | `_extraction_summary.csv` | 9 categories | OK |
| P3 Overpass request math: radii | 4 | P3 feature-design text | 250 m, 500 m, 1 km, 2 km = 4 radii | OK |
| P3 Overpass request math: total requests | 720,000 | arithmetic | 20,000 x 9 x 4 = 720,000 | OK |
| P3 PBF size | ~136 MB | `data/sri-lanka-latest.osm.pbf`; `poi_pipeline/data/raw/sri-lanka-latest.osm.pbf` | 136.11 MB and 136.10 MB | OK |
| P3 runtime | 25-45 min | `_extraction_summary.csv` elapsed sum | 1,492.2 sec = 24.9 min for extraction; within stated lower bound after rounding | OK |
| P3 section title: target categories | 9 | `_extraction_summary.csv` | 9 categories | OK |
| P3 section title: outlet coverage | 80.9% | `poi_coverage_report.md` | 80.9% | OK |
| P3 POI table: schools/universities | 5,694 | `_extraction_summary.csv`; `poi_coverage_report.md` | 5,694 | OK |
| P3 POI table: transport hubs | 5,799 | `_extraction_summary.csv`; `poi_coverage_report.md` | 5,799 | OK |
| P3 POI table: hospitals/healthcare | 2,007 | `_extraction_summary.csv`; `poi_coverage_report.md` | 2,007 | OK |
| P3 POI table: restaurants/cafes | 4,667 | `_extraction_summary.csv`; `poi_coverage_report.md` | 4,667 | OK |
| P3 POI table: supermarkets/groceries | 2,543 | `_extraction_summary.csv`; `poi_coverage_report.md` | 2,543 | OK |
| P3 POI table: religious places | 9,255 | `_extraction_summary.csv`; `poi_coverage_report.md` | 9,255 | OK |
| P3 POI table: hotels/attractions | 5,513 | `_extraction_summary.csv`; `poi_coverage_report.md` | 5,513 | OK |
| P3 POI table: offices | 4,169 | `_extraction_summary.csv`; `poi_coverage_report.md` | 4,169 | OK |
| P3 POI table: banks/ATMs | 2,739 | `_extraction_summary.csv`; `poi_coverage_report.md` | 2,739 | OK |
| P3 POI table: total | 42,386 | `_extraction_summary.csv`; `poi_coverage_report.md` | 42,386 | OK |
| P3 feature design: columns | ~63 columns | `data/gold/outlet_poi_features_full.csv` | 59 total columns, 58 excluding `Outlet_ID` | **FAIL** |
| P3 feature design: counts per category | 4 columns | `data/gold/outlet_poi_features_full.csv` | 4 count radii per category | OK |
| P3 feature design: radii | 250 m / 500 m / 1 km / 2 km | `data/gold/outlet_poi_features_full.csv` column names | `0p25km`, `0p5km`, `1p0km`, `2p0km` | OK |
| P3 feature design: urban sigma | 0.75 km | `Reports/final_report.md`; report text | 0.75 km stated in v2 source; not independently encoded in inspected feature CSV | OK |
| P3 feature design: rural sigma | 2 km | `Reports/final_report.md`; report text | 2 km stated in v2 source; not independently encoded in inspected feature CSV | OK |
| P3 feature design: `has_within_500m` flags | 1 col per category | `data/gold/outlet_poi_features_full.csv` | 0 `has_*` columns found | **FAIL** |
| P3 feature design: decay scores averaged | 9 decay scores | `data/gold/outlet_poi_features_full.csv` | 9 category score groups plus totals | OK |
| P3 feature design: no-POI sentinel radius | 2 km / `2 * max_radius` | `poi_coverage_report.md` | explicitly says `dist_nearest = 2 * max_radius` for no POI within 2 km | OK |
| P3 caveat: POI signal weight | ~20% | `poi_coverage_report.md`; `src/modeling/constraint_score.py` | coverage report says 20%; code uses `weight_capacity=0.2`, not POI-specific | PARTIAL |
| P4 method stack: components | 4 components | `src/modeling/` modules and report text | lower bound, frontier ensemble, censoring correction, constraint score | OK |
| P4 lower bound formula | max(3rd-highest month, median) | `src/modeling/lower_bound.py` | `return max(third_highest, median_floor)` for >=6 active months | OK |
| P4 lower bound fallback | fewer than 6 active months | `src/modeling/lower_bound.py` | fallback uses outlet p95, never below median | OK |
| P4 frontier blend | 60/40 XGBoost q90 + SFA | report text; no direct formula in inspected `predict.py` | not contradicted by final combiner; source implementation not fully inspected here | PARTIAL |
| P4 XGBoost version | 2.0 | report text only | not verified in inspected artifacts | PARTIAL |
| P4 quantile alphas | [0.5, 0.75, 0.9, 0.95] | `Reports/figures/sensitivity_summary.md`; modeling text | sensitivity uses 0.90/0.95 available; q85 absent from table output | PARTIAL |
| P4 censoring threshold | P < 0.10 | report text; `Reports/final_report.md` | v2 source says P(censored) < 0.10 | OK |
| P4 constraint signals | 3 signals | `src/modeling/constraint_score.py` | frontier residual, plateau, PCA capacity | OK |
| P4 plateau threshold | months_since_new_max > 6 | `src/modeling/constraint_score.py` | `months_since_max > 6` | OK |
| P4 plateau variance threshold | recent variance ratio < 0.4 | `src/modeling/constraint_score.py` | `var_ratio < 0.4` | OK |
| P4 constraint score range | [0, 1] | `src/modeling/constraint_score.py` | sigmoid output in [0,1] | OK |
| P4 uplift-floor threshold | cs >= 0.40 | `src/modeling/predict.py` | `UPLIFT_FLOOR_CS_THRESHOLD = 0.40` | OK |
| P4 uplift-floor ratio | 1.25x | `src/modeling/predict.py` | `UPLIFT_FLOOR_RATIO = 1.25` | OK |
| P4 final formula | `max(observed_max, lower_bound + s_i*(F_i-lower_bound))`, capped at `B_i*observed_max` | `src/modeling/predict.py`; `src/modeling/caps.py` | code also clips negative gap to 0 and applies conditional 1.25x uplift floor before cap | **FAIL** - formula block is incomplete |
| P4 bucket cap percentile | empirical 95th percentile | `src/modeling/caps.py` | `cap_quantile=0.95` | OK |
| P4 bucket dimensions | `Outlet_Type x Outlet_Size` | `src/modeling/caps.py` | `bucket_cols=("Outlet_Type", "Outlet_Size")` | OK |
| P4 holdout | 20% outlet-level holdout | `Reports/final_report.md` | v2 source says 80/20 outlet-level holdout | OK |
| P5 validation checklist count | 6-item | `src/reporting/validation.py`; validation reports | 6 checks | OK |
| P5 V1 row count | 20,000 rows | `Results/validation_report.md`; CSV diagnostics | 20,000 | OK |
| P5 V1 schema | 2 columns | `Results/smil_labs_predictions.csv` | `Outlet_ID`, `Maximum_Monthly_Liters` | OK |
| P5 V2 NaN count | 0 | `Results/validation_report.md` | NaN=0 | OK |
| P5 V2 negative count | 0 | `Results/validation_report.md` | neg=0 | OK |
| P5 V2 unique IDs | True | `Results/validation_report.md` | unique=True | OK |
| P5 V3a missing IDs | 0 | `Results/validation_report.md` | missing=0 | OK |
| P5 V3b threshold | >=99% predicted >= historical max | `src/reporting/validation.py` | `pct_below < 1.0` | OK |
| P5 V3b final value | 0.00% below historical max | `Results/validation_report.md` | 0.00% | OK |
| P5 V4 range | [1.25, 2.2] | `src/reporting/validation.py`; validation report | `[1.25, 2.2]` | OK |
| P5 V4 final median | 1.250 | `Results/validation_report.md`; validation JSON | 1.250 | OK |
| P5 V5 threshold | <25% cap binding | `src/reporting/validation.py`; validation report | <25.0% | OK |
| P5 V5 final cap binding | 0.00% | `Results/validation_report.md` | 0.00% appear at cap | OK |
| P5 sensitivity: frontier quantiles swept | 0.85 / 0.90 / 0.95 | `src/reporting/sensitivity.py`; `sensitivity_table.csv` | code permits all three; current output includes 0.90 and 0.95 only | PARTIAL |
| P5 sensitivity: cap multipliers | 2 / 3 / 4 / 5 / 6 | `src/reporting/sensitivity.py`; `sensitivity_table.csv` | 2.0x through 6.0x | OK |
| P5 sensitivity: median uplift range | [1.000, 1.022] | `Reports/figures/sensitivity_summary.md`; `sensitivity_table.csv` | median uplift is 1.250 in every listed row | **FAIL** |
| P5 sensitivity: cap binding at loosest cap | 0% | `sensitivity_summary.md`; `sensitivity_table.csv` | 0.0% at 6.0x cap rows | OK |
| P5 GenAI workflow: research channels | 10-channel swarm | `Reports/final_report.md`; `research/research_brief.md` path exists | v2 source states 10 parallel research subagents | OK |
| P5 GenAI workflow: council critics | 4-5 critics | `Reviews/` file inventory | R1-R3 have 4; R4 has 5 | OK |
| P5 conformal target coverage | 90% | `Results/conformal_intervals_v2.csv` path exists; `Reports/final_report.md` | v2 source says empirical coverage >=90%; deliverable path exists | OK |

# Path Audit

| Path in PDF | Page | Resolved on disk? | Notes |
|---|---:|:---:|---|
| `Reviews/council_review.md` | 1 | YES | Exists. |
| `council_round2/` | 1 | NO | Exact path does not exist at repo root. Intended path `Reviews/council_round2/` exists. |
| `council_round3/` | 1 | NO | Exact path does not exist at repo root. Intended path `Reviews/council_round3/` exists. |
| `council_round4/` | 1 | NO | Exact path does not exist at repo root. Intended path `Reviews/council_round4/` exists. |
| `src/` | 1, 5 | YES | Exists. |
| `data/bronze/` | 2 | YES | Exists. |
| `src/quality/checks.py` | 2 | YES | Exists. |
| `data/silver_rejected/` | 2 | YES | Exists. |
| `sri-lanka-latest.osm.pbf` | 3 | YES | File exists under `data/` and `poi_pipeline/data/raw/`; PDF gives filename only. |
| `poi_pipeline/` | 3 | YES | Exists. |
| `poi_pipeline/data/pois/` | 3 | YES | Exists. |
| `src/reporting/validation.py` | 5 | YES | Exists. |
| `Results/validation_report.md` | 5 | YES | Exists. |
| `src/reporting/sensitivity.py` | 5 | YES | Exists. |
| `research/research_brief.md` | 5 | YES | Exists. |
| `src/quality/` | 5 | YES | Exists. |
| `src/cleaning/` | 5 | YES | Exists. |
| `src/modeling/` | 5 | YES | Exists. |
| `src/reporting/` | 5 | YES | Exists. |
| `Docs/ai_transparency_log_v2.md` | 5 | YES | Exists. |
| `Results/smil_labs_predictions.csv` | 5 | YES | Exists; 20,000 rows. |
| `Results/_legacy/` | 5 | YES | Exists. |
| `Results/smil_labs_predictions_full_20000.csv` | 5 | YES | Exists. |
| `Results/manski_bands_v2.csv` | 5 | YES | Exists. |
| `Results/conformal_intervals_v2.csv` | 5 | YES | Exists. |
| `Notebooks/20_v2_data_pipeline.ipynb` | 5 | YES | Exists. |
| `Notebooks/21_v2_modeling.ipynb` | 5 | YES | Exists. |
| `Notebooks/22_v2_validation.ipynb` | 5 | NO | Actual file is `Notebooks/22_v2_validation_and_submission.ipynb`. |
| `data/gold/` | 5 | YES | Exists. |

# Citation Audit

| Check | Result |
|---|---|
| Unique `\cite{}` keys in `final_report_v3.tex` | 6: `manski2003partial`, `aigner1977sfa`, `jondrow1982je`, `chernozhukov2002hong`, `romano2019cqr`, `chernozhukov2010crossing` |
| Keys present in `Reports/references.bib` | All 6 cited keys exist. |
| Bibliography numbers rendered in page 5 PNG | 6 numbered entries, `[1]` through `[6]`. |
| Count match: cited keys vs rendered bibliography | YES: 6 cited keys, 6 rendered bibliography entries. |
| Unused BibTeX entry | `battese1995panel` exists in `references.bib` but is not cited and does not render. Not a fidelity failure. |

# v1 vs v3 Inconsistencies

These are real contradictions with the archived v1 report, but most are intentional fixes. Do not mix v1 and v3 language in the viva.

| Topic | v1 archive says | v3 says | Current disk truth | Risk |
|---|---|---|---|---|
| Platform submission rows | 914 platform rows | 20,000 outlets predicted | `smil_labs_predictions.csv` has 20,000 rows | v3 is current; v1 is obsolete. |
| ID column | `row_id` | `Outlet_ID` | CSV uses `Outlet_ID` | v3 is current; v1 is obsolete. |
| Median uplift | 1.18x | 1.250x | validation report says 1.250 | v3 is current; v1 is obsolete. |
| POI acquisition | Overpass, 9,581 POIs, 902 valid target outlets | Geofabrik PBF, 42,386 POIs, 80.9% of 20,000 outlets | POI coverage and extraction summary match v3 | v3 is current; v1 is obsolete. |
| Lower bound | `max(historical_max, january_max, recent_3_month_max)` | robust 3rd-highest / median | `lower_bound.py` matches v3 | v3 is current; v1 is obsolete. |
| Constraint score | rank-sum with coordinate availability and POI demand score | three signals: frontier residual, plateau, PCA capacity | `constraint_score.py` matches v3 | v3 is current; v1 is obsolete. |
| Caps | peer 98th percentile and hard size caps | empirical 95th-percentile bucket cap | `caps.py` matches v3 | v3 is current; v1 is obsolete. |

# Missing Content

Important content from `Reports/final_report.md` that got lost or weakened in the v3 LaTeX port:

- The v2 cover context lost `2.37M` historical transactions, 10 distributors, 10 SKUs, and the four province scope. That context helps judges understand scale.
- The EDA evidence was removed: all 20,000 outlets in transaction history, 36 months, median observed max 164.0 L, and 95th percentile 1,307.9 L.
- The POI safety guards were removed: idempotent download, deduplication key, sentinel defaults, and per-category extraction summary.
- The geographic OSM caveat was weakened: v2 explicitly says Colombo/Kandy/Galle are denser and rural North-Western is sparser.
- The Manski lower/upper formulas were removed. v3 says Manski bounds exist but does not show `manski_lower` / `manski_upper`.
- The validation principles were removed: no blind acceptance, adversarial review, and provenance trail.
- The "what we did NOT use AI for" section was removed. That was useful for GenAI transparency.
- The reproducibility appendix commands were removed. v3 lists notebooks, but not the run sequence.

# Fidelity Grade

**7 / 10**

The core headline output is mostly solid: 20,000 rows, POI total, coverage, median uplift, and 6/6 validation all trace to disk. The grade drops because the report has several visible precision failures: rejected "rows" are really failed-check totals, the sensitivity median range is wrong, the final formula is not exact vs `predict.py`, the POI feature-column description does not match the feature CSV, and multiple paths print incorrectly.
