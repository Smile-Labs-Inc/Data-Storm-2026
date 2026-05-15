# TL;DR

- Make the story one pipeline: `observed sales are a censored lower bound -> POI + outlet features explain demand -> SFA/quantile frontier estimates the ceiling -> Manski bounds and auto-checks control overclaiming`.
- Ship a minimal stack, not a methods zoo: Manski bounds, external POI catchment, one frontier estimator, and one calibrated constraint score. Drop causal forest and deep Tobit unless everything else is finished.
- Fix correctness first: the submission shape, coordinate teleporting, same-type sign, and invalid `valid_coordinate_rank` issue are on the critical path before any modeling upgrade.

# Verdict on Coherence

**Grade: B-.** The current pipeline has strong data engineering bones, but the methodology still reads like a smart heuristic wrapped around a weakly defined constraint score; adding POI and replacing the heuristic with a named frontier-plus-bounds architecture would move it to A-range.

# End-to-End Arc Diagram

```text
CURRENT STATE
[No true target]
  -> [Bronze/Silver DQ]
  -> [Internal outlet + sales features]
  -> [Rank-sum constraint_score]
  -> [q90/peer frontier]
  -> [Caps + 914/20k outputs]
  -> [Loose validation]

PROPOSED STATE
[Latent demand = censored lower-bound problem]
  -> [Bronze/Silver forensics + rejected reasons]
  -> [Gold = internal + POI + cannibalization + domain features]
  -> [Manski lower/upper bounds]
  -> [SFA or censored q90 frontier + calibrated constraint probability]
  -> [Evidence-based caps + full 20k output]
  -> [Auto-validation report + report figures]
```

# Methodology-to-Rubric Map

| Rubric question | Current answer | Strength of answer | Improvement |
| --- | --- | --- | --- |
| How is Latent Potential conceptualised? | `lower_bound + constraint_score^1.25 * (peer_frontier - lower_bound)` where observed history is a floor and peer frontier is the ceiling. | **Medium.** The lower-bound idea is right, but the score is ad hoc and the exponent is not justified. | Define latent potential as `Y* = D`, with `Y_obs = min(D, C)`. Report `[Manski lower, point estimate, Manski upper]`, not just one number. |
| What math handles missing target? | No supervised target; uses historical max, q90 frontier, peer percentiles, and caps. | **Medium.** Practical, but judges can call it engineered blending. | Add SFA or Chernozhukov-Hong censored q90 as the point-estimate engine. Use conformal or bootstrap intervals as uncertainty evidence. |
| What math handles censored data? | Assumes high peer/frontier sales reveal uncapped potential; constraint score moves outlets upward. | **Weak-to-medium.** Correct direction, weak identification story. | State non-identification. Then use Manski bounds, monotone response, and SFA inefficiency `u >= 0` or censored quantile filtering. |
| Is final uncap commercially defensible? | Size caps, peer p98 cap, no negatives, no missing predictions, conservative uplift. | **Medium-high.** Guardrails are sensible. | Make caps empirical by `Outlet_Size x Outlet_Type` bootstrap, lower Extra Large max to `4.0x` unless supported, and report cap-binding rate. |
| Are external demand drivers included? | Internal catchment only; no external POI yet. | **Weak.** This is a rubric miss. | Add Geofabrik/OSM POI features to Gold with counts, nearest distance, decay scores, and cannibalization features. |

# Minimal Impressive Stack

The research stack of SFA + Quantile GBM + Manski bounds + Conformalized QR + causal sensitivity is too many methods for 36 hours. It will look unfocused unless each method has a clear role.

Ship this **4-part minimal stack**:

| Method | Role | Why it earns Methodology marks | Ship rule |
| --- | --- | --- | --- |
| **Manski bounds** | Honest identification frame: `lower = historical max`, `upper = empirical peer/cap frontier`. | Directly answers "missing target" and "not point-identified." Very high narrative ROI. | Must ship. Costs little. |
| **External POI catchment Gold layer** | Demand-side evidence: schools, transport, markets, eateries, hospitals, offices, religious, hotels, supermarkets. | Moves method from internal sales extrapolation to market potential estimation. | Must ship. This is also Data Engineering evidence. |
| **One frontier estimator: SFA if stable, censored q90 GBM if not** | Point estimate of uncapped ceiling. | SFA gives the cleanest `frontier - inefficiency` math; censored q90 is the fastest robust fallback. | Time-box SFA to 3 hours. If unstable, lead with censored q90. |
| **Calibrated constraint score** | Probability/degree of under-realisation. | Replaces rank-sum with frontier residual + plateau + decorrelated capacity + SFA/QR signal. | Must replace `^1.25` heuristic. |

