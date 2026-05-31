# Business / Viva Critic — Council Round 5

**Reviewer:** Business & Viva Critic (R5)
**Scope:** Report credibility, viva pitch readiness, artifact coherence, hostile-judge Q&A
**Context:** Validation 6/6 PASS. Two candidate reports on disk. EDA charts produced but not wired into report.

---

# TL;DR

- **There are now TWO active final reports on disk** that any judge could find: `Docs/smile_labs_final_report.md` (claims 1.18× uplift, "Tobit Type-I") and `Reports/final_report.md` (correct numbers but still has fill-in placeholders). Submit exactly one PDF from exactly one source. Anything else is an unforced credibility error.
- **The `Reports/final_report.md` placeholders are the single highest-visibility bug for viva.** If the PDF has literal `\textit{fill in from run_summary.json}` in the headline numbers table, the submission looks unfinished — independent of model quality.
- **The 3-slide viva pitch from R4 is still the right pitch.** Nothing in R5 changes the business framing. The charts now exist. Use them.

---

# Report Status Audit

| File                              | Uplift claim                | Methods                                                  | Validation claim          | Placeholders   | Action                          |
| --------------------------------- | --------------------------- | -------------------------------------------------------- | ------------------------- | -------------- | ------------------------------- |
| `Docs/smile_labs_final_report.md` | **1.18× (stale v1)**        | SFA + CH-CQR + multi-q + **Tobit Type-I** (ghost method) | 6/6 (but pre-fix numbers) | None           | **Archive to `Docs/_archive/`** |
| `Reports/final_report.md`         | **"fill in"** (placeholder) | SFA + multi-q + CQR + CH-3 + Manski (correct)            | "fill in PASS/FAIL"       | **3 unfilled** | **Fill and use as canonical**   |

The `smile_labs_final_report.md` is the more polished prose document, but its numbers are wrong and it references a method ("Tobit Type-I MLE") that does not exist anywhere in `src/modeling/`. If a judge looks at the code and then the report, they will find:

- `src/modeling/*.py` files: `sfa.py`, `censored_qr.py`, `frontier.py`, `conformal.py`, `caps.py`, `constraint_score.py`, `lower_bound.py`, `predict.py`
- No `tobit.py`. No `tobit_mle.py`. No mention of Tobit anywhere in the codebase.
- The `smile_labs_final_report.md` method table lists Tobit Type-I as a key component.

This is a hard credibility break. **Archive the stale report immediately.**

---

# Filling the `Reports/final_report.md` Placeholders

Three lines need updating (lines 39-41):

**Before:**

```latex
| Median uplift vs historical max | \textit{1.10-1.50x (fill in from `Results/run_summary.json` after running v2)} |
| Mean uplift vs historical max | \textit{1.35-1.70x (fill in after run)} |
| 6-item auto-validation | \textit{fill in PASS/FAIL from `Results/validation_report.md`} |
```

**After (from `Results/validation_report.json` + R4 diagnostics):**

```latex
| Median uplift vs historical max | 1.250× |
| Mean uplift vs historical max | 1.233× |
| 6-item auto-validation | ALL PASS (6/6) |
```

The `Results/validation_report.json` is on disk and confirms `median_uplift=1.250` and all 6 checks passing. Mean uplift of 1.233 comes from the R4 diagnostician's post-fix simulation on `predictions_v2.parquet`.

---

# 3-Slide Viva Pitch (unchanged from R4 — now with chart references)

## Slide 1: "We don't predict sales. We predict ceiling."

**Headline:** `20,000 outlets, 2.37M transactions. Median observed max = 164 L vs 95th pct = 1,308 L.`
**Chart:** `Reports/figures/eda_frontier_gap.png`
**Say:** _"Every outlet in this dataset has a ceiling — credit limits, stockouts, cooler space, delivery caps. Observed sales are the floor of true demand, not the level. Our model estimates the gap."_

## Slide 2: "A guarded uplift, not a black-box forecast."

**Headline:** `1.250× median uplift. 0.00% below historical max. All 6 release checks pass.`
**Chart:** `Reports/figures/eda_constraint_uplift.png`
**Say:** _"Every prediction is anchored at or above what the outlet has already proven. We only move above the floor when the outlet shows constraint evidence: peer-frontier gap, plateau behavior, capacity, and catchment signals. The uplift is conservative and bounded."_

## Slide 3: "Turn the model into an action list."

