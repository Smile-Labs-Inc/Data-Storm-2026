# AI Council Round 7 -- Master Synthesis (v3 PDF Review)

**4 parallel critics audited `Reports/final_report_v3.pdf` (5 pages, 267 KB, built via LaTeX skill).**

| Critic | Model | File | Grade |
|---|---|---|---|
| Visual Designer | Claude 4.6 Sonnet thinking | `01_visual_designer_v7.md` | **6.4 / 10** today -> 8.0 / 10 after fixes |
| Content Fidelity | GPT-5.5 extra-high | `02_content_fidelity_v7.md` | **7 / 10** (8 numeric/formula failures) |
| Judge Proxy | Claude 4.6 Sonnet thinking | `03_judge_proxy_v7.md` | **82 / 100** -- "Strong, not Top-tier" |
| Risk / Adversarial | GPT-5.5 extra-high | `04_risk_adversarial_v7.md` | flagged page-5 clipping + 1.25 looks tuned |

**Consensus verdict:** *PDF is shippable today at ~80/100. ~90 minutes of targeted fixes lifts to ~88/100 (top-tier). Three issues are independently flagged by 2+ critics -- those are the priorities.*

---

## CONVERGENT FINDINGS (2+ critics agree)

### C1. The "[1.000, 1.022]" sensitivity range on page 5 IS WRONG

*Flagged by:* Content Fidelity + Risk

The PDF says (page 5, sensitivity sweep paragraph):
> "Median uplift remains in $[1.000, 1.022]$ across all quantile x scheme combinations"

But `Reports/figures/sensitivity_summary.md` actually shows median uplift = **1.250x** consistently across all sweep rows. The "[1.000, 1.022]" range looks like leftover prose from the PRE-FIX v2 state.

**Severity:** BLOCKER for accuracy. A judge cross-referencing this against the cover ("median uplift 1.250x") will catch the contradiction in 30 seconds.

**Fix (StrReplace, 1 min):** rewrite the sentence on page 5 to say "Median uplift stays at 1.250x across all combinations; cap-binding rate at 0.00% even at the loosest cap multiplier."

### C2. POI weak-signal disclosure is MISSING

*Flagged by:* Judge Proxy + Risk

The team's own EDA (notebook 23) found POI correlation with volume is `|r| ≤ 0.026` per outlet type. The PDF page 3 ("Honest Sri Lanka coverage caveats") admits the OSM tag patchiness but does NOT admit the actual signal weakness. A judge who reads the EDA notebook (in the repo zip) will spot this and attack it.

**Severity:** MAJOR -- "honest disclosure" page that hides the actual finding is worse than no disclosure.

**Fix (StrReplace, 5 min):** add to the caveat box on page 3:
> "Per our own EDA (notebook 23), per-outlet POI counts correlate weakly with monthly volume (|r| ≤ 0.026 across outlet types). POI catchment therefore enters the model only through the composite catchment_density_score (rank-percentile feature) at ~20% weight in the constraint score -- not as a standalone demand predictor."

### C3. Page 5 is over-dense / looks formatting-broken

*Flagged by:* Visual Designer + Risk + Content Fidelity (overfull hbox warnings)

Bibliography at `\scriptsize` with `\bibitemsep=0pt` immediately after the deliverables list looks like a formatting bug, not a deliberate choice. The "Reproducible codebase" bullet still slightly overflows the column (Risk found overfull hbox in the .log).

**Severity:** MAJOR for first impressions.

**Fix options (~15 min):**
- Replace the prose sensitivity paragraph with a small 3x3 heatmap (pgfplots) -- buys vertical space
- Move bibliography to a 2-column `\begin{multicols}{2}` layout
- Add a 0.5em vertical rule between deliverables list and bibliography

---

## NEW CRITIC-SPECIFIC FINDINGS

### Visual Designer (6.4 -> 8.0/10)

| Page | Score | Single issue |
|---|---|---|
| 1 Cover | 6/10 | upper 40% bare white -- no logo / brand band |
| 2 Forensics | 7.5/10 | B-S-G TikZ clean; edge labels at scriptsize marginal |
| 3 POI | 6.5/10 | zero figures -- 80.9% buried in a table row |
| 4 Methodology | 7/10 | DAG node text at scriptsize / "right-censored" at tiny -- below 7pt print legibility |
| 5 Validation | 5/10 | sensitivity prose-only; bibliography looks like format error |

**3 ROI fixes ranked:**
1. DAG font bump (`\scriptsize -> \small`, widen estimand node x-offset 0.4 -> 1.0 cm) -- **5 min, biggest legibility gain**
2. Sensitivity heatmap replacing prose paragraph on p5 -- **25 min, turns strongest robustness claim into visible chart**
3. TikZ overlay header band on cover with primary-blue + Smil Labs wordmark -- **15 min, crosses from "LaTeX article" to "branded submission"**

### Content Fidelity (7/10, 8 numeric/formula failures)

Biggest fidelity issues:

| Claim in PDF | Actually | Action |
|---|---|---|
| "Rejected records ... 480 + 9,606 + 93" on cover | Those are **failed-check totals** (some failed multiple checks); unique quarantined rows differ slightly | reword to "10,179 rejected check records across 3 datasets" OR cite the actual unique-row counts |
| Sensitivity range "[1.000, 1.022]" | actual 1.250x median uplift | see C1 above |
| Final formula on page 4 vs `predict.py` | formula in PDF is missing the constrained-uplift floor (`cs >= 0.40 -> >= 1.25x observed_max`) which IS in predict.py | add a third line to the formula box |
| 6 cited refs in bib | match expected count (6) | OK -- no action |
| All path references | resolve | OK |
| All POI category counts (9) vs `_extraction_summary.csv` | match | OK |

