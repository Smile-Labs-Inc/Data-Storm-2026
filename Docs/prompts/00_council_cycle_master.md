# Mission: AI Council Review + Fix Cycle for Data Storm 2026 (smile Labs)

## Context

Repo: `D:\projects\Data-Storm-2026\`
Team: smile Labs
Comp: OCTAVE - John Keells Group "Data Storm 7.0 - Storming Round" (Sri Lanka)
Goal: Predict latent maximum monthly purchase potential (liters) for 20,000
traditional retail outlets for January 2026. Observed sales are right-censored
(observed = min(true_demand, operational_constraint)). Judging is 100%
qualitative: 40% Data Engineering + 40% Methodology + 20% GenAI Workflow.

## Current state (as of the last cycle)

Council rounds R1-R4 are complete in `Reviews/`. R4 surfaced a rounding bug +
constrained-uplift floor issue; both are fixed. Validation passes 6/6:

```
V1 schema OK | V2 NaN/neg/dup OK | V3a IDs OK | V3b 0.00% below hist OK
V4 median uplift 1.250 OK | V5 cap-binding 0.00% OK
```

The v2 stack (notebooks 20/21/22 + 23 EDA, src/ modules, poi_pipeline/)
produces the canonical submission `Results/smile_labs_predictions.csv`.

## Your job

Run **Council Round N+1** (look at the highest existing `Reviews/council_round*/`
folder and increment) to find what's still leaving points on the table NOW that
validation passes. Then apply fixes, re-execute affected notebooks, verify.

## Pattern (do exactly this, in order)

### Step 1 -- Read prior context

Use Read on:

- `Reviews/council_review.md` (R1)
- `Reviews/council_round2/council_review_v2.md` (R2)
- `Reviews/council_round3/council_review_v3.md` (R3)
- `Reviews/council_round4/council_review_v4.md` (R4)
- `Results/validation_report.md` (current state)
- `Reports/final_report.md` (the v2 PDF source)

### Step 2 -- Launch 5 critics IN PARALLEL via the Task tool

Send one assistant message with 5 Task tool calls. DO NOT serialise.

Critic roster (mix premium models for diversity):

| Critic          | Model                               | Role                                                                                |
| --------------- | ----------------------------------- | ----------------------------------------------------------------------------------- |
| Gap Analyzer    | `claude-opus-4-7-thinking-xhigh`    | Map current state vs 40/40/20 rubric; ROI-rank fixes                                |
| Data Engineer   | `claude-4.6-sonnet-medium-thinking` | DE rubric scorecard + file hygiene + reproducibility                                |
| EDA Refiner     | `claude-opus-4-7-thinking-xhigh`    | Audit notebook 23 outputs + add missing analyses                                    |
| Modeling Critic | `claude-opus-4-7-thinking-xhigh`    | Run live diagnostics on `data/gold/predictions_v2.parquet` for any remaining issues |
| Business / Viva | `gpt-5.5-extra-high`                | 3-slide pitch + 5 hostile-judge Q&A + report polish                                 |

Use the per-critic prompts in this folder (`01_..` through `05_..`) as
the body of each Task call. Each critic must:

1. Read all 4+ prior council reviews + the current validation report.
2. Use Shell + Python to run real diagnostics where applicable. Use venv:
   `D:\projects\Data-Storm-2026\.venv\Scripts\python.exe`
3. Write its review file to: `Reviews/council_round<N+1>/0X_<role>_v<N+1>.md`
4. Return a 7-line summary in the response.

### Step 3 -- Write `Reviews/council_round<N+1>/council_review_v<N+1>.md`

Synthesize the 5 critic outputs. Structure:

- **Convergent Verdict** (consensus grade today + after fixes)
- **What R4 fixed that's still working** (verification table)
- **NEW issues found this round** (numbered, severity-tagged)
- **Tier 1 / 2 / 3 / 4 priorities** (ordered ROI list)
- **Critical-path plan** for the remaining time
- **Ship-or-fix decision matrix** (1h / 6h / 12h)

### Step 4 -- Apply fixes

Use `StrReplace` for `src/*.py` and `EditNotebook` for cells.
After fixes, ReadLints on touched files.

### Step 5 -- Re-execute notebooks via venv

The team venv has python 3.13 + pandas 2.3 + xgboost 3.2 + pyarrow 24.
Kernel is registered as `datastorm-venv`. To execute:

```powershell
D:\projects\Data-Storm-2026\.venv\Scripts\python.exe -m nbconvert ^
  --to notebook --execute --inplace ^
  --ExecutePreprocessor.timeout=900 ^
  --ExecutePreprocessor.kernel_name=datastorm-venv ^
  D:\projects\Data-Storm-2026\Notebooks\<file>.ipynb
```

Order depends on what was touched:

- `predict.py` / `constraint_score.py` / `frontier.py` / `sfa.py` changed -> re-run nb21 then nb22
- Only nb22 cells changed -> re-run nb22 only
- `gold.py` / `silver.py` / `checks.py` changed -> re-run nb20 -> nb21 -> nb22
- EDA only -> re-run nb23

Block until completion (~80s for nb20 or nb22; ~140s for nb21).

### Step 6 -- Read and report

Read updated `Results/validation_report.md`. If still 6/6 PASS, report numbers
and the new submission CSV head. If anything fails, mini-iterate ONCE
(targeted patch + re-run only nb22) before reporting back.

### Step 7 -- DO NOT

- Do NOT run any git command (commit / push / amend / rebase).
- Do NOT touch `Results/_legacy/` (it's the v1 backup; keep for audit).
- Do NOT touch `Docs/_archive/` (v1 PDF lives there for diff only).
- Do NOT modify the team's v1 notebooks (`01_`, `03_`, `04_`, `10_`, `11_`).
  All v2 work goes in notebooks 20/21/22/23.
- Do NOT run notebooks with Python 3.11 system kernel; only `datastorm-venv`.

## Deliverable

A final message with:

1. Council R<N+1> consensus grade today + after fixes
2. List of files modified (paths + 1-line each)
3. Notebooks re-executed (with timing)
4. Validation report 6 lines
5. Submission CSV head + row count
6. The single most-impactful next move (if any)

## Defaults

- 5 subagents in parallel (one Task batch)
- Premium models for thinking critics
- Validation V3b threshold 99%, V4 range [1.25, 2.2], V5 < 25%
- Submission policy: notebook 22 always overwrites
  `Results/smile_labs_predictions.csv` with v2 (Option B canonical release gate)
- Iteration: max 1 mini-iteration on V3b/V4 failure before reporting back
