# Judge Proxy — Data Storm 7.0 Storming Round
**Report reviewed:** `final_report_v3.pdf` (5 pages)  
**Rubric:** Data Engineering 40% / Methodology 40% / GenAI 20%  
**Reviewer stance:** Senior panel (DS + DE + Business). Not a cheerleader.

---

# TL;DR

- **Score: 82 / 100 → Strong.** The methodology and GenAI transparency are genuinely above-average for a hackathon. Data engineering is solid but not watertight.
- **Biggest risk at viva:** The POI features have near-zero empirical correlation with volume, but the report markets them confidently as "catchment demand drivers." A prepared judge will attack this.
- **Biggest strength:** The team honestly labels the estimand as non-point-identified and provides per-outlet Manski bounds. Most teams never admit non-identifiability. This buys credibility.

---

# Per-Criterion Scorecard

| # | Criterion | Score | One-line reason | Key evidence (↑ or ↓) |
|---|-----------|------:|-----------------|----------------------|
| 1 | Bronze→Silver→Gold + rejected store | **8 / 10** | Pipeline diagram, SHA-256 audit, every reject has `failure_reason`; breakdown of 480+9,606+93 = 10,179 rows is clear. | ↑ `dataset_name, failed_check, failure_reason` schema shown. ↓ Can't verify the store is queryable/filterable from the PDF alone; 9,606 transaction rejects is a large fraction and no justification for that threshold is given. |
| 2 | Reusable + parameterizable DQ checks | **9 / 10** | Six functions with parameterized signatures shown in Table 1; applied consistently across all 5 datasets. | ↑ `geospatial_bounds_check(df, lat, lon, lat_range, lon_range)` is non-trivial; functions cover all rubric-recommended check types. ↓ "Zero check is hardcoded for one dataset" — honestly disclosed but still an inconsistency. |
| 3 | Legacy SFA/ERP artifacts neutralised | **7.5 / 10** | Table 2 covers 7 explicit artifact types with counts and actions; typos, case issues, missing values, bad coords, negatives, and holiday dupes all caught. | ↑ "Bakry → Bakery" and `lowercase small` normalization documented. ↓ No mention of phantom outlets, zombie distributor routes, or cross-SFA referential contamination — deeper ERP forensics missing. Reads like clean-data problems, not legacy-system artifacts. |
| 4 | POI scraping pipeline robustness | **9 / 10** | Geofabrik offline extract chosen explicitly over Overpass with stated reasons (ToS + timeout infeasibility at 720,000 requests). Idempotent, 25–45 min, `poi_pipeline/` is a separate sub-project. | ↑ ToS awareness + scalability reasoning is production-grade. BallTree haversine for nearest-neighbor is correct. ↓ No vintage date on OSM extract; small OSM-LK coverage gap for kades honestly disclosed but not mitigated. |
| 5 | Features that isolate true market signals | **7 / 10** | 63 POI columns (multi-radius counts + decay scores + composite) plus constraint score (PCA + frontier residual + plateau). Monotone XGBoost constraints applied. | ↑ Gaussian-decay weighting and composite `poi_catchment_score` are methodologically sound. ↓ R4 EDA shows POI correlation with volume is `|r| ≤ 0.026`. The PDF does not acknowledge this, and no feature importance is shown. The complexity may not be earning its keep. |
| 6 | Conceptualisation of latent potential | **8.5 / 10** | DAG, right-censored identification, honest "not point-identified," Manski bounds per outlet, conformal interval output. Best single section of the paper. | ↑ Manski partial-identification framing is rare in hackathons. ↑ Reporting a band instead of a point is intellectually honest. ↓ The actual distribution of Manski band widths is not shown — judge cannot assess whether bounds are informative or vacuously wide. |
| 7 | Math/stat for missing target + censored data | **8 / 10** | CH-3 (Chernozhukov-Hong 2002) for censoring propensity, SFA via truncated-normal MLE, conformal QR on 20% holdout, sensitivity sweep on three free knobs. | ↑ All four method blocks have explicit formulas. CQR holdout is disjoint from training set — correct. ↓ CH-3 is cosmetic at global 1.16% censoring rate (from R4). The PDF prominently features it without noting it mainly fires on DIST\_S\_01/S\_02. Overclaims the correction's reach. |
| 8 | Documentation of LLM usage | **9 / 10** | Table 5 (p. 5): 5 phases, AI usage named per phase, human-validation step named per phase, full log referenced at `Docs/ai_transparency_log_v2.md`. | ↑ Phase-by-phase transparency is far better than any "we used ChatGPT" boilerplate. ↓ The log file itself is not in the PDF; judge has to trust it exists. |
| 9 | AI as accelerator (not crutch) | **8 / 10** | AI used for domain research (10-channel swarm), methodology audit (4 council rounds), implementation scaffolding, SFA+POI form recall, LaTeX assembly. Human owns each decision. | ↑ Council review structure (4 rounds, 4–5 parallel critics) is genuine engineering discipline, not rubber-stamping. ↓ "Cursor + Claude/GPT routing scaffolded `src/quality/, src/cleaning/`" — if AI wrote the DQ layer, that's closer to crutch territory and needs clearer human-ownership evidence. |
| 10 | Critical evaluation of AI outputs | **8 / 10** | "Every finding cites `file:line`; verified or rebutted manually." OSM coverage caveat (p. 3) is explicit AI-assisted work evaluated honestly. SFA recalled from LLM cross-checked against Greene's *Econometric Analysis*. | ↑ Citing specific textbook to validate LLM recall is the right instinct. ↑ The orange warning box on p. 3 (OSM caveat) is exactly the kind of critical self-evaluation judges want to see. ↓ No example of an AI claim that was *rejected* — only acceptances shown. |

