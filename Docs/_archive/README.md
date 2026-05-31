# Archived v1 documents

These are kept for audit / diff only. They describe the **v1 pipeline** (notebook 01) and contain numbers and conventions that **contradict the v2 stack**:

- `row_id` column name (v2 uses `Outlet_ID` per the official PDF)
- 914-row submission (v2 uses 20,000)
- median uplift 1.18x (v2: see `Results/validation_report.md` after re-running notebook 22)
- constraint_score with `valid_coordinate_rank` (v2: PCA + frontier-residual + plateau composite)

**Do NOT cite these in the 5-page PDF report.** The canonical methodology source is `Reports/final_report.md` after notebook 22 has been re-executed with the council R4 fixes.

| File                            | Why archived                                                                                                                                                                    |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `final_report_v1.pdf`           | written by the v1 pipeline; describes the broken median-uplift 1.18x story                                                                                                      |
| `final_report_draft_v1.md`      | source of `final_report_v1.pdf`                                                                                                                                                 |
| `smile_labs_final_report_v1.md` | early v1 narrative; cites "Tobit Type-I MLE" (no `src/modeling/tobit.py` exists) and median-uplift `1.18x` (canonical: `1.250x`). Archived in R7 per council R5 N5.5 / R6 N6.1. |
| `ai_transparency_log_v1.md`     | initial AI usage log (pre-council). Superseded by `../ai_transparency_log.md` which covers R1-R7.                                                                               |
| `ai_transparency_log_v2.md`     | second-pass AI log covering R1+R2 only. Superseded by `../ai_transparency_log.md`.                                                                                              |
| `next_steps_after_eda.md`       | mid-v1 planning notes; the listed next steps were executed across R1-R7 and the EDA findings are now in `../eda_summary.md`.                                                    |

The current canonical narrative lives in `../../Reports/final_report.md` (markdown source) and `../../Reports/final_report_v3.pdf` (built deliverable). The canonical AI log is `../ai_transparency_log.md`.
