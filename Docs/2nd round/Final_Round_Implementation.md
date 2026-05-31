# Final Round — Implementation Summary

> What was built on top of the Phase-1 modeling pipeline to deliver the Data Storm v7.0
> **Final Round** decision engine: a marketing-spend optimizer, a functional Explainable-AI
> layer, and an interactive Outlet Intelligence web app, plus the shared data layer they rely on.
>
> Team **smile Labs** · See [README_FIRST.md](README_FIRST.md) for the problem statement.

---

## 1. Scope: what changed from Phase 1

Phase 1 already produced the latent-potential predictions (`Results/smile_labs_predictions.csv`),
Gaussian distance-decay POI features, and competition counts. The Final Round adds the
**decision layer** on top of those predictions:

| Brief requirement | Status | Where |
| ----------------- | ------ | ----- |
| 2.1 Spatial distance-decay modeling | Existed (Phase 1), reused | `poi_pipeline/src/features.py` |
| 2.2 Competitive catchment density | Surfaced into decision layer | `src/intelligence/build_table.py` |
| 2.3 Marketing spend optimization (LKR 5M Western) | **New** | `src/optimization/` |
| 4.1 Functional XAI (LLM explanations) | **New** | `src/xai/` |
| Deliverable #1 Predictions CSV | Existed (Phase 1) | `Results/smile_labs_predictions.csv` |
| Deliverable #2 Budget allocations CSV | **New** | `Results/smile_labs_budget_allocations.csv` |
| Deliverable #4 Outlet Intelligence web app | **New** | `app/streamlit_app.py` |

---

## 2. New components

### 2.1 Outlet Intelligence layer — `src/intelligence/`

Assembles one decision-ready row per outlet directly from the raw challenge CSVs plus the
predictions CSV — **no parquet / Bronze–Silver–Gold dependency**, so the Final-Round
deliverables run for judges out of the box.

- **Province** is derived from the `Distributor_ID` prefix (`DIST_W_*` → Western,
  `DIST_C_*` → Central, `DIST_NW_*` → North-Western, `DIST_S_*` → Southern).
- Derives normal vs. best vs. predicted monthly volume, **headroom** (potential − normal
  baseline), bill-per-litre, baseline revenue, and **competitive catchment density**
  (count of other outlets within 500 m via a haversine BallTree, normalised to `[0,1]`).
- Output: `Results/outlet_intelligence.csv` — **20,000 outlets** (Western 9,000 · Central
  4,000 · North-Western 4,000 · Southern 3,000).

### 2.2 Marketing spend optimizer — `src/optimization/spend_allocation.py`

Distributes the **LKR 5,000,000** Western-Province budget to maximise *additional* sales
volume over the normal historical baseline.

- **Response model** (concave, saturating returns):
  `g(s) = H · (1 − e^(−s/k))` — incremental litres from spend `s`, where `H` is latent
  headroom and `k` (the responsiveness scale) grows with the opportunity's revenue value
  and local competitive intensity:
  `k = α · (H · bill_per_litre) · (1 + β · competitive_intensity)`.
- A **revenue-anchored per-outlet cap** (`cap_frac · H · bill_per_litre`) prevents a few
  large outlets from absorbing the budget.
- Because the objective is separable-concave, the optimum is found **exactly by Lagrangian
  water-filling** — bisection on the shadow price `λ` so total spend equals the budget
  (KKT conditions), not a heuristic ranking.

**Result (default config α=0.15, β=0.50, cap_frac=0.35):**

| Metric | Value |
| ------ | ----- |
| Budget utilisation | 97.9 % (LKR 4,895,104) |
| Outlets funded | 3,681 / 9,000 |
| Expected incremental volume | +109,479 L |
| Expected incremental revenue | LKR 27.2 M |
| Revenue-to-spend ROI | 5.56× |

Outputs: `Results/smile_labs_budget_allocations.csv` (the **required submission**:
`Outlet_ID`, `Trade_Spend_Allocation_LKR` for all Western outlets), plus
`_detailed.csv` (expected litres/revenue/efficiency) and
`Results/budget_allocation_summary.json`.

### 2.3 Functional Explainable AI — `src/xai/`

Two stages, matching the four signal groups the brief asks the XAI module to surface:

1. **`drivers.py`** — converts a prediction into a **signed, ranked driver payload**:
   model drivers (latent headroom, best-month anchor, sales-history depth), local
   environment signals (competitive catchment density), and operational constraints
   (cooler capacity vs. the outlet-size norm). Each driver carries a direction
   (increases / decreases / neutral), a relative weight, and a one-line technical detail.
2. **`narrative.py`** — an LLM translates that payload into plain business language for a
   non-technical sales leader. Uses the **Anthropic API when `ANTHROPIC_API_KEY` is set**,
   with a deterministic **offline template fallback** so the app always produces a grounded
   explanation (no key / no network required). The same structured payload feeds both paths,
   so narratives are never free-floating.

### 2.4 Outlet Intelligence web app — `app/streamlit_app.py`

A local Streamlit app (no external services) with three tabs:

- **Browse** — every outlet; filter by province / distributor / outlet type, search by ID,
  sort, geographic map, and CSV export of the current view.
- **Drill-down** — per-outlet metrics (potential, normal/best month, competitors), the
  signed driver list, an on-demand **XAI narrative** (live or offline toggle), and the raw
  structured payload.
- **Western spend plan** — the LKR 5M allocation with budget utilisation, funded-outlet
  count, expected uplift, and submission-CSV download.

---

## 3. How to run

```powershell
# 1. Modeling pipeline (Phase 1) — produces the predictions CSV
python run_pipeline.py

# 2. Final-Round decision layer — intelligence + budget + XAI samples
python run_final_round.py            # offline XAI
python run_final_round.py --xai-live # use Anthropic API for narratives

# 3. Web app
streamlit run app/streamlit_app.py

# Optional: enable live LLM narratives
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

`run_final_round.py` is the one-shot orchestrator for the decision layer; it writes all
intelligence, budget, and XAI outputs and prints the app launch command.

---

## 4. Files added / changed

**Added**

```
src/intelligence/__init__.py
src/intelligence/build_table.py        outlet intelligence table builder
src/optimization/__init__.py
src/optimization/spend_allocation.py   LKR 5M KKT water-filling optimizer
src/xai/__init__.py
src/xai/drivers.py                     signed driver payload
src/xai/narrative.py                   Anthropic + offline narrative
app/streamlit_app.py                   Outlet Intelligence web app
run_final_round.py                     decision-layer orchestrator
Docs/2nd round/README_FIRST.md         problem statement (markdown)
Docs/2nd round/Final_Round_Implementation.md   this file
```

**Changed**

```
requirements.txt   + streamlit>=1.40.0, anthropic>=0.40.0
README.md          + Final Round section, repo-layout entries
```

**Generated outputs (in `Results/`)**

```
outlet_intelligence.csv
smile_labs_budget_allocations.csv          <- spend submission
smile_labs_budget_allocations_detailed.csv
budget_allocation_summary.json
xai_samples.json
```

---

## 5. Still outstanding (documentation deliverables)

These two Final-Round deliverables are documents, not code, and are not yet produced:

- **Deliverable #5** — Comprehensive Methodology & Technical Paper (PDF, max 10 pages).
- **Deliverable #6** — Executive Pitch Deck (PDF, max 10 slides).

Both can pull real figures from `budget_allocation_summary.json` and the validation reports.
