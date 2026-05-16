# Generative AI Transparency Log

This document records how Generative AI was used as an engineering accelerator during the solution build.

## Usage Log

| Area | AI Assistance | Human Validation |
| --- | --- | --- |
| Challenge understanding | Summarized the business problem and converted the prompt into structured documentation. | Reviewed against the original problem statement and saved as `Docs/challenge_brief.md`. |
| Solution planning | Drafted a Bronze, Silver, Gold execution plan and latent potential methodology. | Adapted to the actual repository and available datasets. |
| Repository structure | Proposed lakehouse folders and documentation layout. | Created tracked folders with `.gitkeep` and documented them in `Docs/folder_structure.md`. |
| Notebook implementation | Helped draft notebook cells for ingestion, quality checks, cleaning, feature engineering, and modeling. | Ran the notebook end to end in a local virtual environment and inspected generated outputs. |
| Data quality logic | Suggested reusable duplicate, null, range, domain, and referential integrity checks. | Verified checks against real data anomalies such as invalid coordinates and negative transactions. |
| Modeling logic | Suggested a lower-bound plus peer-frontier approach for latent demand uncapping. | Evaluated prediction distributions and revised the method after the first result was too conservative. |
| Guardrail tuning | Helped identify excessive uplift outliers and add size-based caps. | Re-ran predictions and checked uplift ratios, row counts, and missing values. |
| Git workflow | Helped diagnose a GitHub push rejection caused by a file over 100 MB. | Removed challenge datasets from Git history, kept them local, and added `Datasets/` to `.gitignore`. |

## Validation Principles

AI-generated code and assumptions were not accepted blindly.

| Phase | AI tool / role | Concrete usage | Validation we performed | Final decision |
|---|---|---|---|---|
| Background research swarm | Claude Opus 4.7-thinking + GPT-5.5 (10 parallel research subagents) | Survey of latent-demand modelling (Tobit, censored QR, SFA), Sri Lanka POI sources, OSM Overpass query design, past Data Storm winners, quantile regression best practices, causal identification limits, defensible uplift caps | Each agent's claims cross-checked against the cited URLs. Synthesised by hand into `research/research_brief.md` with explicit `USE / SUPPLEMENT / REJECT` decisions per method. | Adopted: SFA + multi-quantile + Conformalised QR + Manski + Geofabrik PBF approach. Rejected: Heckman (no exclusion restriction), DEA (too slow on 20k DMUs), full Two-Tier SFA (no mature Python lib for 36h). |
| Methodology audit (round 1) | Claude Opus 4.7-thinking + GPT-5.5 (4 parallel critics: Statistician, Skeptic, Methodology Architect, Safety + DE) | Audit of the team's existing methodology (lower_bound + 90th-pct quantile GBM frontier + rank-sum constraint score + size caps) | Each finding traced back to a specific file:line in `Notebooks/01_latent_potential_pipeline.ipynb`. Manually verified: rank-sum constraint score had `valid_coordinate_rank` (a DQ flag) at 10% weight; the four-layer throttle (`^1.25` + `clip(0, 0.65)` + size cap + peer-p98 cap) was mechanically forcing median uplift to ~1.20x. | Acted on every BLOCKER and MAJOR; deferred MINORs. Master synthesis in `Reviews/council_review.md`. |
| Implementation | Cursor IDE with Claude / GPT routing | Scaffolded `src/quality/`, `src/cleaning/`, `src/features/`, `src/modeling/`, `src/reporting/`, and `poi_pipeline/`. Refactored notebook logic into reusable modules. | Every module has docstrings citing the specific paper / heuristic. `_syntax_check.py` and `_import_check.py` verified imports clean before each commit. ReadLints showed no errors on the new modules. | All scaffolded code adopted. |
| SFA derivation | LLM-assisted recall of JLMS 1982 closed-form expressions | `src/modeling/sfa.py` -- the MLE objective, Aigner-Lovell-Schmidt log-likelihood, and Jondrow-Lovell-Materov-Schmidt technical efficiency formula | Unit-checked the closed forms against Greene's *Econometric Analysis* (8th ed., chapter 18). `sigma_v`, `sigma_u`, `lambda` printed at fit time so we can sanity-check the inefficiency variance. | Adopted; later patched after round 2 caught a target-leakage bug (see below). |
| POI design | LLM survey of OSM tagging conventions for Sri Lanka + the OSM Wiki | Category-to-tag mapping in `poi_pipeline/config.py` (9 categories x 1-3 OSM keys each) | Tag names cross-checked against the OSM Wiki entry per category. Geofabrik PBF download verified to be ~136 MB and parseable by `pyrosm`. | Adopted. Coverage caveat (kades thinly mapped in LK) honestly disclosed in `poi_pipeline/output/poi_coverage_report.md` and Section 2 of the PDF. |
| Methodology audit (round 2) | Claude Opus 4.7-thinking + GPT-5.5 (same 4 critics, re-audit) | Verification that round 1 fixes landed + identification of new bugs introduced by the refactor | Each finding traced to file:line. Verified: N1 = `predict.py` floored at `lower_bound` (would fail V3b); N2 = `manski_lower < observed_max` violated trivial Manski floor; N3 = SFA target leakage (observed_p90/p95/median/mean fed into `sfa_X` while predicting `observed_max`); N4 = Conformalised QR module existed but was never wired into the orchestrator. | All 4 N-blockers fixed. Master synthesis in `Reviews/council_round2/council_review_v2.md`. |
| Round-2 fix application | LLM-assisted code edits | StrReplace edits to `predict.py`, `manski.py`, `validation.py`, `run_pipeline.py` to fix N1-N4 + O1 (V5 cap-binding) + O5 (move legacy CSV out of `Results/`) | After each edit: `_check_after_fixes.py` ran ast.parse on every src/ file and re-imported the orchestrator. ReadLints clean. | Ship. |
| Report drafting | LLM as drafting accelerator | First draft of `Reports/final_report.md` -- 5 pages with cover, forensics, POI, causal logic, GenAI log | Every claim mapped to an artifact in the repo. Numbers will be pulled from `Results/run_summary.json` and `Results/validation_report.md` after the final pipeline run. | Adopted as-is for first draft; team reviews/edits before final build. |

- running the notebook end to end.
- checking prediction row counts and uniqueness.
- checking missing and negative predictions.
- comparing potential predictions against historical maxima.
- reviewing rejected record counts.
- revising the model when results were too conservative.
- adding guardrails when uplift became too aggressive.

## Current AI-Accelerated Artifacts

- `Docs/challenge_brief.md`
- `Docs/solution_plan.md`
- `Docs/folder_structure.md`
- `Docs/data_quality_report.md`
- `Docs/modeling_methodology.md`
- `Docs/ai_transparency_log.md`
- `Notebooks/01_latent_potential_pipeline.ipynb`

## Remaining Human Review Needed

Before final submission, the team should manually review:

- the highest potential outlets.
- the highest uplift outlets.
- peer frontier assumptions.
- final POI categories once external geospatial features are added.
- the final PDF report narrative.
