# TL;DR

- **Do not ship either report as-is.** Ship a merged, rebuilt PDF using `Reports/final_report.md` as the canonical v2 spine, with only the still-true v1 readability and forensics numbers carried across.
- **The viva can win if it is honest:** "sales are a floor, not demand" is strong. But the current package has a credibility bomb: v2 validation says `V3b FAIL` and `V4 FAIL`, while the report text implies pass.
- **The team must retire the v1 PDF and stale docs before judges see them.** The `914 rows / row_id / 1.18x` story contradicts the official `20,000 rows / Outlet_ID` story.

# Which Report to Ship

**Verdict: merge, but v2 is the canonical report.** Do not ship `Docs/final_report.pdf` as-is: it is readable, but it tells the wrong submission story (`row_id`, 914 rows, 1.18x median uplift, Overpass-on-target-set). Do not ship `Reports/final_report.md` as-is either: it has the right 20,000-row schema and stronger methodology, but it still contains placeholders and claims validation will pass while `Results/validation_report.md` currently says two core checks fail. The only defensible move is to rebuild the final PDF from the v2 markdown after the release gate is green, then merge in the v1 report's simple business wording and concrete forensics counts. Judges will forgive a conservative model. They will not forgive two official-looking reports that disagree.

# 3-Slide Viva Pitch

## Slide 1: Historical Sales Are Not Market Potential

**Headline / chart:** `20,000 outlets, 2.37M transactions; median observed max = 164 L vs 95th percentile = 1,307.9 L` using `Reports/figures/eda_frontier_gap.png`.

**Presenter says:**

- "The business problem is not forecasting next month's sales. It is finding outlets where observed sales are capped by credit, stock, delivery, cooler space, or execution."
- "We use historical maximum as a hard floor because an outlet has already proven it can sell that much."
- "The wide peer spread tells us why potential-based allocation can beat history-based allocation."

**Why this wins points vs the obvious alternative:** The obvious alternative is opening with the model stack: SFA, quantile regression, Manski, CQR. That loses business leaders in 30 seconds. This slide starts with John Keells' resource-allocation problem: where should coolers, trade spend, and distributor attention go?

## Slide 2: A Guarded Uncap, Not a Black-Box Forecast

**Headline / chart:** `Release-gate target: 0.00% below historical max; median uplift >= 1.25x after the v4 fix` using `Reports/figures/eda_constraint_uplift.png`.

**Presenter says:**

- "Every prediction is anchored at or above demonstrated historical capability. We do not ask the business to believe an outlet's potential is below what it already achieved."
- "The model only moves above the floor when the outlet has constraint evidence: peer-frontier gap, plateau behavior, capacity, catchment, and POI signals."
- "We cap the upside by peer buckets and report bands, because latent demand is not directly observed."

**Why this wins points vs the obvious alternative:** The obvious alternative is claiming the model "finds true demand." That is indefensible. This framing sounds mature: the model produces a bounded business estimate with audit checks, not fake certainty.

## Slide 3: Turn the Model Into an Action List

**Headline / chart:** `Top-100 uplift outlets: 11% likely censored vs 1.16% population` using `Reports/figures/eda_top100_sanity.png`.

**Presenter says:**

- "The top uplift list is not random. It is enriched for constrained outlets and lower observed-max stores with headroom."
- "The model points the field team to specific actions: check stockouts, credit limits, cooler availability, and distributor execution before spending blindly."
- "This gives John Keells a ranked intervention queue, not just a CSV."

**Why this wins points vs the obvious alternative:** The obvious alternative is ending on accuracy metrics. There is no true latent-demand label, so accuracy talk invites attack. This slide lands the commercial value: where to act Monday morning.

# 5 Hostile Judge Questions

## 1. "Your validation report says 27.92% of predictions are below historical max. Why should we trust this?"

**30-second answer:** "You should not trust that package until the release gate is green. The current v2 validation exposed a packaging/model-output issue, not a business-story issue. Our final submission must floor predictions at observed historical maximum, use floor-preserving export rounding, rerun validation, and only then rebuild the PDF. If the validation report does not show pass, we should not claim pass."

**Trap if answered wrong:** If the team says "it passes" while the file says `FAIL`, the room stops listening. This is not a small bug. It attacks the core promise that potential cannot be below proven sales.

## 2. "Is your 1.25x median uplift just hardcoded to pass your own validation?"

**30-second answer:** "The 1.25x is not a hidden model discovery. If used, it must be presented as a transparent business floor for outlets the constraint score flags as constrained, and it remains below empirical peer-bucket caps. The honest claim is: we use model evidence to identify constrained outlets, then apply a conservative minimum uplift so the model does not collapse to historical max for most of the panel."

**Trap if answered wrong:** Do not say "the model learned exactly 1.25x." That sounds fake. Call the floor a policy guardrail informed by model evidence and caps.

## 3. "Why use POI data if your own docs show POI score is zero or weakly correlated?"

