# AI Council Review — Master Synthesis

**Reviewers (parallel premium models):**
1. Statistician (`01_statistician.md`) — Claude Opus 4.7 thinking xhigh
2. Skeptic (`02_skeptic.md`) — Claude Opus 4.7 thinking xhigh
3. Methodology Architect (`03_methodology_architect.md`) — GPT-5.5
4. Safety + DE Reviewer (`04_safety_and_de.md`) — GPT-5.5

**Date:** 2026-05-15, T-30h to comp start at 06:00.

---

## Convergent Verdict

| Reviewer | Grade today | Grade after fixes |
|---|---|---|
| Statistician | C− | B+ |
| Skeptic | D+ | B+ |
| Methodology Architect | B− | A− |
| Safety + DE | D+ | B− |
| **Consensus** | **D+ / C−** | **B+** |

**One-line verdict:** *The pipeline runs and the docs read well, but the methodology is mostly theatre and the submission file has self-inflicted blockers. The fix list is concrete and finishable inside the 36-hour window — but only if execution starts on hour 1.*

---

## BLOCKERS (must fix before anything else — total ~1h 45m)

These were independently flagged by 3+ reviewers. **The submission can be auto-rejected over these.**

| # | Blocker | Severity | Time | Source |
|---|---|---|---|---|
| B1 | `Results/teamname_predictions.csv` has column `row_id` instead of `Outlet_ID` (per official PDF) | DISQUALIFY | 5 min | All 4 |
| B2 | Submission is `head(914)` from the full file. The 914-row "platform validator" assumption is unverified. Brief asks for predictions for the 20,000 outlets in scope. | DISQUALIFY | 10 min | Skeptic, Safety |
| B3 | `data/silver_rejected/` is empty in the current tree (only `.gitkeep`); rejected-records store is invisible to a reviewer | -10 to DE rubric | 20 min | Safety |
| B4 | `src/cleaning/`, `src/features/`, `src/poi/`, `src/modeling/` etc. are EMPTY (.gitkeep only). All logic lives in one notebook. Rubric explicitly demands a "cleanly structured codebase reflecting B→S→G separation". | -10 to DE rubric | 60 min (minimal extract) | Safety, Architect |
| B5 | No external POI data exists yet. Per the official PDF, POI is mandatory and explicitly judged. | -25 to combined DE+Method | 4–6h (separate task) | Skeptic, Architect, Safety |

---

## CRITICAL METHODOLOGY DEFECTS (same finding from 2+ reviewers)

These are **substantive math problems** with the existing model. Each one reduces the Methodology score.

### M1. The "1.20× median uplift" is mechanically forced — not learned
*Statistician + Skeptic, independently.*

The chain `^1.25` exponent → `clip(0, 0.65)` cap on uncap_weight → 4.5× size cap → peer p98 × 1.35 = **quadruple throttling**. Even if the constraint score correctly identified an outlet as 100% constrained, the prediction can never reach the peer frontier. The headline "median uplift 1.20×, mean 1.37×" is therefore a property of the formula, not of the data.

**Fix:** drop the `clip(0, 0.65)`, drop one of the two outer caps, and *calibrate* the exponent (or replace with a simple linear interpolation) on a held-out outlet bootstrap.

### M2. `constraint_score` is a re-labelled "outlet bigness" score
*Statistician + Skeptic, independently.*

Components: 35% structural_capacity + 15% cooler + 15% SKU breadth + 25% catchment + **10% `valid_coordinate_rank` (a data-quality flag)**. The first four are highly correlated indicators of *size and wealth*, not of *being constrained below true demand*. The fifth is a DQ artifact that has no business being in a demand model.

**Net result:** uplift flows to outlets that are already big — the opposite of what the brief asks for.

**Fix (per research brief + Statistician + Skeptic):** replace the rank-sum with:
- Frontier residual: `(peer_q90_volume − observed_max) / sd(peer)` z-score
- Plateau gate: months-since-new-max + variance-of-recent-12 indicator
- PCA-decorrelated capacity component
- Calibrate weights via supervised proxy label (not the hardcoded `^1.25`)
Drop `valid_coordinate_rank` entirely — it goes to the data-quality report, not the model.

### M3. `lower_bound` is dominated by `historical_max`
*Statistician.*

`max(historical_max, january_max, recent_3mo_max)` collapses to ≈ `historical_max` for ~all outlets (since historical_max is by definition ≥ the other two). One bad month (festival spike, data error, holiday glitch) becomes the permanent floor for that outlet. Worst case: max prediction = 10,457.94 L (= EDA outlet-monthly max from a single outlier).

**Fix:** use a robust lower bound — e.g., 3rd-highest month, or 95th-percentile of the outlet's own history with at least 6 months of data. Drop `january_max` and `recent_3mo_max` (they're already inside `historical_max`).

