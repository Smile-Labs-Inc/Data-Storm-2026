# Archived v1 documents

These are kept for audit / diff only. They describe the **v1 pipeline** (notebook 01) and contain numbers and conventions that **contradict the v2 stack**:

- `row_id` column name (v2 uses `Outlet_ID` per the official PDF)
- 914-row submission (v2 uses 20,000)
- median uplift 1.18x (v2: see `Results/validation_report.md` after re-running notebook 22)
- constraint_score with `valid_coordinate_rank` (v2: PCA + frontier-residual + plateau composite)

**Do NOT cite these in the 5-page PDF report.** The canonical methodology source is `Reports/final_report.md` after notebook 22 has been re-executed with the council R4 fixes.

| File | Why archived |
|---|---|
| `final_report_v1.pdf` | written by the v1 pipeline; describes the broken median-uplift 1.18x story |
| `final_report_draft_v1.md` | source of `final_report_v1.pdf` |

The current canonical narrative lives in `../../Reports/final_report.md`.