---

# Total Score

| Section | Raw scores | Raw sum | Max raw | Section weight | Weighted score |
|---------|-----------|---------|---------|---------------|---------------|
| Data Engineering (criteria 1–5) | 8 + 9 + 7.5 + 9 + 7 | **40.5** | 50 | 40% | **32.4** |
| Methodology (criteria 6–7) | 8.5 + 8 | **16.5** | 20 | 40% | **33.0** |
| GenAI (criteria 8–10) | 9 + 8 + 8 | **25** | 30 | 20% | **16.7** |
| **Total** | | | | **100%** | **82.1 / 100** |

---

# 30-Second First Impression

Page 1 lands well. The title is precise ("Latent Outlet Potential Estimation" — not "Sales Prediction"). The one-line method box signals that the team knows the math: right-censored, partial identification, not a naive regression. The headline table gives concrete numbers immediately: 20,000 outlets, 42,386 POIs, 1.250× median uplift, 6/6 PASS. The "Build trail" mentioning 4 AI council rounds is unusual and makes the team look disciplined rather than last-minute.

**30-second verdict:** *These people have thought about this properly. Let me check if the methodology holds up.*

That's a strong opening impression — it makes me want to read further, which is the entire job of a cover page.

---

# Single Hardest Viva Question

> **"Your CH-3 censoring correction requires a propensity P(censored | X). You estimate this using plateau proxies on 1.16% of outlets that show true ceiling behaviour. Walk me through: how many outlets actually receive a materially different prediction because of CH-3 vs. without it? And if the answer is 'very few,' why does it appear alongside SFA and XGBoost as if it's load-bearing?"**

**Team's defensible answer (from a judge's perspective):**
CH-3 is conditionally applied only to outlets where the estimated propensity exceeds 0.10. This fires mainly on DIST_S_01 and DIST_S_02, which have ~5× the base censoring rate. For the other 8 distributors, CH-3 is a no-op and the q90 XGBoost frontier dominates. The correction is presented in the stack because it is structurally necessary for the Southern distributor subgroup, not because it changes global aggregates. The sensitivity table on p. 5 (knob sweep) is indirect evidence that removing it would change fewer than 5% of predictions materially.

If the team cannot produce outlet-level counts showing CH-3 actually changes predictions for ≥500 outlets, this becomes a credibility problem. They need that number ready.

---

# 3 Things This Does BETTER

1. **Offline Geofabrik extract over Overpass API.** The explicit reasoning — 720,000 API requests, timeouts, ToS violation — is the kind of production-grade decision-making most hackathon teams miss entirely. They picked the right tool and explained why. This is a senior DE instinct.

2. **Manski partial-identification bounds per outlet.** Most teams claim a point estimate for a non-identified estimand without blinking. This team labels the problem correctly ("not point-identified"), reports a band, and uses Manski's framework by name with a citation. This is methodologically honest in a way that stands out at a judged event.

3. **GenAI transparency at phase granularity.** Table 5 breaks down 5 workflow phases, names the AI tool, and names the human validation step per phase. This is not boilerplate — it is auditable. The reference to a full log at `Docs/ai_transparency_log_v2.md` gives the judges somewhere to go. No other hackathon entry I have seen documents AI usage this way.

---

# 3 Things That LOSE Me Points

1. **POI features with near-zero empirical correlation, marketed as "catchment demand drivers."** R4 EDA established `|r| ≤ 0.026` for POI features against volume at outlet level. The PDF on p. 3 honestly discloses the OSM-LK coverage gap but does not say "POI barely correlates with volume." Then p. 4 weights POI in the constraint score at ~20%. A judge who asks "show me your feature importances" will find nothing in the PDF to defend this weighting. This is the single most attackable gap.

2. **CH-3 censoring correction overclaimed.** The method stack (p. 4) presents CH-3 as a co-equal component alongside SFA and XGBoost frontier. But the 1.16% global censoring rate means CH-3 is largely cosmetic for 98.84% of outlets. The PDF never says this. It reads as if censoring is a major modeling challenge when the real heavy lifting is done by the frontier ensemble and the lower-bound floor. This inflates the apparent method complexity in a way a statistician judge will see through.

3. **No feature importance or ablation study.** The PDF shows the formula, the components, and the validation checklist — but not which components contribute to the 1.25× median uplift. No SHAP plot, no ablation table, no comparison of "frontier-only" vs "full stack." The judge cannot verify that the method complexity (SFA + XGBoost + CH-3 + CQR + Manski) is better than a simpler peer-bucket cap applied to historical max. The validation checks confirm the output is well-formed, not that the model is better than a baseline.

---

# Ship Verdict

**Strong (82 / 100)**

The pipeline is clean, the identification theory is honest, and the GenAI transparency is best-in-class for this format. The weaknesses (POI signal strength, CH-3 overstatement, missing ablation) are real but survivable if the team can answer questions under pressure. The report will not embarrass itself in front of the John Keells panel. It will, however, get a hard question about feature importance that it currently cannot answer from the PDF alone.

**Prepare before viva:** one table showing CH-3 outlet count affected, one feature-importance chart (even a quick XGBoost `gain` plot), one sentence in the report acknowledging that POI is a weak signal used as a directional catchment proxy rather than a strong predictive feature.