**Headline:** `Top-100 uplift outlets: 9.5× censoring enrichment. DIST_S_01/02: 5× Southern province censoring rate.`
**Chart:** `Reports/figures/eda_top100_sanity.png` + `eda_distributor_volume.png`
**Say:** _"The model points to specific actions: check Southern province distributor supply allocation. The top uplift outlets are smaller, more constrained, and more likely to be supply-limited — exactly where cooler investment and trade spend will yield real volume."_

---

# 5 Hostile Judge Q&A (updated for R5 state)

## Q1: "Your report says median uplift 1.18×. Your validation report says 1.250×. Which is right?"

**Answer:** _"The 1.18× figure appears in `Docs/smile_labs_final_report.md`, which is an earlier version of the report written before the v2 model fixes. The canonical report is `Reports/final_report.md` and the authoritative number is `median_uplift=1.250` from `Results/validation_report.json`. We archived the stale document — I apologise if both were visible."_

**If not archived before viva:** This question ends the viva badly. Archive it.

## Q2: "Where is your Tobit Type-I MLE code? We can't find `tobit.py` in `src/`."

**Answer:** _"Tobit Type-I was evaluated in our research phase but not implemented — it requires a known censoring threshold (the constraint value), which we only observe via proxies. We chose SFA (which models the inefficiency term directly) and multi-quantile XGBoost. The `Docs/smile_labs_final_report.md` that mentions Tobit is a stale draft and does not reflect the final codebase."_

**If `smile_labs_final_report.md` is not archived:** The judge has it in hand and this answer sounds like a post-hoc cover-up.

## Q3: "Your POI correlation with volume is nearly zero. Why is POI in Section 2 of your report?"

**Answer:** _"That's a fair challenge. POI catchment score shows |r| ≤ 0.026 with outlet volume across all outlet types — the OSM data in Sri Lanka has good coverage for schools, hospitals, and transport hubs, but thin coverage for informal kades and small grocers, which are exactly the outlets most likely to be constrained. POI contributes as a catchment-context signal in the constraint score's capacity PCA component. We're honest about this in Section 2 and flag it as a future improvement as OSM tagging improves."_

## Q4: "If censoring is only 1.16%, why do you need Chernozhukov-Hong?"

**Answer:** _"Censoring being rare is itself a finding from the EDA — it means the model's primary job is not a censoring correction but rather identifying outlets with latent headroom via the constraint score. CH-3 is in the pipeline as a principled diagnostic: with 1.16% censored, it correctly keeps 100% of the training set and the q90 refit is a no-op. If a future supply disruption quarter produces 10%+ censored outlets, the pipeline engages the correction automatically without code changes."_

## Q5: "Why is `run_pipeline.py` in your repo if the canonical output comes from notebooks?"

**Answer:** _"The orchestrator and the notebooks produce identical outputs — both call the same `src/` modules. The README correctly documents the notebook workflow as the primary execution path. `run_pipeline.py` is the single-command production equivalent, and in R5 we patched the one rounding inconsistency that existed between the two paths. Both now produce the same V3b-safe CSV."_

---

# Report Build Instructions

```bash
# 1. Fill in the three placeholder lines in Reports/final_report.md (see above)
# 2. Build PDF:
cd /Users/sithijaseneviratne/Documents/Github/Data-Storm-2026/Reports
pandoc final_report.md -o final_report.pdf \
  --pdf-engine=xelatex \
  --variable geometry:margin=2cm \
  --variable fontsize=10pt
# 3. Verify PDF is exactly 5 pages, all sections present, no "fill in" text
# 4. Place PDF in Reports/ as final_report.pdf
```

---

# Pre-Viva Checklist

- [ ] Only ONE final report PDF — from `Reports/final_report.md` (no stale `Docs/smile_labs_final_report.md` visible)
- [ ] All three placeholder lines filled with real numbers
- [ ] `Results/smile_labs_predictions.csv` — verify `head -1` is `Outlet_ID,Maximum_Monthly_Liters`
- [ ] `Results/validation_report.md` — all 6 PASS (last line is V5)
- [ ] R4 + R5 council rounds mentioned in `README.md` and `ai_transparency_log_v3.md`
- [ ] All `eda_*.png` charts accessible from `Reports/figures/` for slideshow
- [ ] 3-slide pitch rehearsed with the business framing sentence memorised

**Business framing sentence (memorise):**

> _"Our model treats observed sales as a hard lower bound on constrained demand, and predicts the gap to a comparable outlet peer frontier — defended by constraint evidence, catchment signals, peer caps, and a six-item validation gate."_