Do **not** ship causal forest, deep Tobit, full two-tier SFA, or Heckman in the main pipeline. They are either too fragile, need unavailable assumptions, or distract from the central story.

# 5-Page Report Section Budget

Assume one cover page, leaving four real pages. Use dense visuals, short text.

| Section | Pages | Paragraphs / charts | Headline figure | What NOT to include |
| --- | ---: | --- | --- | --- |
| Cover + one-line thesis | 1.0 | 1 thesis sentence, team info, one mini pipeline strip | `Observed = min(demand, constraint)` banner | Long background or generic hackathon text |
| Forensics and lakehouse | 0.8 | 2 paragraphs, 2 charts | Rejected-record waterfall: Bronze -> Silver -> rejected coordinate/transaction reasons -> Gold rows | Full DQ rules table; put it in appendix/codebase |
| POI and catchment demand | 0.8 | 2 paragraphs, 1 map/table | Map or bar chart of POI demand score by province/type, plus example outlet catchment | Raw OSM query dumps, 50 feature names |
| Latent-demand math | 1.1 | 3 paragraphs, 2 charts | Bounds-and-frontier chart: lower bound, point estimate, upper bound for sample outlets | Five model names. Lead with one estimator and one fallback only |
| Validation and business action | 0.8 | 2 paragraphs, 2 charts | Auto-validation scorecard plus top-uplift outlet audit scatter | Leaderboard-style claims or "accuracy" without ground truth |
| GenAI workflow | 0.5 | 1 paragraph, 1 mini flow | AI usage audit: generated -> reviewed -> tested -> accepted/rejected | Prompt dumps; show human validation, not raw chat |

# 6-Item Auto-Validation Checklist

The pipeline should write these to a markdown/CSV validation report on every run.

| Check | Pass/fail threshold | Why it matters |
| --- | --- | --- |
| **Lower-bound respect** | `100%` of predictions must be `>= historical_max_monthly_liters`; hard fail if any violation. | Potential cannot be below demonstrated capability. |
| **Full-output completeness** | Full business file has exactly `20,000` unique outlets and no null/negative predictions; platform file must be derived from an official template if using `914` rows. | Avoids submission ambiguity and row-count errors. |
| **Monotonicity sanity** | Within each outlet type, median prediction must be non-decreasing from Small -> Medium -> Large -> Extra Large, allowing at most one adjacent inversion under `2%`. | Judges expect larger outlets to have higher capacity. |
| **Cap-binding rate** | Share of outlets at final cap `< 7%`; share of total liters from capped outlets `< 15%`; no size-type bucket has `> 20%` cap binding. | If caps dominate, the model is not really estimating potential. |
| **Peer-frontier coverage** | At least `95%` of point estimates must lie inside `[Manski lower, Manski upper]`; any breach goes to manual review. | Keeps the point estimate inside the stated identification set. |
| **Stability and reasonableness** | Total predicted liters changes `< 8%` under `3x` vs `4x` caps, median uplift between `1.10x` and `1.70x`, and p99 uplift `< 3.0x` unless explicitly flagged. | Prevents fragile cap-driven outputs and wild tail behavior. |

# 36-Hour Gantt with Gates

