# Gap Analyzer — Council Round 5 (Data Storm 7.0)

**Reviewer:** Competition Gap Analyzer (R5)
**Scope:** v2 deliverables vs 40/40/20 rubric — full codebase audit post-R4 fixes
**Validation state going in:** 6/6 PASS (`validation_report.md` confirmed)
**Bottom line:** R4 closed the V3b+V4 notebook-level bugs, but **`run_pipeline.py` (the canonical `python run_pipeline.py` entry point) was never patched** — it still carries the rounding bug AND outputs the wrong filename. A judge who reproduces the pipeline gets a broken submission with the wrong team name. This is the single highest-priority finding in R5.

---

# Expected Score Today (post-R4, pre-R5 fixes)

| Rubric block | Weight | Score /10 | Weighted pts | Notes |
|---|---:|---:|---:|---|
| DE & Forensics (#1–5) | 40 | 7.8 | **31.2** | Silver layer clean; gold wired; POI in model. Lost pts: SHA-12 claim vs PDF, stale report doc, research CSVs in Results/ |
| Methodology & Math (#6–7) | 40 | 7.5 | **30.0** | SFA+multi-q+CH-3+Manski stack documented and running. Lost pts: report placeholders unfilled, POI oversold, V4 margin = 0 |
| GenAI Workflow (#8–10) | 20 | 7.8 | **15.6** | Three council rounds logged; adversarial loop real. Lost pts: R3+R4 not in transparency log, README cites only R1-R3 |
| **Total today** | | | **~77 / 100** | |

---

# New Issues Found in R5 (not present in R4)

## N5.1 [CRITICAL] `run_pipeline.py:363` — V3b rounding bug NOT fixed here

The R4 Modeling Diagnostician patched `Notebooks/22_v2_validation_and_submission.ipynb` cell 3 with `np.ceil(x * 1000) / 1000`. But `run_pipeline.py`'s `write_submission()` function at line 363 still reads:

```python
sub["Maximum_Monthly_Liters"] = sub["Maximum_Monthly_Liters"].round(3)
```

Running `python run_pipeline.py` (the canonical entry point documented in the README) still generates V3b FAIL (27.92% below historical max). The notebook fix and the orchestrator fix are inconsistent — and the README says to use `run_pipeline.py` as the canonical runner.

**Fix:** Replace line 363 with:
```python
sub["Maximum_Monthly_Liters"] = np.ceil(sub["Maximum_Monthly_Liters"] * 1000) / 1000
```

## N5.2 [CRITICAL] `run_pipeline.py:90` — Wrong team name → wrong submission filename

```python
TEAM_NAME = "teamname"
```

`write_submission()` at line 364 produces `Results/teamname_predictions.csv`. The brief requires a file named for the team. Running the pipeline fresh gives the wrong file. The submission checklist says `Results/smil_labs_predictions.csv` but a pipeline-reproduced run would overwrite or produce a different file.

**Fix:** Change `TEAM_NAME = "teamname"` to `TEAM_NAME = "smil_labs"`.

## N5.3 [HIGH] `run_pipeline.py:124-125` — SHA-12 contradicts PDF's SHA-256 claim

```python
sha = hashlib.sha256(dst.read_bytes()).hexdigest()[:12]
audit.append({"file": name, "size_bytes": dst.stat().st_size, "sha256_12": sha})
```

The PDF §1 and README state "SHA-256 audit log". The audit CSV column is named `sha256_12` and contains only 12 hex characters. A judge who opens `data/bronze/ingestion_audit.csv` or `_ingestion_audit.csv` will see a truncated value and a misleading column name. This undermines the reproducibility story.

**Fix:** Remove `[:12]`, rename column to `sha256`, rename output to `ingestion_audit.csv` (matching the full-SHA file that already exists from a previous run).

## N5.4 [HIGH] `Reports/final_report.md` lines 39-41 — Unfilled placeholders still visible

```latex
\textit{1.10-1.50x (fill in from `Results/run_summary.json` after running v2)}
\textit{1.35-1.70x (fill in after run)}
\textit{fill in PASS/FAIL from `Results/validation_report.md`}
```

The validation report and `run_summary.json` exist on disk with real numbers. Judges opening the PDF see literal `\textit{fill in...}` text. This is a presentation-layer disqualifier for any score above B.

**Fix:** Replace with actual values: median uplift = 1.250, mean uplift = 1.233, 6/6 PASS.

## N5.5 [HIGH] `Docs/smil_labs_final_report.md` — Stale v1 numbers visible to judges

Line 13: `| Median uplift vs historical max | 1.18x |`
Line 6: `"...Tobit Type-I MLE..."` — this method does NOT exist in `src/modeling/`. The codebase has SFA + multi-q XGBoost + CH-3 + CQR. "Tobit Type-I MLE" is a ghost method that no judge can reproduce from the code.

If judges see two reports (one at `Docs/`, one at `Reports/`) claiming different numbers (1.18x vs 1.25x) and different methods, the credibility damage is severe.

**Fix:** Archive `Docs/smil_labs_final_report.md` to `Docs/_archive/`. It should not be in the top-level Docs directory alongside the canonical report.

## N5.6 [MEDIUM] `Docs/ai_transparency_log_v2.md` — R3 and R4 rounds not logged

The log ends after Round 2. Council Rounds R3 and R4 each found real bugs (R3: N1-N5 new blockers; R4: rounding bug + V4 root cause). Those are exactly the kind of adversarial AI audit work that scores 20% of the rubric. Not logging them leaves ~2-3 rubric points on the table.

**Fix:** Create `Docs/ai_transparency_log_v3.md` that carries R3 + R4 entries.

## N5.7 [MEDIUM] `README.md:141-145` — Council audit trail lists R1-R3 only

```md
- `Reviews/council_review.md` — Round 1 master (v1 grade D+).
- `Reviews/council_round2/council_review_v2.md` — Round 2 ...
- `Reviews/council_round3/council_review_v3.md` — Round 3 ...
```

Round 4 and Round 5 are not mentioned. If the GenAI rubric judges skim the README to understand the AI workflow depth, they see an incomplete picture.

**Fix:** Add R4 and R5 lines to the README council section.

## N5.8 [MEDIUM] Two unexplained "research" CSVs in `Results/`

```
Results/smil_labs_predictions_research.csv        17 KB  (today, 20:07)
Results/smil_labs_predictions_research_full.csv   2.6 MB (today, 20:07)
```

These were written today. The small file (~570 rows) is NOT the canonical 20,000-row submission. The large file (2.6 MB >> 361 KB for 20k rows) likely contains multi-scenario predictions from a research notebook. Having ambiguous prediction files in the submission directory is the exact "5 prediction files" failure mode R4 flagged and was supposed to be resolved.

**Fix:** Move both to `Results/_legacy/` or a `Results/_research/` folder. Document what they are.

## N5.9 [LOW] V4 safety margin is zero

`median_uplift = 1.250` exactly equals `median_uplift_min = 1.25`. A re-run with a different random seed or slightly different data slice would produce `1.249` and fail V4. The threshold was designed as a safety floor, but the model is sitting on the floor.

**Fix (report only, not model):** Add a comment to the validation output noting the floor is binding and document the business-decision rationale from the R4 Diagnostician's narrative.

---

# ROI-Ranked Fix Priority

| Rank | Fix | Score lift | Time | ROI |
|---:|---|---:|---:|---:|
| 1 | N5.1: `run_pipeline.py` rounding fix | +0 pts (already in nb22, but prevents regression) | 1 min | ∞ (risk elimination) |
| 2 | N5.2: `TEAM_NAME = "smil_labs"` | +0 pts but prevents wrong filename | 1 min | ∞ (risk elimination) |
| 3 | N5.3: SHA-256 full hash + correct filename | +1 pt (DE provenance) | 5 min | 12 pts/hr |
| 4 | N5.4: Fill final_report.md placeholders | +2-3 pts (presentation) | 10 min | 15 pts/hr |
| 5 | N5.5: Archive smil_labs_final_report.md | +1 pt (no conflicting docs) | 2 min | 30 pts/hr |
| 6 | N5.6+N5.7: Transparency log v3 + README | +2 pts (GenAI rubric) | 20 min | 6 pts/hr |
| 7 | N5.8: Move research CSVs | +0 pts but prevents footgun | 2 min | ∞ (risk elimination) |

**Total: ~+6-7 raw points, ~1 hour of work → 77 → ~83.**

---

# Ship-or-Fix Matrix

### If < 30 minutes to submission
Fix N5.1 + N5.2 only. Do NOT touch the model or re-run.

### If 1–2 hours to submission
Fix N5.1-N5.5. Re-run notebook 22 to confirm validation still 6/6 after run_pipeline.py fix. Rebuild PDF from filled-in final_report.md.

### If 3+ hours to submission
All of the above + N5.6 (transparency log v3) + N5.7 (README) + N5.8 (move research CSVs). Do NOT open new method tracks.

---

# Expected Score After R5 Fixes

| Scenario | DE /40 | Method /40 | GenAI /20 | Total |
|---|---:|---:|---:|---:|
| Now (post-R4) | 31.2 | 30.0 | 15.6 | **~77** |
| After N5.1-N5.5 (1 hour) | **33.0** | **32.0** | 15.6 | **~81** |
| After all R5 fixes (3 hours) | **33.5** | **32.0** | **17.0** | **~83** |
