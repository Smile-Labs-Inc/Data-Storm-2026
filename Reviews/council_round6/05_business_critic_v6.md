# Business / Viva Critic — Council Round 6

**Reviewer:** Business & Viva Critic (R6)
**Scope:** Report credibility, viva pitch readiness, artifact coherence
**Context:** Validation 6/6 PASS. Stale report still visible. EDA charts not wired.

---

# TL;DR

- **`Docs/smile_labs_final_report.md` is still visible** — claims 1.18× uplift + "Tobit Type-I" ghost method. R5 said archive it. Not done. This is the #1 credibility risk.
- **`Reports/final_report.md` placeholders are filled** (R5 fix landed) but EDA charts are not referenced. The PDF has numbers but no data visualizations.
- **The 3-slide viva pitch from R4/R5 is still correct.** The charts exist. Use them. The business framing sentence is memorizable.

---

# Which Report to Ship

**Verdict: `Reports/final_report.md` built to PDF.** It has correct numbers (1.250×, 1.233×, 6/6 PASS), correct methods (SFA + multi-q + CH-3 + CQR + Manski), and no ghost methods.

**Archive immediately:** `Docs/smile_labs_final_report.md` → `Docs/_archive/`. It claims 1.18× and "Tobit Type-I MLE" — a method with zero code in `src/modeling/`. If a judge finds both reports, the contradiction is fatal.

---

# 3-Slide Viva Pitch

## Slide 1: "We don't predict sales. We predict ceiling."

- **Chart:** `eda_frontier_gap.png`
- **Say:** _"20,000 outlets, 2.37M transactions. Observed sales are the floor of true demand. Our model estimates the gap to a peer-derived frontier."_

## Slide 2: "A guarded uplift, not a black-box forecast."

- **Chart:** `eda_constraint_uplift.png`
- **Headline:** `1.250× median uplift. 0.00% below historical max. 6/6 release checks pass.`
- **Say:** _"Every prediction is anchored at or above proven historical max. Uplift only when constraint evidence exists."_

## Slide 3: "Turn the model into an action list."

- **Charts:** `eda_top100_sanity.png` + `eda_distributor_volume.png`
- **Headline:** `Top-100 uplift outlets: 9.5× censoring enrichment. DIST_S_01/02: 5× Southern province censoring.`
- **Say:** _"Check Southern province distributor supply. Top uplift outlets are supply-limited — where investment yields real volume."_

---

# 5 Hostile Judge Questions

**Q1: "Your Docs/ folder has a report claiming 1.18× uplift. Your Results/ says 1.250×. Which is right?"**

- **Answer:** _"1.250× is correct. The Docs/ file is a stale draft archived in Docs/\_archive/. The canonical report is Reports/final_report.md."_
- **Trap:** If not archived before viva, this ends badly.

**Q2: "Where is your Tobit Type-I code?"**

- **Answer:** _"Tobit was evaluated in research but not implemented. We chose SFA + multi-quantile XGBoost. The stale report mentioning Tobit does not reflect the codebase."_
- **Trap:** If stale report visible, sounds like a cover-up.

**Q3: "POI correlation with volume is near zero. Why is POI in your report?"**

- **Answer:** _"Fair challenge. |r| ≤ 0.026 across outlet types — OSM coverage is thin for informal kades. POI contributes to catchment density composite. We flag this honestly as a future improvement."_

**Q4: "If censoring is only 1.16%, why Chernozhukov-Hong?"**

- **Answer:** _"Censoring being rare is itself an EDA finding. CH-3 correctly keeps 100% of training data as a no-op. The pipeline auto-engages if future data shows elevated censoring."_

**Q5: "Why is median uplift exactly 1.250 — the lower bound of your V4 check?"**

- **Answer:** _"The 1.25× floor is applied to ~87% of outlets flagged as constrained. The median sits in this cohort. It's conservative by design — we'd rather under-predict than over-claim."_

---

# Business Framing Sentence (memorise)

> _"Our model treats observed sales as a hard lower bound on constrained demand, and predicts the gap to a comparable outlet peer frontier — defended by constraint evidence, catchment signals, peer caps, and a six-item validation gate."_

---

# GenAI Story for the Pitch

_"We used LLMs as an adversarial accelerator: 10 research agents surveyed latent-demand methods across econometrics and ML, 4 parallel critics per round found bugs our team missed (12 issues in R5 alone), and every AI output was verified against primary sources or run end-to-end. The AI didn't write our model — it stress-tested it. Six rounds of council audits, each finding real, fixable issues, is the evidence."_

---

# v1 Docs Retirement Plan

| File                              | Action                    | Why                                   |
| --------------------------------- | ------------------------- | ------------------------------------- |
| `Docs/smile_labs_final_report.md` | **ARCHIVE to \_archive/** | 1.18× + Tobit ghost method            |
| `Docs/modeling_methodology.md`    | KEEP (v1 reference)       | Documents v1 approach for audit trail |
| `Docs/solution_plan.md`           | KEEP                      | Early planning artifact               |
| `Docs/next_steps_after_eda.md`    | KEEP                      | EDA follow-up plan                    |

---

# The Single Derailment Risk

**The stale `Docs/smile_labs_final_report.md` being found by a judge.** It claims different numbers (1.18× vs 1.250×) and a method that doesn't exist (Tobit Type-I). If a judge opens Docs/ and sees two conflicting reports, the team loses all credibility regardless of model quality. Archive it before anything else.