**30-second answer:** "POI is a catchment context signal, not a causal proof. The stale v1 validation summary showing `poi_demand_score = 0.0` should not be in the final judging pack. In the final story, POI must be described modestly: it supports local-footfall context, while the model still relies on observed history, peer frontiers, capacity, and constraints. If the final run shows weak POI lift, we say that honestly."

**Trap if answered wrong:** Overselling POI as the magic driver is dangerous. A data-science judge will ask for correlation or ablation and expose it.

## 4. "Where is your ground truth for true potential?"

**30-second answer:** "There is no clean ground truth. That is the point of the challenge. We treat observed sales as a censored lower bound, estimate a comparable peer frontier, and defend the gap using constraints and guardrails. We are not claiming perfect truth; we are producing a ranked, bounded estimate for business allocation."

**Trap if answered wrong:** Do not call this a supervised accuracy problem. There is no actual `true_potential` label.

## 5. "Which file is the official submission: the 914-row `row_id` file or the 20,000-row `Outlet_ID` file?"

**30-second answer:** "The challenge brief asks for `Outlet_ID, Maximum_Monthly_Liters` for the outlet universe, so the canonical business submission is the 20,000-row `Outlet_ID` file. The old 914-row `row_id` file came from platform ambiguity and must be archived so it cannot be uploaded or cited by mistake."

**Trap if answered wrong:** Saying "both are fine" is a disqualification risk. Judges and upload scripts need one canonical file.

# The Business Framing Sentence

Our model treats observed sales as **a hard lower bound on constrained demand**, and predicts the gap to **a comparable outlet peer frontier**, defending the gap with **constraint evidence, catchment signals, peer caps, and validation guardrails**.

# GenAI Story for the Pitch

Pitch GenAI as a controlled engineering workflow, not as authorship. Say that AI was used in three disciplined roles: a research assistant to map possible methods, a coding accelerator to scaffold reusable checks and pipelines, and an adversarial reviewer to find bugs across multiple council rounds. The team did not accept AI output blindly: every claim had to map to a file, every code change had to run, and every final number had to come from validation artifacts rather than prose. The best proof is that the AI reviews found uncomfortable failures in the team's own work; that is exactly how responsible AI should be used in a data competition.

# v1 Docs Retirement Plan

| File | Keep / archive / merge | Why |
|---|---|---|
| `Docs/final_report.pdf` | Archive | It tells the v1 story: 914 rows, `row_id`, 1.18x median uplift, and platform fallback. This directly conflicts with the v2 20,000-row `Outlet_ID` submission. |
| `Docs/final_report_draft.md` | Archive after merge | Keep only the clear wording. The deliverable schema and numbers are stale. |
| `Reports/final_report.md` | Merge / canonical | Use this as the final report spine, but only after validation passes and placeholder numbers are replaced. |
| `Docs/ai_transparency_log.md` | Archive | It is the shorter v1 log and does not capture the council audits and v2 method trail. |
| `Docs/ai_transparency_log_v2.md` | Keep / merge | This is the stronger GenAI story. Use it in the PDF and viva. |
| `Docs/model_validation_summary.md` | Archive or regenerate | Current numbers show 914-era/stale behavior and `poi_demand_score = 0.0`; it conflicts with the intended v2 story. |
| `Results/validation_report.md` | Keep, but must be green | This is the real release gate. Do not hide it. Fix the run until it passes. |
| `Docs/modeling_methodology.md` | Merge carefully | It has good plain-language framing, but stale caps, 914 notes, and older methodology details must be removed. |
| `Docs/poi_enrichment.md` | Archive or rewrite | It describes the older 914-row Overpass workflow. v2 says Geofabrik/full-outlet pipeline. Do not show both. |
| `Docs/geospatial_catchment_features.md` | Archive or rewrite | It says POI is a remaining improvement and cites old uplift numbers. That conflicts with v2. |
| `Docs/solution_plan.md` | Archive | Planning artifact, not a final judging artifact. It invites "why was this not finished?" questions. |
| `Docs/next_steps_after_eda.md` | Archive | "Next steps" documents make the submission look unfinished. |
| `Docs/challenge_brief.md` | Keep | It matches the official problem and is useful for judges. |
| `Docs/eda_summary.md` | Keep | Strong factual support: 20,000 outlets, 2.37M transactions, data quality findings, and observed-volume spread. |
| `Docs/data_quality_report.md` | Keep | Strong for the 40% data-engineering rubric. Make sure counts match the final run. |
| `Docs/folder_structure.md` | Keep | Low-risk repo navigation aid. |

# The Single Derailment Risk

The pitch dies the moment a judge asks, **"Why does your report say the validation passes when `Results/validation_report.md` says it fails?"** That question converts the whole submission from "ambitious but conservative" to "unreliable." The team must not walk into the viva with contradictory artifacts. Fix the release gate, rebuild the PDF from the green run, archive v1, and rehearse one honest sentence: "We only submit the v2 report after the validation artifact is green."
