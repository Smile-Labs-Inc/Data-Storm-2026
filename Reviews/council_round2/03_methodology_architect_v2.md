# TL;DR

- **Re-grade: B+**. The refactor now has a real spine: censored latent demand -> lakehouse forensics -> Gold features with optional POI -> frontier/SFA -> Manski bands -> validation -> CSV.
- The stack is close to the Round 1 recommendation, but not clean yet: CQR is implemented and claimed, but not wired into `run_pipeline.py`; POI is separate and optional, not guaranteed.
- The highest-grade move is claim control: generate one methodology manifest from the run that says exactly what executed, what artifacts exist, and what the PDF may claim.

# Coherence Re-grade

**Was: B-. Now: B+.**

The end-to-end story is now coherent enough to defend:

```text
Business problem:
  estimate January 2026 maximum monthly liters for 20,000 outlets

Identification:
  observed sales are a censored lower bound:
  observed = min(true demand, operational constraints)

Data method:
  Bronze raw copies + hashes
  -> Silver cleaned records + rejected store
  -> Gold outlet features
  -> optional POI catchment merge

Model method:
  robust lower bound
  -> censored q90 frontier
  -> SFA secondary frontier signal
  -> calibrated constraint score
  -> bootstrap caps
  -> Manski lower/point/upper bands

Validation/output:
  DAG + sensitivity sweep + validation suite
  -> 20,000-row CSV
```

This is no longer a pile of notebooks. It is a pipeline with named modules and a visible causal story.

The remaining weakness is not architecture. It is claim control. The README says CQR intervals are part of the interval story, but the orchestrator never calls `conformalised_qr`. `Reports/` and `poi_pipeline/output/` are not present in the current tree, so those are planned/run-time artifacts, not reviewable artifacts yet. That keeps this below A-range.

# Method-Rubric Re-mapping

| Rubric item | Round 1 answer | Now | Grade movement |
| --- | --- | --- | --- |
| Conceptualization of latent potential | Correct lower-bound idea, but framed through an ad hoc `constraint_score^1.25` blend. | Clear latent variable framing: `observed = min(true_demand, constraints)`. Final formula is `lower + constraint_score * (frontier - lower)`, capped once by bootstrap caps. | **B -> A-**. The concept is now report-grade. |
| Math/stat for missing target + censored data | Weak-to-medium. Q90/peer frontier and caps, but no honest non-identification frame. | Manski bands exist. SFA exists. Chernozhukov-Hong-style censoring correction exists. Multi-quantile frontier exists. CQR exists as dead code unless wired into the run. | **C+ -> B+**. Stronger, but claims exceed execution on CQR. |
| DE forensics: Bronze/Silver/Gold + rejected records | Good intent, but notebook-heavy and some correctness bugs. | `run_pipeline.py` creates Bronze copies, Silver cleaned parquet, rejected CSVs, Gold features, and `Docs/data_quality_report.md`. Rejected counts are explicit: 480 coordinate rows and 9,606 transaction rows. | **B -> A-**. This is now one of the stronger areas. |
| POI scraping robustness | Missing. Round 1 called this a major rubric miss. | Separate Geofabrik PBF pipeline with local pyrosm parsing, BallTree joins, 9 categories, coverage report, and no Overpass-per-outlet spam. Main pipeline merges POI if `poi_features.parquet` exists. | **D -> B** until run, **B+** after output exists. Good design, but optional runtime means judges may not see it unless run and reported. |
| Feature engineering for true demand signals | Mostly internal sales and outlet density; some demand/constraint confusion. | Better split: historical capability, capacity, plateau, internal catchment, cannibalisation, POI decay scores, seasonality, holidays. Still light on explicit "POI demand gap" inside constraint score. | **B- -> B+**. Much better, but not fully calibrated to external demand. |

# Minimal Stack Audit

Round 1 recommended:

| Recommended minimal stack | Shipped? | Verdict |
| --- | --- | --- |
| Manski bounds | **Yes**: `src/reporting/manski.py`, called by `run_pipeline.py`. | Good. This is the identification anchor. |
| External POI catchment layer | **Mostly**: separate POI pipeline and optional merge into Gold. | Good design, but operationally optional. Must run before final report. |
| ONE frontier model | **Mostly**: q90 multi-quantile frontier is the main model; SFA is blended in at 40% if it succeeds. | Slightly heavier than requested, but defensible if SFA is described as a secondary frontier signal, not a competing model zoo. |
| Calibrated constraint score | **Partly**: PCA + frontier residual + plateau with sigmoid is much cleaner than Round 1. | Better, but not truly calibrated against a labeled constraint target. Call it a constraint index, not a probability. |