### M4. q90 is fitted on capped sales (downward-biased frontier)
*Statistician — direct flag from research brief Channel 1.*

Training the 90th-percentile model on `y_obs = min(true, constraint)` makes `q90(y_obs) ≤ q90(y_true)`. The "frontier" is therefore a lower bound on the real frontier.

**Fix:** Chernozhukov-Hong 3-step censored quantile regression: fit a δ-propensity model on plateau/stockout proxies → refit q90 only on rows where `P(censored) < 0.10`. Or: switch to SFA (Channel 2) which models the censoring explicitly.

### M5. No validation, no sensitivity, no robustness check
*Statistician + Skeptic + Architect.*

Zero held-out outlets. Zero year-on-year backtest. Zero sensitivity analysis on the four free knobs (`^1.25`, `clip(0.65)`, 4.5x cap, p98×1.35). Zero Manski upper-bound sanity comparison. The model is a single point estimate with no defensibility evidence. **This alone caps the Methodology score around C.**

**Fix:** see Architect's 6-item validation checklist below.

---

## Architect's Recommended Minimal Stack (don't over-engineer)

The research brief recommends 5+ methods. The Architect — correctly — pushes back: **for 36 hours, ship 4, not 8.**

```
Final method:
  1. POI features (Geofabrik PBF + pyrosm)         ← required, biggest lift
  2. Manski-bounded frontier (the report spine)    ← cheap honesty
  3. ONE frontier model (XGBoost q90 multi-quantile + Conformalized QR)
  4. Calibrated constraint score (frontier-residual + plateau + PCA)

Final formula:
  potential = lower_bound  +  constraint_score * (frontier - lower_bound)
              [bootstrap shrinkage toward peer median when binding]

Reported as:
  potential ∈ [Manski_lower, point_estimate, Manski_upper]
```

What we are NOT shipping (and saying so in the report):
- DEA — too slow on 20k DMUs, no noise term.
- Heckman — no exclusion restriction available.
- Two-Tier SFA — no mature Python lib; 150 LOC is too risky in 36h.
- Causal Forest CATE — fancy but not on the critical path.

This is **fewer methods done well** vs **many methods done badly**. The Skeptic explicitly warned about "winner-pleasing fluff that doesn't answer the business question".

---

## 36-Hour Plan (consensus across reviewers)

| Block | Hours | Owner | Deliverables | Gate |
|---|---|---|---|---|
| 0–1 | First hour | All | Bug fixes B1–B3; refactor 60% of notebook into `src/` modules per Safety review | If B1+B2 not done by hour 1 → STOP, fix |
| 1–7 | 6h | One person | POI pipeline (Geofabrik PBF → pyrosm → ~54 features → `data/gold/poi_features.parquet`) | If POI not loaded by hour 5 → fall back to Overpass live with reduced radii |
| 1–4 | 3h (parallel with POI) | Other person | Replace `constraint_score` with PCA + frontier-residual + plateau composite (M2 fix). Drop `valid_coordinate_rank`. | If composite doesn't behave monotonically → revert and just remove `valid_coordinate_rank` |
| 4–7 | 3h | Same | Fix `lower_bound` (M3) + drop quadruple throttle (M1) + add Chernozhukov-Hong censoring correction (M4) | Sanity: median uplift ≥ 1.4× after fixes |
| 7–10 | 3h | Either | Fit SFA via `pySFA` or `FronPy` as second method track; report inefficiency drivers | Optional — if behind, skip |
| 10–14 | 4h | Either | Switch q90 to XGBoost 2.0 multi-quantile + Conformalized QR via MAPIE | |
| 14–18 | 4h | Either | Add Manski bounds + DAG section to report. Add 6-item auto-validation checklist (see below). | |
| 18–24 | 6h | Both | Write 5-page PDF report (cover + forensics + POI + causal logic + GenAI log) | If POI section thin → priority |
| 24–30 | 6h | Both | Iterate on report based on Council fix-list; manual audit of top-100 uplift outlets | |
| 30–36 | 6h | Both | Final submission package (CSV + zipped repo + PDF). Buffer for last-minute issues. | NO new methods after hour 30 |

**Hard gate at hour 18:** if the report is < 50% drafted, STOP all method work and write the report. The deliverable is judged, not your code.

---

## 6-Item Auto-Validation Checklist (Architect)

These should be in the notebook and run automatically:

| # | Check | Pass threshold |
|---|---|---|
| V1 | `Outlet_ID` column present, no duplicates, 20,000 rows | exact match |
| V2 | `Maximum_Monthly_Liters` > 0 for every row, no NaN | 100% |
| V3 | `predicted >= historical_max` for every outlet (predict ≥ observed evidence) | ≥ 99% |
| V4 | Median uplift ratio in [1.2x, 2.0x] (not too tame, not absurd) | within range |
| V5 | Cap-binding rate per size bucket < 25% | yes |
| V6 | Year-on-year stability: predictions correlate ≥ 0.85 with predictions trained on 2023-only data | ≥ 0.85 |

