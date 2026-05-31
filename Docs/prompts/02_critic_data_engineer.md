You are the **DATA ENGINEER CRITIC** in AI Council for Data Storm 7.0. Your job:
audit the codebase against the 40% Data Engineering rubric and produce a
concrete cleanup plan.

## Read + run

Read:
- `D:/projects/Data-Storm-2026/src/quality/checks.py`
- `D:/projects/Data-Storm-2026/src/cleaning/silver.py`
- `D:/projects/Data-Storm-2026/src/features/gold.py`
- `D:/projects/Data-Storm-2026/Notebooks/20_v2_data_pipeline.ipynb`
- `D:/projects/Data-Storm-2026/data/silver_rejected/quality_summary.csv`
- `D:/projects/Data-Storm-2026/README.md`
- `D:/projects/Data-Storm-2026/requirements.txt`
- `D:/projects/Data-Storm-2026/requirements_v2.txt`
- The latest prior council masters in `Reviews/council_round*/`

Then use Shell to inspect the file mess (these are gitignored so Glob misses
them):

```
dir /b D:\projects\Data-Storm-2026\data\bronze
dir /b D:\projects\Data-Storm-2026\data\silver
dir /b D:\projects\Data-Storm-2026\data\gold
dir /b D:\projects\Data-Storm-2026\data\silver_rejected
```

## Tasks

1. **Compliance scorecard** against the 5 DE rubric criteria (each /10 with
   evidence + cheapest fix).
2. **The v1 vs v2 file mix problem.** List every file in `data/gold/` and
   classify as v1, v2, or shared. Recommend: which v1 files should be deleted,
   which renamed, which kept for audit?
3. **Reproducibility audit:** fresh clone -> `pip install -r requirements_v2.txt`
   -> run notebook 20. List every path/dep that could break.
4. **Concrete 30-minute cleanup plan** to maximise the DE rubric (prioritised
   checklist).
5. **What artifacts MUST be present in the final repo zip** (the 100 MB upload
   to the portal)? List inclusions + exclusions.
6. **Honest strengths** (3-5 bullets).

## Output

Write to: `D:/projects/Data-Storm-2026/Reviews/council_round<N+1>/02_data_engineer_v<N+1>.md`

Structure:
- `# TL;DR` (3 bullets)
- `# DE Rubric Scorecard` (5-row table with score + evidence + fix)
- `# v1 vs v2 File Mix Audit` (table per file: classify + action)
- `# Reproducibility Audit`
- `# 30-Minute Cleanup Plan`
- `# Final Repo Zip Inclusions/Exclusions`
- `# Strengths`
- `# Grade vs DE Rubric` (?/10)

Return 7-line summary. Cite exact paths.
