# Skeptic Review — Data Storm 7.0 Team Methodology

> Reviewer role: assume the plan is overconfident. Hunt for hidden assumptions, narrative-fitting, and judge-bait.
> Reviewed artefacts: `Docs/challenge_brief.md`, `Docs/modeling_methodology.md`, `Docs/data_quality_report.md`, `Docs/eda_summary.md`, `Docs/next_steps_after_eda.md`, `research/research_brief.md`, `Notebooks/01_latent_potential_pipeline.ipynb`, `Results/teamname_predictions*.csv`, `Docs/ai_transparency_log.md`.

---

# TL;DR

- **The "platform submission" is fabricated**: `Results/teamname_predictions.csv` is literally `full_20000.head(914)` — outlets `OUT_00001..OUT_00914` sorted alphabetically (notebook cell at line ~621: `predictions = full_predictions.sort_values('row_id').head(914)`), with column name `row_id` instead of the brief-mandated `Outlet_ID`. This is a self-inflicted disqualifier dressed up as a "platform template" workaround. The research brief already flagged it.
- **The "latent demand" framework collapses to a ~20% nudge on historical max**, scaled by a constraint score that is mostly a re-labelled size/wealth proxy (`structural_capacity_score` 35% + `Cooler_Count` 15% + `mean_sku_count` 15% + `catchment_density_score` 25% + `has_valid_coordinates` 10%). It rewards already-big outlets and uses a data-quality flag (valid coords) as a *demand* signal. The latent-demand framing is rhetoric; the math is `lower_bound + small_size_dependent_constant × frontier_gap`.
- **Zero POI, zero causal/probabilistic logic, zero out-of-sample validation, and zero macro/Avurudu adjustment** — so the team is unilaterally giving up the 50% of the DE+Method rubric that explicitly rewards external geospatial drivers, plus all of the "causal or probabilistic logic" line item. The 5-page PDF doesn't exist yet. The pitch is a story without the receipts.

# Brutal Verdict

**Grade: D+ (currently mid-pack at best; one hostile judge question away from elimination).** The pipeline runs and the documentation is tidy, but the methodology is theatre: a frontier-shaped wrapper around `1.2 × historical_max`, with a submission file in the wrong schema and the highest-weighted features (POI) completely missing. Without ≥10 focused hours fixing the bugs from the research brief, replacing the constraint score, and shipping POI, this team will get politely thanked and not advance.

# What's Theatre vs What's Substance

