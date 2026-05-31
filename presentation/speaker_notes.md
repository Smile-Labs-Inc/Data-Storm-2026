# Executive Pitch — Speaker Notes

**Format:** 10 slides · 10-min pitch · then 5-min live demo + technical Q&A.
**Audience:** non-technical C-suite. Lead with money and decisions, not method. ~1 min/slide.

---

### Slide 1 — Cover (0:00–0:30)
Open with the one line: *"We found the sales hiding inside your existing outlet network — and a plan to unlock it."* Name the three headline numbers and move on. Don't read the slide.

### Slide 2 — The blind spot (0:30–1:30)
The hook. Today, trade spend rewards the top sellers — but they're already near full, so the money does little. The real growth is in outlets quietly under-selling their potential. **End on the question on the right** — that's what the rest of the deck answers.

### Slide 3 — The insight (1:30–2:45)  *[requirement a]*
The single most important idea: **what an outlet sold is the floor, not the ceiling.** Use the bar visual. Stress that we give a *range* per outlet, not a fake-precise number — that's honesty the board can trust. Median outlet can do 1.25× its best month.

### Slide 4 — How we unmask it (2:45–4:00)  *[requirement a]*
Keep it plain: five independent reads (track record, peers, neighbourhood from 42,386 real landmarks, physical capacity) vote together. No single assumption drives it. **Credibility line:** seven review rounds, 6/6 automated quality gates. Do NOT say "stochastic frontier", "censoring", "quantile" — save jargon for the Q&A.

### Slide 5 — Potential-Based Allocation (4:00–5:00)  *[requirement b]*
The principle: **fund the gap, not the glory.** Every rupee chases the most extra litres. We respect diminishing returns (stop before waste) and the plan is provably optimal for a fixed budget.

### Slide 6 — The Western plan (5:00–6:15)  *[requirement b]*
The concrete split. 9,000 outlets considered → back the **3,729** with the best return. **98% of the LKR 5M** deployed, 21.8 L bought per LKR 1,000. Focused, not sprayed. Each funded outlet gets a precise amount it can absorb.

### Slide 7 — Business impact (6:15–7:30)  *[requirement c]*
The payoff slide — slow down here. **+109,021 L** incremental volume, **LKR 27.1M** incremental revenue, **5.53× ROI**. Emphasise: traceable per-outlet, survives sensitivity testing — disciplined projections, not round numbers.

### Slide 8 — Efficiency & regional growth (7:30–8:30)  *[requirement c]*
Why ours beats the alternatives (reward-top / spread-evenly). Same budget, better aim. Growth comes from overlooked clusters. **Scale message:** same engine runs all 20,000 outlets nationwide — repeatable for any future budget.

### Slide 9 — Rollout (8:30–9:30)  *[requirement d]*
Make it feel easy: (1) hand each distributor a ready spend list that drops into existing routes; (2) reps get plain-language reasons in the Outlet Intelligence app; (3) track actuals vs projection and re-run next cycle. Nothing new for teams to learn.

### Slide 10 — The ask (9:30–10:00)
Close memorably: *"Stop funding the past. Start funding the potential."* Approve the Western plan now; the engine is ready to allocate every future rupee. Then transition: *"Let me show you the live system."* → demo.

---

## Q&A ammo (technical session — pull from the report if pressed)
- **"How is potential estimated?"** Right-censored demand: observed sales = min(true demand, constraint). Blend of XGBoost multi-quantile + Stochastic Frontier Analysis (60/40), Chernozhukov–Hong censoring correction, Conformalised QR intervals, bootstrap peer-bucket caps.
- **"Why a range?"** Estimand isn't point-identified from observational data — we report [lower, point, upper] + Manski worst-case bounds. Honest by construction.
- **"How is the budget solved?"** Concave saturating response per outlet; Lagrangian water-filling (KKT), bisection on the shadow price. Provably budget-feasible and optimal — not a heuristic.
- **"Is POI data reliable?"** Disclosed caveat: per-outlet POI correlates weakly with volume (|r|≤0.026); enters only as a ~20% catchment signal, never a standalone predictor. OSM under-maps small kades — we say so.
- **"Validation without ground truth?"** 6-item auto-checklist, all PASS: schema, no NaN/neg, IDs in master, ≥99% predicted ≥ historical max, median uplift in [1.25, 2.2], cap-binding < 25%.
- **Provenance:** every code fix cites the AI-council finding it addresses; full log in `Docs/ai_transparency_log.md`.