---

## Submission Pre-flight Checklist (Safety)

Before the team uploads anything:

- [ ] `teamname_predictions.csv` has columns exactly `Outlet_ID, Maximum_Monthly_Liters`
- [ ] 20,000 rows (or whatever the official portal demands — verify on the day)
- [ ] No NaN, no negatives, no duplicate `Outlet_ID`
- [ ] All `Outlet_ID` values exist in `outlet_master.csv`
- [ ] Column dtype: int/string for ID, float for liters
- [ ] No leading/trailing whitespace in headers
- [ ] No BOM, UTF-8 encoded
- [ ] File size < 10 MB
- [ ] Repo zip < 100 MB (no `Datasets/` or `data/bronze/` in zip)
- [ ] README has `pip install -r requirements.txt` + run instructions tested on a fresh venv
- [ ] PDF is exactly 5 pages incl. cover, all 4 mandatory sections present
- [ ] GenAI transparency log timestamps cover the entire 36h

---

## 7 Killer Judge Questions (Skeptic predicted these — prepare answers now)

The Skeptic's review predicted what a hostile judging panel will ask. The team should rehearse answers:

1. *"Why is your median uplift only 1.20×? Are you actually uncapping anything?"*
   → After fixes M1+M3 it should be 1.4–1.7×. Show before/after distributions.
2. *"Your constraint score correlates 0.85 with outlet size — isn't this just predicting that big outlets get more uplift?"*
   → After M2 fix the correlation should drop to ~0.3. Show the ranked correlation table.
3. *"What's your assumption about right-censoring? Are you correcting for the bias?"*
   → Cite Chernozhukov-Hong 2002. Show the propensity-model results.
4. *"Where did the 4.5× cap come from?"*
   → After M1 + bootstrap-cap fix, cite the empirical 95th-percentile uplift in size-type peer buckets.
5. *"How did you scrape POIs at scale?"*
   → Geofabrik PBF + pyrosm. Show the wall-clock + cited Channel 4 of research brief.
6. *"Without a holdout, how did you validate?"*
   → 6-item auto-validation checklist + year-on-year stability + Manski-band sanity. (Currently NONE of these exist — fix on the day.)
7. *"How is this different from a pure historical-sales baseline?"*
   → Manski lower bound = baseline. Show that 60%+ of outlets receive nonzero uplift driven by POI evidence.

---

## What the Team Got RIGHT (credit where due)

- Real Bronze → Silver → Gold structure with rejected records intent (480 coord, 9606 txn).
- Reusable DQ check categories chosen well (duplicate, null, range, referential, domain).
- Genuine EDA with substantive findings (Grocry/Bakry artifacts, lowercase `small`, holiday duplicates, monthly seasonality patterns).
- Internal catchment features built with correct math (BallTree haversine).
- AI transparency log started (just needs running discipline, not a redesign).
- Comprehensive `research/research_brief.md` already names every fix.
- Lakehouse intent + size cap concept are defensible *narratives* — they just need data-driven calibration.

---

## Open Decisions (council deferred to team)

| Decision | Default | Conditions to override |
|---|---|---|
| Drop SFA from minimal stack? | Keep IF time allows after hour 7 | Drop if POI runs late or composite constraint score is unstable |
| Manski bounds — wide or narrow assumptions? | Wide (use full historical range as upper) | Narrow only if the team can defend a tight assumption in viva |
| Submit single point estimate or interval? | Submit point estimate (CSV is single column); interval lives in the report | If portal allows, submit point + add interval as separate column |
| Refactor `src/` minimally or fully? | Minimally (extract DQ + POI + modeling — 3 files, 60 min) | Fully only if hour 24 still has >2 free hours |

---

## Aggregate Cost & Effort

- Council reviews: 4 premium-model subagents in parallel + this synthesis ≈ ~$10–25 (Cursor-billed; not from your `BUDGET_USD`).
- Research swarm: 10 premium-model subagents ≈ ~$30–60.
- **Total spent on planning so far: ~$40–85.**
- Remaining 36 hours: zero LLM cost required; everything is engineering. Budget LLM use for: in-the-moment debugging help, report drafting, and the GenAI workflow demonstration itself (which is part of the 20% rubric — so log it).

---

## Single Most Important Sentence

> **Fix the CSV format and the constraint-score double-counting in hour 1, ship the POI pipeline by hour 7, hold the report deadline at hour 30, and the team moves from D+ to B+.**

---

## Pointers

- Full research brief: `competition/research/research_brief.md`
- Per-channel research: `competition/research/0[1-9]_*.md` and `10_*.md`
- Per-critic reviews: `competition/Reviews/0[1-4]_*.md`

The team should now read the four critic files (1–2 min each) for the line-cited details, then start hour 1.