| Theatre (looks impressive, doesn't move the needle) | Substance (actually defensible) |
|---|---|
| "Lower bound + peer frontier + constraint score" prose in `modeling_methodology.md` § 6 | Lower bound itself (`max(hist_max, jan_max, recent_3mo_max)`) — correctly conservative |
| `constraint_score = 0.75·(demand_proxy − observed_proxy) + 0.25·plateau` — fancy rank math that is mostly size-rank double-counting | Plateau term (low CV) — only honest constraint signal in the score |
| Methodology doc's bullet "model handles missing ground truth" — there is no validation strategy in the notebook, only `len(predictions)==20000` and `min ≥ 0` checks (cell ~660) | Bronze→Silver→Gold scaffolding and reusable DQ check pattern in `data_quality_report.md` — real points there |
| `^1.25` exponent on `constraint_score` — looks like calibration; is a hard-coded magic number | EDA documentation (median 164 vs p95 1308) — real story |
| `has_valid_coordinates.rank(pct=True)` inside demand proxy (notebook line ~573) — pure noise | Quarantine of 240 invalid coord + 9,606 invalid txn rows — judges will like the rejected store |
| Size uplift cap table (3.0/3.5/4.0/4.5x) — quoted with precision, sourced from nothing | Lakehouse folder structure + `rejected_records` files — partially earns the DE 40% |
| AI transparency log table "Reviewed against the original problem statement" — vague | The fact that an AI log file exists at all (most teams forget this) — partial credit toward GenAI 20% |
| Methodology doc paragraph "more defensible than a pure historical maximum baseline" | EDA's distributor + monthly breakdown table — useful business framing |

# Hidden Assumptions That Will Bite

1. **[BLOCKER]** *Submission schema is wrong.* `teamname_predictions.csv` has column `row_id`, the brief (§ Required Deliverables → table) demands `Outlet_ID`. The notebook (`predictions = predictions.rename(columns={'Outlet_ID': 'row_id'})`) makes this on purpose, citing a "platform validator" the research brief says nobody can verify exists. Cost: one-shot scoring fail.
2. **[BLOCKER]** *The 914-row file is `head(914)`.* When no template is found, notebook silently writes the first 914 sorted outlet IDs as the "platform upload". That's `OUT_00001..OUT_00914`, not a stratified sample, not a holdout, not anything justified. Pure fabrication that contradicts the brief's "estimate ... for every outlet" wording. Judges will read the notebook.
3. **[MAJOR]** *Constraint score is a size proxy.* `demand_proxy = 0.35·structural_capacity + 0.15·Cooler_Count + 0.15·mean_sku_count + 0.25·catchment_density + 0.10·has_valid_coordinates`. The first three are all monotone in outlet size; `catchment_density` is dominated by outlet counts at 1-5 km which correlate with urban→wealth→size. Result: high constraint score ↔ big, well-stocked, urban outlets, i.e. the ones with the *least* hidden potential. The "latent demand uncapping" actually points the uplift at the outlets least likely to be constrained.
4. **[MAJOR]** *Cannibalisation sign is flipped* (already in research brief). `same_type_outlet_count_2km` is rolled into `catchment_density_score` with a positive weight (notebook line ~497: `0.10 * features['same_type_outlet_count_2km'].rank(pct=True)`). Same-type outlets within 2 km are *competitors*, not demand. Easy ammo for a judge.
5. **[MAJOR]** *240 invalid-coord outlets silently teleported.* `features['Latitude'].fillna(features['Latitude'].median())` (notebook line ~440) then they participate in BallTree catchment scoring at the median lat/lon → all 240 get a fake suburban catchment density. Both the "rejected records" narrative (the same 480 rows live in `outlet_coordinates_rejected.csv`) and the constraint score lie to each other.
6. **[MAJOR]** *`uncap_weight` is capped at 0.65* (notebook line ~593: `.clip(0, 0.65)`). Even an outlet that scores 1.0 on constraint can only move 65% of the way to the peer frontier. Combined with point (3), this guarantees the "median uplift ≈ 1.20x" headline — it's not a result, it's an arithmetic consequence of the clip. The team is reverse-engineering a conservative-sounding number.
7. **[MAJOR]** *No proxy validation.* The notebook's "Final Validation" cell only checks row count, uniqueness, NaN, min, median, max. There is no: outlet-holdout, year-on-year stability (predict Jan 2025 from 2023-24, compare to actual Jan 2025), distributor-totals reasonableness vs distributor capacity, peer-group monotonicity, or Manski/SFA cross-method agreement. "No ground truth" is being used as a thought-stopper.
8. **[MAJOR]** *POI is absent.* The brief (§ Evaluation → Data Engineering → bullet "Robust web scraping or API-based external POI acquisition") and the report requirements (§ Required Deliverables → 3. PDF → "POI data acquisition approach", "POI categories", "Method used to map POIs to internal outlets") make POI a hard requirement for a meaningful score on the 40% DE bucket and a chunk of the Method 40%. `Docs/next_steps_after_eda.md` § 3 still labels POI as "biggest remaining competitive improvement". With <30h to go this is not "next steps", this is *the* step.
9. **[MAJOR]** *Causal/probabilistic logic is missing.* Brief § 3. PDF requires "Causal or probabilistic logic for estimating uncapped potential". A rank-sum score + GBM quantile fit is neither causal nor probabilistic in any rigorous sense — no DAG, no SFA, no censored regression, no bounds. Research brief § 4 listed Stochastic Frontier Analysis, Manski bounds, conformalised QR — none adopted.
10. **[MAJOR]** *Historical-max contamination.* `lower_bound = max(hist_max, jan_max, recent_3mo_max)`. One festival, one bulk wholesale month, one data-entry error → permanently inflated floor, and `final ≥ lower_bound` is hard-coded (`np.maximum(raw_potential, lower_bound)`). EDA shows transaction-level `max = 9438.578` L (single transaction) and outlet-monthly `max = 10457.94` L. The full 20k predictions file has `max = 10457.94` — *exactly* the EDA outlet-monthly max, meaning at least one outlet got zero uplift because its historical max already blew through every peer frontier. So one outlier owns the top of the prediction distribution and the framework had no protective logic.
11. **[MODERATE]** *Stale macro envelope.* Training is 2023-2025, predicting Jan 2026. Sri Lanka's 2022-23 IMF/economic collapse → 2024-25 recovery means Jan 2023 ≠ Jan 2025 ≠ Jan 2026 even ignoring outlet-level constraint. No macro deflator, no price-elasticity, no LKR/fuel adjustment. Channel 5 of the research brief literally hands them Avurudu/Poya/Vesak as cheap wins; ignored.
12. **[MODERATE]** *Arbitrary size caps.* `{Unknown: 2.0, Small: 3.0, Medium: 3.5, Large: 4.0, Extra Large: 4.5}` (notebook line ~596). No bootstrap, no domain anchor, no sensitivity analysis. Research brief § 10 explicitly recommends bootstrap-estimated caps and lowering Extra Large to 4.0x. A judge asking "why 4.5?" gets silence.
13. **[MODERATE]** *Unknown size = 2.0x cap punishes 196 missing-size rows twice.* They lose the size signal *and* get the lowest uplift ceiling. A judge will spot this in 30 seconds.
14. **[MODERATE]** *Active-month sparsity ignored.* EDA shows ~12,500 active outlets/month out of 20,000 — i.e. ~37% of the outlet universe is silent in any month. `active_months` is computed (notebook line ~408) but never enters the constraint score. An outlet with 2 active months and one good one gets a fully credible `lower_bound`. This is the censored-data problem the methodology doc claims to solve, and the code does not solve it.
15. **[MODERATE]** *9,606 transaction rejects and 4,853 negative-volume rows are never explained.* Negative volumes in a beverage trade context are usually returns / breakage / promo adjustments — direct evidence of execution constraints. Quarantining them silently is a missed forensic story worth real DE points.
16. **[MODERATE]** *AI transparency log is generic.* Eight rows of "AI suggested X / human reviewed Y" with no per-cell or per-decision validation. GenAI 20% rubric rewards "critically reviewed, tested, and validated"; this log shows attendance, not rigour.
17. **[MINOR]** *Two CSVs is a smell.* Shipping `teamname_predictions.csv` (914 rows) and `teamname_predictions_full_20000.csv` invites judges to ask "which one is real?". The brief asks for one file.

# 7 Killer Judge Questions + Defensible Answers

> Defensible answers assume the team executes the fixes — without the fixes, the answers below are aspirational, not real.

1. **"Why does your platform-upload CSV only contain 914 outlets when the brief explicitly says to estimate potential for every outlet, and where did the 914 number come from?"**
   - Defensible answer: it should be one file with all 20,000 rows and column `Outlet_ID`. The 914-row variant was a precautionary fallback before any official template was confirmed; we are dropping it. (Cost of giving any other answer: judges decide you can't read the brief.)

2. **"Walk me through one outlet where your constraint score correctly identifies a constrained outlet — not a small/wealthy/urban one — and show how your uplift reflects that."**
   - Defensible answer: an outlet with low coefficient-of-variation in monthly volume, sustained months at cooler/SKU capacity, and a frontier-residual gap (q90 SFA frontier − observed mean), where peer outlets in the same type+size cell at similar catchment density are doing 2-3x. Currently the team can't show this end-to-end — they need the SFA/frontier-residual constraint score from research brief § C8 to exist first.

3. **"Your `same_type_outlet_count_2km` is contributing positively to your demand signal — isn't that competition, not catchment?"**
   - Defensible answer: yes, sign was wrong; we split into "same-type within 200 m" (negative, cannibalisation) and "all-type within 2 km" (positive, foot traffic), as the research brief recommends.

4. **"You claim historical sales are censored. Where in your code do you actually model the censoring? Show me the likelihood or the bounds."**
   - Defensible answer: today, nowhere — only a lower bound + heuristic uplift. Defensible plan: Stochastic Frontier Analysis (`y = f(X) − u`, `u ≥ 0`) gives a closed-form `TE = exp(−E[u|ε])` constraint estimate; Manski bounds `[lower, upper]` give the honest identification disclosure. Without those, you cannot defend the word "censored" in your methodology doc.

5. **"You're predicting Jan 2026 from 2023-25 data covering the IMF crisis and recovery. How does your model handle the macro level shift?"**
   - Defensible answer: distributor-level monthly seasonality index + explicit Avurudu/Poya/Vesak features + price-per-litre deflator + active-month decay weighting recent months heavier. Currently: nothing — `target_jan_seasonality_score` is a single distributor-month average ignoring year.

6. **"Where are your POI features? Schools, hospitals, transport hubs?"**
   - Defensible answer: they have to exist by submission. Geofabrik LK PBF + pyrosm extraction (research brief § 7) is a ~25-min pipeline. If the team ships without it, the answer is "we ran out of time" — instant downgrade against any team that did ship it. There is no defensible "we chose not to" answer.

7. **"Your maximum uplift caps are 3.0×, 3.5×, 4.0×, 4.5× by size. Where does that come from? Why not 5×? Why not 2.5×?"**
   - Defensible answer: bootstrap the 99th-percentile uplift in each size bucket from the q90/q50 ratio of comparable peers and round to the nearest 0.25. Today: vibes. Without a number-backed answer this question lands as "you guessed", which is a methodology rubric kill.

# Pre-mortem — Three Specific Ways This Lands at B or Worse

1. **"Disqualification by formatting."** Submission day, judges' validator script rejects `row_id` column or refuses the 914-row variant against a brief that says all outlets. Predictions are excluded from scoring; the team is graded only on report + code. Probability: HIGH if they ship today.

2. **"Methodology unmasked in viva."** Judges open the notebook, see `0.75 * gap + 0.25 * plateau`, `^1.25`, `clip(0, 0.65)`, and `head(914)`. One judge asks for the formal name of the latent-demand framework being used (Tobit? SFA? Heckman?). The team has no answer. The 1.20× median uplift is shown to be the mechanical consequence of the 0.65 clip × 1.25 exponent. Method 40% score collapses to ~50%. Probability: HIGH if SFA/frontier-residual is not added.

3. **"POI no-show."** Half the field ships some form of OSM POI features; the team ships none. DE 40% score is capped because the rubric explicitly rewards "Robust web scraping or API-based external POI acquisition" and "POI categories used as catchment demand drivers". Even with a beautiful Bronze/Silver/Gold and rejected store, the team is penalised one full grade. Probability: HIGH given POI is still "next step" with <30h remaining.

# Honest Strengths (credit where due)

1. **Documentation is actually written.** `challenge_brief.md`, `modeling_methodology.md`, `data_quality_report.md`, `eda_summary.md`, `next_steps_after_eda.md`, `ai_transparency_log.md`, `folder_structure.md` all exist and are reasonably clear. Most hackathon teams ship a notebook + a panicked README. The team is in much better shape on the *report-writing surface area* than peers.

2. **Bronze/Silver/Gold + rejected records is real.** The notebook does quarantine 240 invalid coords and 9,606 bad transactions into named files, and the DQ report table is parameterizable. That's exactly what the DE 40% rubric is asking for; the bar is not high among hackathon submissions and this clears it.

3. **EDA is genuinely informative.** The monthly time series (35 rows × 7 cols across 2023-2025), distributor breakdown, SKU breakdown, and size×cooler matrix in `eda_summary.md` are the kind of business framing that scores well in viva. Treat this as a moat — most teams will not produce this depth in 36 hours.

4. **They have a research brief.** Channels 1-10 in `research/research_brief.md` already identify the bugs, the SFA/Manski/CQR upgrade path, the Geofabrik POI playbook, and the LK-domain calendar features. The cost of going from D+ to B+ is *executing the brief they already wrote*. The intellectual work is done; the engineering work is not.