The team did **not** badly over-engineer the executable pipeline. The over-engineering risk is in the prose: README claims SFA + CQR + censored QR + Manski + conformal intervals. In code, the actual run is q90 frontier + optional SFA blend + Manski + validation. That is acceptable. Just stop claiming unused CQR until it is wired.

Also fix stale docs before the PDF. `Docs/modeling_methodology.md` and `Docs/geospatial_catchment_features.md` still describe the old notebook-era score, old caps, old 914-row note, and missing POI. Do not cite them as current truth.

# Critical Path Status at Each Gate

| Gate | If `python run_pipeline.py` works, likely status | Bottleneck |
| --- | --- | --- |
| Hour 18 | Bronze/Silver/Gold and core modeling should be runnable. The team has a real 20,000-row CSV path, rejected records, lower bounds, quantiles, SFA attempt, caps, and validation outputs. | Dependency/runtime fragility: XGBoost 2.0, LightGBM fallback, scipy SFA convergence, parquet engine. |
| Hour 24 | POI should either be complete or explicitly dropped from the main claim. If POI ran first, Gold includes POI decay features and the story moves into B+/A- territory. | POI pipeline wall-clock and dependency setup: PBF download, pyrosm, geopandas/parquet stack. |
| Hour 30 | Results should include CSV, `manski_bands.csv`, validation report, DAG source/PNG fallback, sensitivity table, and run summary. | Validation failures and claim mismatch. Hard fails must beat aesthetics. |
| Hour 36 | Final deliverable should be a tight 5-page PDF plus CSV, README, AI log, and reports. | The PDF is the bottleneck. The code story exists, but it still needs a disciplined written narrative with only executed claims. |

If the pipeline runs cleanly, the team is not blocked on methodology anymore. They are blocked on packaging evidence into the final report.

# Report-readiness Map

| PDF section | Artifact now available | Readiness |
| --- | --- | --- |
| Cover | `README.md`, `Docs/challenge_brief.md`, `Results/run_summary.json`, final CSV path. | Needs final thesis line and team details. |
| Forensics (1 page) | `Docs/data_quality_report.md`, `data/bronze/_ingestion_audit.csv` after running, `data/silver_rejected/*.csv`, `src/quality/checks.py`, `src/cleaning/silver.py`. | Strong. Use a Bronze -> Silver -> rejected -> Gold waterfall. |
| POI (1 page) | `poi_pipeline/README.md`, `poi_pipeline/output/poi_coverage_report.md` after running, `poi_pipeline/output/poi_features.parquet`, `src/features/gold.py`. | Good if run. Weak if only described. |
| Causal logic (1.5 pages) | Round 1 reviews, research notes, `src/reporting/dag.py`, `Results/manski_bands.csv`, `Reports/figures/sensitivity_summary.md`, `src/modeling/sfa.py`, `src/modeling/censored_qr.py`, `src/modeling/predict.py`. | Strong core. Must remove or wire CQR claim before final. |
| GenAI log (0.5 page) | `Docs/ai_transparency_log.md`, `Reviews/council_review.md`, this Round 2 review, research files. | Needs update. Current AI log still says POI is remaining and references notebook-era artifacts. |

# The One Move

**Generate a single `Reports/final_methodology_manifest.md` from `run_pipeline.py`.**

It should be short and brutal:

- exact methods that actually ran;
- artifact paths produced;
- row counts and validation pass/fail;
- whether POI was present or absent;
- whether SFA converged;
- whether CQR intervals were produced;
- final allowed report claims.

This one move would push the grade highest because it closes the gap between architecture, code, and PDF. Judges reward a story they can audit. Right now the story is good, but some claims are still ahead of the executable evidence.

# The One Thing to Avoid

**Do not add more methods.**

No causal forest. No DEA. No Heckman. No deep Tobit. No extra ensemble layer.

The risk is not lack of sophistication anymore. The risk is incoherence by overclaiming. Finish the bounded-frontier story, run POI, update the AI log, and write the PDF from generated artifacts.