### Judge Proxy (82/100 = STRONG)

Rubric breakdown:

| Rubric | Weight | Score |
|---|---|---|
| DE & Forensics | 40% | 32.4 / 40 (81%) |
| Methodology & Base Math | 40% | 33.0 / 40 (82.5%) |
| GenAI Workflow | 20% | 16.7 / 20 (83.5%) |
| **Total** | **100%** | **82.1 / 100** |

**Hardest viva question:** *"How many outlets actually change predictions because of CH-3 vs without it?"* -- CH-3 is largely cosmetic (1.16% of outlets censored). PDF doesn't say so. Team needs an outlet-count number ready.

**3 things this PDF does BETTER than typical hackathon entries:**
1. Manski partial-identification framing -- rare at hackathon level, buys real credibility
2. Geofabrik > Overpass rationale on page 3 -- production-engineer instinct
3. GenAI Table 5 (5-row per-phase log) is the best AI transparency disclosure of the format

**3 things that LOSE points:**
1. No ablation / feature-importance chart (POI carrying 20% weight isn't defended)
2. CH-3 looks load-bearing but is mostly cosmetic
3. No SFA fit diagnostics ($\sigma_u, \sigma_v, \lambda$ or TE distribution)

**Verdict:** Strong, not Top-tier. Off 88+ until ablation + CH-3 outlet count are added.

### Risk / Adversarial

**Top 3 disasters by severity:**
1. Sensitivity range typo (same as C1) -- BLOCKER for accuracy
2. "1.250x median" looks suspiciously close to V4 floor (1.25x) -- INVITES "did you tune to the validation?" question
3. Page 5 overfull hbox warning in the .log -- MAJOR (visual + signals carelessness)

**Hostile questions the PDF invites:**
- "Why is your median uplift EXACTLY 1.250 -- did you fit to your own validation threshold?" (Best answer: "1.25 is the empirical 95th-percentile uplift from peer top-decile bootstraps, the V4 threshold was set to match the methodology, not the other way around" -- but this MUST be in the report or it sounds defensive)
- "Where are your model diagnostics?" (no SFA sigma, no CQR coverage, no constraint-score distribution)
- "Does removing POI features change anything?" (no ablation)
- "What's the confidence interval for the median uplift number?" (no bootstrap CI)
- "Why does Table 5 only show 5 GenAI phases over 36 hours? Were no AI prompts used during the 31 other hours?" (the per-phase log is too compressed)

---

## PRE-SUBMISSION PREFLIGHT (10 items from Risk critic)

1. [ ] Fix "[1.000, 1.022]" sensitivity range typo on p5 (BLOCKER)
2. [ ] Add POI |r| <= 0.026 disclosure to p3 caveat box (MAJOR)
3. [ ] Add 3rd formula line for the constrained-uplift floor on p4 (MAJOR -- formula incomplete)
4. [ ] Add one sentence on p4 with SFA fit diagnostics ($\sigma_u, \sigma_v, \lambda$, TE median)
5. [ ] Add one sentence on p4 with CH-3 outlet count ("CH-3 reclassified N outlets; primarily DIST_S_01 / DIST_S_02")
6. [ ] DAG font bump on p4 ($\scriptsize \to \small$)
7. [ ] Verify `Results/smil_labs_predictions.csv` has `Outlet_ID` + 20,000 rows + no NaN before zipping
8. [ ] Rebuild PDF after each fix; verify still 5 pages exactly
9. [ ] Zip repo EXCLUDING `data/bronze/`, `data/silver/`, `poi_pipeline/data/raw/`, `Results/_legacy/`, `.venv/`
10. [ ] Spot-check `Reports/figures/final_report_v3_p-{1..5}.png` for any rendering artifact

---

## ORDERED FIX LIST (recommended apply order)

If you do nothing else, do these in this order. Each fix is small:

| # | Fix | File | Time | Score lift |
|---|---|---|---|---|
| 1 | Rewrite sensitivity sentence on p5 (1.250 not 1.000-1.022) | `final_report_v3.tex` | 1 min | +3 fidelity, +1 judge |
| 2 | Add POI weak-signal disclosure to p3 caveat box | `final_report_v3.tex` | 5 min | +2 judge, +2 risk |
| 3 | Add constrained-uplift floor 3rd line to formula on p4 | `final_report_v3.tex` | 3 min | +2 fidelity |
| 4 | Add SFA + CH-3 diagnostics sentence on p4 | `final_report_v3.tex` | 10 min | +3 judge |
| 5 | DAG font bump on p4 + estimand-node x-offset 0.4 -> 1.0 cm | `final_report_v3.tex` | 5 min | +1 visual |
| 6 | Move bibliography to 2-column `multicols` on p5 | `final_report_v3.tex` | 5 min | +1 visual |
| 7 | Rebuild + verify still 5 pages exactly | `build_pdf_v3.py` | 1 min (cached packages) | -- |

**Total: ~30 min for +12 estimated points (82 -> 88 -> "Top-tier").**

---

## What to do NOW

This synthesis lists every fix; **no fixes have been applied yet** (Round 7 was diagnostic only, per the user's intent: "do a review").

To apply fixes, switch back to Agent mode and say either:
- "apply all R7 fixes" -- I'll do all 7 in order + rebuild + verify
- "apply only fixes 1-3" (or any subset) -- I'll do just those
- "apply fixes then trigger R8" -- I'll do the fixes, rebuild, then run R8 on the updated PDF

If you want to ship the PDF as-is right now, you'll be at ~80/100 (Strong / Acceptable per Judge Proxy). The 3 convergent fixes alone (C1, C2, C3) take ~10 min and push to ~85.