| Time | Work | Output | Gate |
| --- | --- | --- | --- |
| **0-6 h** | Fix blockers: submission column/name, choose 20k as canonical business file, remove lat/lon median teleport, flip same-type sign, remove `valid_coordinate_rank` from `constraint_score`. | Clean rerun with valid outputs and fixed Gold features. | If not clean by hour 6, freeze modeling upgrades and finish correctness first. |
| **6-12 h** | Build POI module from Geofabrik/OSM PBF or HDX extract. Add counts at 250/500/1000/2000m, nearest distances, decay scores, and POI demand score. | `data/gold` POI feature table joined to outlet model frame. | If PBF tooling fails by hour 10, use HDX OSM CSV/GeoJSON export or a province-level Overpass bbox fallback. |
| **12-18 h** | Replace constraint score: decorrelated capacity PC1, frontier residual, plateau flag, cannibalization, POI demand gap. Add empirical caps by size/type. | New `constraint_score_v2`, cap table, diagnostics. | If behind by hour 18, drop SFA and keep censored q90 + Manski. Do not drop POI. |
| **18-24 h** | Fit point estimator: SFA time-box first; if unstable, fit XGBoost/LightGBM q90 with monotone constraints and CH-style filtered training. Add Manski bounds. | Point estimate and interval columns per outlet. | If SFA residuals/skew look wrong after 3 hours, demote it to robustness note. |
| **24-30 h** | Run auto-validation and sensitivity: cap scenarios, frontier coverage, monotonicity, cap-binding, top-uplift map/manual audit. | Validation scorecard and report-ready figures. | If any hard fail remains at hour 30, fix outputs, not aesthetics. |
| **30-36 h** | Final CSV, code cleanup, 5-page PDF, AI transparency log, README/run steps. | Submission package. | If report is not done by hour 33, cut extra methods and protect the story: forensics -> POI -> bounds/frontier -> validation. |

# The One Change That Matters Most

**Add an explicit Manski-bounded frontier architecture and make it the spine of the report.**

This is the biggest Methodology lift because it answers the real judging question: not "which model did you train?" but "how can you estimate a missing, censored target without pretending it is observed?" The team should output three columns internally: `lower_bound`, `point_potential`, and `upper_bound`. The CSV can still submit the point estimate, but the report should show the bounds.

The best final story:

```text
Observed history gives a lower bound.
POI + outlet features define comparable demand context.
SFA/censored q90 gives the point frontier.
Empirical peer caps give the upper bound.
Auto-validation proves the point estimate stays inside the bounds.
```

# The One Change to AVOID

**Do not add five advanced methods and call it an ensemble.**

A bloated stack of SFA, causal forest, Heckman, DEA, deep Tobit, CQR, and hand-coded two-tier SFA will hurt the score because it signals panic, not methodology. Judges will ask which assumption identifies latent demand, and the team will have no clean answer. One coherent bounded-frontier method beats six disconnected tricks.

# Critical Bug Sequence

Fix these before any modeling extension:

| Order | Bug | Why this order |
| ---: | --- | --- |
| 1 | Resolve submission schema and row count: use `Outlet_ID` vs `row_id` only according to the official template, and make the 20k file canonical for the business deliverable. | Wrong output shape can fail submission or confuse judges. |
| 2 | Stop coordinate teleporting. Invalid coordinates should get no spatial features or distributor-level derived-feature imputation, never median lat/lon. | Bad spatial features poison POI and catchment modeling. |
| 3 | Flip same-type outlet logic from positive demand to cannibalization. | This changes model direction, not just cosmetics. |
| 4 | Remove `valid_coordinate_rank` from `constraint_score`. | A DQ flag is not a demand or constraint signal. |
| 5 | Recompute `constraint_score` and final predictions after the above fixes. | The core formula depends on all previous signals. |

# POI Module Principles

- **Gold owns outlet-level features.** Raw OSM/PBF extracts belong in Bronze, cleaned POIs in Silver, and one row per outlet POI features in Gold.
- **Use local extraction, not 720k live API calls.** Prefer Geofabrik/HDX Sri Lanka data and BallTree/geopandas joins. Keep Overpass snippets as evidence, not the main runtime path.
- **Separate demand, competition, and confidence.** Schools, transport, markets, offices, hospitals, eateries, religious sites, hotels are demand signals. Same-type and supermarkets nearby are cannibalization. Invalid coordinates are confidence flags.
- **Make every feature auditable.** Each POI category needs a tag definition, count radius, nearest-distance default, and missing-coverage caveat.
- **No target leakage.** Do not use neighboring outlets' observed liters as a POI/catchment feature unless computed out-of-fold.
