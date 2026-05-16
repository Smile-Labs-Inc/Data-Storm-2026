# Skeptic Review v3 — Data Storm 7.0 (Council Round 3)

> R1 grade was D+. R2 grade was B-. v2 notebooks (`20`, `21`, `22`) now narrate a coherent latent-demand story.
> My job in R3: ignore the architecture; audit the gap between what the v2 notebooks **claim** and what they
> will **actually produce on a teammate's laptop in the panicked final 6 hours of the hackathon**.

---

# TL;DR

- **Ship probability under hackathon time pressure is ~30%, not the ~80% the v2 notebooks read like.** Six gates must all hold and four of them are quietly broken right now: (G1) raw data placed in `Datasets/`, (G2) deps installed — but `requirements.txt` lines 1-6 still pin only `pandas, numpy, scikit-learn, openpyxl, requests, reportlab`; the v2 deps live in a _separate_ file `requirements_v2.txt` that the top-level `README.md:39` does not reference, (G3) the POI pipeline produces `poi_pipeline/output/poi_features.parquet` — currently the `output/` directory does not exist, (G4) notebooks 20→21→22 execute in order — `data/{bronze,silver,silver_rejected,gold}/` are all empty except for `.gitkeep`, so the v2 pipeline has **never been run end-to-end even by the team that wrote it**, (G5) someone manually overwrites `smile_labs_predictions.csv` with the v2 file, (G6) someone rewrites `Docs/final_report_draft.md` (still 100% v1 numbers) and re-renders the PDF. Joint probability: ~0.30. The remaining 70% splits across "partial ship with mismatched PDF" (~25%), "v1 uploaded by muscle memory" (~20%), and "POI silently absent" (~15%).
- **The repo's front door still says v1.** `README.md:9-11` lists `01_latent_potential_pipeline.ipynb / 03_poi_enrichment.ipynb / 04_model_validation.ipynb` as "Key files". `README.md:39` says `pip install -r requirements.txt` (the broken short list). `README.md:86` says the submission columns are `row_id` + `Maximum_Monthly_Liters`. `README.md:89` literally writes _"The current platform validator expects 914 rows. ... it creates a 914-row fallback from the first sorted outlet IDs so the file matches the row-count gate."_ A judge or last-minute teammate who opens the repo's `README.md` first is sent straight back to v1.
- **Three previously-unflagged code bugs in the v2 stack.** (1) `src/reporting/manski.py:54-61` merges `cap_table` with `suffixes=("", "_cap")`, but `predict.latent_potential()` already returns `cap_uplift` as a column. The merge silently no-ops: `df["cap_uplift"]` keeps the **original** value from the predictions frame and the cap_table-derived column lives at `cap_uplift_cap`, ignored. (2) `src/reporting/manski.py:70` _clips_ the point estimate inside `[manski_lower, manski_upper]`. The `manski_bands_v2.csv` "point" column can therefore disagree with `smile_labs_predictions_v2.csv` "Maximum_Monthly_Liters" for any outlet where the v2 prediction sits outside the Manski interval — a judge cross-checking the two CSVs sees inconsistent answers for the same outlet. (3) Notebook 22 cell 3 runs the `assert not sub["Maximum_Monthly_Liters"].isna().any()` **before** reindexing to `outlet_master`. If any `Outlet_ID` in `outlet_master.csv` is missing from `preds`, the merge in the next line introduces silent NaNs that bypass all four asserts, and `to_csv` writes them out as empty cells.

---

# Probability of a Clean Ship (Honest Math)

I am being deliberately uncharitable. A hackathon team is sleep-deprived and divergent-attention by design.

| Gate                               | What must happen on the day                                                                                         | Evidence today                                                                                                                                                                                                                                                                                                                                                 | Honest P | Failure mode                                                                                                                                                        |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **G1: raw data placed**            | `Datasets/outlet_master.csv` + 4 siblings exist on the team's machine                                               | The folder isn't checked in (intentional, file size). v2 notebook 20 has an `ALT_RAW_DIR = ROOT.parent / "Logical" / "logical-context" / "autokaggle" / "datastorm-7-0-rotaract"` fallback that is **specific to a reviewer machine**. On a teammate machine that path doesn't exist either → `raise FileNotFoundError(f"raw file missing: {src}")` in cell 4. | **0.85** | Tomorrow morning teammate runs notebook 20, hits the FileNotFoundError, asks where to put files.                                                                    |
| **G2: deps installed**             | All v2 modeling deps actually available in the active venv                                                          | `requirements.txt` (the one the README points to) has 6 packages, none of `pyarrow / scipy / xgboost / lightgbm / pyrosm / geopandas / mapie` that the v2 imports use. `requirements_v2.txt` has the right list but **no doc in the repo says to use it**.                                                                                                     | **0.70** | Notebook 20 cell 11 raises on `to_parquet` (no pyarrow); or notebook 21 cell 9 raises on `from xgboost import ...`.                                                 |
| **G3: POI pipeline runs**          | All 4 scripts in `poi_pipeline/` → `poi_pipeline/output/poi_features.parquet` exists; notebook 20 cell 15 finds it. | `poi_pipeline/output/` directory does not exist. `poi_pipeline/data/pois/` contains only `schools.parquet` and `transport_hubs.parquet` — 2 of the 9 categories the methodology promises. The PBF is downloaded (142 MB) so step 1 worked, but step 2 (extract POIs for all 9 categories) is **incomplete**.                                                   | **0.55** | Team runs `03_build_features.py` → produces a parquet with 2 decay scores instead of ~9-15, the methodology bullet about "9 POI categories" becomes false silently. |
| **G4: 3 notebooks run in order**   | 20 → 21 → 22 fully executes; outputs land in `data/silver_rejected/`, `data/gold/`, `Results/`                      | All of `data/bronze/`, `data/silver/`, `data/silver_rejected/`, `data/gold/` contain only `.gitkeep`. **The v2 pipeline has demonstrably never been run end-to-end** — not even by the people who wrote the v2 notebooks. So there are zero observed runtime errors recorded anywhere.                                                                         | **0.65** | A cell raises something the author never saw (KeyError on a column rename, SFA `scipy.optimize` non-convergence, OOM on the multi-quantile fit, etc.).              |
| **G5: canonical file overwritten** | `Results/smile_labs_predictions.csv` overwritten with v2 contents; v1 archived.                                     | Notebook 22 cell 0 is explicit: _"Submission policy (Option A — non-destructive): Writes to `Results/smile_labs_predictions_v2.csv` (does NOT overwrite `smile_labs_predictions.csv`)."_ The cutover is a manual `copy` command in cell 16's markdown.                                                                                                         | **0.70** | Team uploads `smile_labs_predictions.csv` from muscle memory → 914 rows + `row_id` → disqualifier. See Scenario C below.                                            |
| **G6: PDF rewritten**              | `Docs/final_report_draft.md` / `Docs/final_report.pdf` updated from v1 numbers to v2 numbers.                       | The draft is 100% v1 — `914`, `row_id`, `1.18x median uplift`, `lower_bound = max(historical_max, january_max, recent_3_month_max)`, `coordinate availability` in the constraint score. None of this is what v2 does.                                                                                                                                          | **0.60** | Team ships v2 CSV + v1 PDF → judge spots contradiction in 30 seconds.                                                                                               |

**Joint clean-ship probability: 0.85 × 0.70 × 0.55 × 0.65 × 0.70 × 0.60 ≈ 0.10**.

Adding a generous "the team reads the council reviews and prioritises the packaging fix" multiplier of 3× pushes the floor to ~0.30. **My honest estimate: ~30% probability of a clean v2 ship across all 6 gates.** The remaining 70% splits roughly:

- ~25% partial v2 ship (POI partial, PDF mismatched) → realised grade B-/B.
- ~20% v2 model runs but the **wrong CSV** gets uploaded (Scenario C below) → disqualifier or near-disqualifier.
- ~15% pipeline fails on the day (G2 or G4) and the team falls back to v1.
- ~10% spread across edge cases (NaN-in-CSV escape — see Theatre Audit §4 — or POI silent absence with overclaim).

This is not pessimism. This is what the filesystem says.

---

# v2 Theatre Audit

## 1) Notebook 21 cell ordering — q90 IS correctly fit on uncensored only; q50/q75/q95 are NOT

I verified the cell ordering against the notebook JSON.

- **Cell 7**: `delta` proxy → `X_train, y_train, corr = chernozhukov_hong_correction(X, y, delta, propensity_threshold=0.10)`. Per `src/modeling/censored_qr.py:108-143`, this returns `X.loc[keep_mask]` and `y.loc[keep_mask]` where `keep_mask = p_censored < 0.10`. So `X_train, y_train` are filtered to the low-censoring sub-population.
- **Cell 9**: `model_bundle = fit_multi_quantile(X_train, y_train, quantiles=(0.50, 0.75, 0.90, 0.95))`.

**Verdict for q90 (the frontier): CORRECT.** This is the actual R1 M4 / R2 carry-over fix. The frontier quantile is no longer trained on capped sales. The CH-3 correction is real preprocessing, not theatre.

**Verdict for q50, q75, q95: WRONG.** The conditional median is identified on the full sample; filtering to uncensored-only biases the median of the _retained_ outlets upward, because you've thrown out the high-demand-and-capped left tail of the response. Then cell 21 picks `q_lo_col = "q50"` and `q_hi_col = "q95"` for CQR:

```python
q_lo_col = "q50"   # use q50 as the lower edge -- conservative
q_hi_col = "q95"
```

So the calibrated `cqr_lower` is **not** a `[q05, q95]` band — it is a `[biased_q50, q95]` band. The cell 25 markdown summary calls it "calibrated `[q05, q95]` interval"; the actual quantile list `(0.50, 0.75, 0.90, 0.95)` has no `0.05` head in it at all. Three independent factual errors in one cell:

1. `q50` used where the surrounding text says `q05`.
2. `q50` itself is fit on the wrong subset.
3. The CQR is labelled "calibrated `[q05, q95]`" but the calibration data inherit the same upward bias.

**10-minute fix**: split the call into two — `fit_multi_quantile(X, y, quantiles=(0.05, 0.50, 0.75, 0.95))` on the full sample, and `fit_multi_quantile(X_train, y_train, quantiles=(0.90,))` on the CH-filtered subset. Then cell 21 uses `q_lo_col = "q05"`.

## 2) Notebook 22 is additive (footgun), not replacing (release gate)

Quoting cell 0 of `22_v2_validation_and_submission.ipynb`:

> **Submission policy (Option A — non-destructive):** Writes to `Results/smile_labs_predictions_v2.csv` (does **not** overwrite `smile_labs_predictions.csv`). You can compare side-by-side and choose which to upload. The team's existing `smile_labs_predictions.csv` is **not** touched by this notebook.

And cell 3:

```python
sub_path = RESULTS_DIR / "smile_labs_predictions_v2.csv"
sub.to_csv(sub_path, index=False)
sub.to_csv(RESULTS_DIR / "smile_labs_predictions_full_20000_v2.csv", index=False)
```

The v1 files I verified on disk right now:

```text
Results/smile_labs_predictions.csv          → 915 lines, header "row_id,Maximum_Monthly_Liters", 914 data rows OUT_00001..OUT_00914
Results/smile_labs_predictions_full_20000.csv → 20,001 lines, header STILL "row_id,Maximum_Monthly_Liters" (wrong schema)
```

The "full 20k" v1 file is the worst trap. A stressed teammate who quickly checks "20k rows? sure, this must be the right one" still uploads the **wrong column name** and gets either rejected on schema or silently mis-scored.

Cell 16 markdown then tells the team:

> ```powershell
> copy Results\smile_labs_predictions_v2.csv Results\smile_labs_predictions.csv
> ```
>
> (or upload `smile_labs_predictions_v2.csv` directly).
> **Before you submit, verify with the portal whether the 914-row constraint is real. If the portal accepts only 914 rows, filter `smile_labs_predictions_v2.csv` to whatever `Outlet_ID` list the portal expects.**

A friendly skeptic's reading: this is responsible disclosure. A hostile skeptic's reading: at hour 33 of 36, this paragraph makes the team second-guess uploading the 20,000-row file. Some non-zero fraction grabs the familiar 914-row v1 instead, "just to be safe with the validator." The single highest realistic loss in the entire 36 hours.

**Fix**: make cell 16 destructive by default. Five lines:

```python
import shutil
LEGACY = RESULTS_DIR / "_legacy_do_not_submit"; LEGACY.mkdir(exist_ok=True)
for f in ("smile_labs_predictions.csv", "smile_labs_predictions_full_20000.csv"):
    p = RESULTS_DIR / f
    if p.exists():
        shutil.move(p, LEGACY / f.replace(".csv", "_v1.csv"))
shutil.copy(RESULTS_DIR / "smile_labs_predictions_v2.csv", RESULTS_DIR / "smile_labs_predictions.csv")
```

Run by default. Notebook 22 should be the release gate, not a polite suggestion.

## 3) Will SFA converge, or silently fall back to pure XGBoost?

Notebook 21 cell 11 has the now-correct feature set — the four leaky `observed_*` columns are removed by `leaky_cols = {...}` before `fit_sfa`. R2 N3 is genuinely fixed in code.

Honest convergence expectations:

- **If POI features are present** (~9-15 `*_decay_score` columns): SFA on `log(observed_max) ~ ~25 features` over 20,000 outlets has ample degrees of freedom. `scipy.optimize.minimize` on the half-normal log-likelihood should converge on most starts. **P(convergence) ≈ 0.80.**
- **If POI features are absent** (likely, given that `poi_pipeline/data/pois/` has only 2 of 9 categories right now): SFA on 14 features against `log(observed_max)`. Three of those features (`Cooler_Count, sku_breadth, transaction_count`) explain most of the variance and are tightly correlated with each other. `sigma_u` is more fragile to identify. **P(convergence) ≈ 0.65.**
- **Silent failure cushion**: cell 11 wraps the fit in `try/except Exception as e: print(...); sfa_ok = False`. Cell 13 then writes _"SFA fit failed → using pure XGBoost q90 frontier."_ and continues. The print is visible in the notebook output but `predictions_v2.parquet` is still written with the pure-q90 frontier; the README and PDF claim about "60/40 ensemble" then becomes false silently.
- **Even on convergence**, the 60/40 ensemble is a `0.6 * q90 + 0.4 * exp(X·β)` blend over essentially the same feature set. The marginal lift over pure q90 is plausibly < 5% on point predictions. The methodology bullet is more impressive in the PDF than in the data.

**Honest answer**: SFA will probably converge. The 60/40 ensemble is largely cosmetic. The actual value of SFA is the team being able to answer "what's your σ_u?" with a real number — not the ensemble term.

## 4) Does the Manski upper bound ever bind, and is the implementation even correct?

Two problems, one new, one re-flagged.

### 4a) NEW BUG: the cap_table merge in `manski.py` is silently a no-op

```54:61:D:/projects/Data-Storm-2026/src/reporting/manski.py
    if cap_table is not None:
        df = df.merge(
            cap_table[["Outlet_Type", "Outlet_Size", "cap_uplift"]],
            on=["Outlet_Type", "Outlet_Size"],
            how="left",
            suffixes=("", "_cap"),
        )
        cap = df["cap_uplift"].fillna(max_uplift)
```

`compute_manski_bands` is called from notebook 21 cell 23 with `preds` (the output of `latent_potential`). Per `src/modeling/predict.py:79-92`, `latent_potential` returns a DataFrame that **already contains a `cap_uplift` column** (inherited from `apply_caps`). So when `compute_manski_bands` merges in `cap_table`'s `cap_uplift` with `suffixes=("", "_cap")`, the cap_table column lands at `cap_uplift_cap`. The very next line then reads `df["cap_uplift"]` — which is the **original** column already on the frame, _not_ the cap_table-derived one. The `cap_table` parameter is silently ignored.

Consequence: the "empirical bootstrap cap" claim for the Manski upper is doubly hollow — the cap_table you pass in is never consulted, and even if it were, it would only be used for the `lower_bound × cap` branch (a 6.0 hardcoded ceiling otherwise).

**Fix**: rename the merge `suffixes=("_pred", "_cap")` and explicitly read `df["cap_uplift_cap"]`. 2-line fix.

### 4b) NEW BUG: `manski.py:70` rewrites the point estimate

```70:72:D:/projects/Data-Storm-2026/src/reporting/manski.py
    df["point"] = df["Maximum_Monthly_Liters"]
    df["point"] = np.clip(df["point"], df["manski_lower"], df["manski_upper"])
```

The clip silently mutates the point estimate to fit inside the Manski interval. Two things follow:

1. For any outlet where `manski_upper < Maximum_Monthly_Liters`, the **`point` column in `manski_bands_v2.csv` disagrees with the `Maximum_Monthly_Liters` column in `smile_labs_predictions_v2.csv`** for the same `Outlet_ID`. A judge cross-checking the two CSVs sees the team providing two different numerical answers for the same outlet.
2. For small outlets where `manski_upper = max(peer_p99, lower_bound × cap_uplift_from_pred)` happens to fall below the v2 point, the report-displayed point estimate is **lower** than the submitted point estimate. Visually this looks fine until a judge sums column differences.

**Fix**: don't clip. Add a separate `point_clipped_to_manski` column if the team really wants to show "what would the point be if we enforced the band". Keep the submission's `Maximum_Monthly_Liters` as the canonical point.

### 4c) Re-flagged from R2: "Manski" is still a misnomer

Per `src/reporting/manski.py:25-67`:

```python
DEFAULT_MAX_UPLIFT = 6.0  # absolute ceiling on multiplier vs lower bound
...
upper_a = peer_p99.fillna(df["observed_max_monthly_liters"])
upper_b = df["lower_bound"] * np.minimum(cap, max_uplift)
df["manski_upper"] = np.maximum(upper_a, upper_b)
```

A real Manski (1990) partial-identification upper requires an exogenous identifying assumption. `max(peer_p99, lb × cap)` is an empirical demand band with a famous label glued on. A hostile viva-killing question writes itself: _"What identifying assumption gives you that upper, and where in the code is it enforced?"_

**Fix**: either anchor the upper to SFA's `1/TE_q10` (model-based, defensible) or rename to "empirical demand band" and stop saying "Manski".

## 5) NEW BUG: Notebook 22 cell 3 asserts run BEFORE the reindex that can introduce NaNs

```python
sub = preds[["Outlet_ID", "Maximum_Monthly_Liters"]].copy()
sub["Maximum_Monthly_Liters"] = sub["Maximum_Monthly_Liters"].round(3)

# Sanity guards before writing
assert "Outlet_ID" in sub.columns, "FATAL: column must be Outlet_ID per official PDF"
assert sub["Outlet_ID"].is_unique, "FATAL: duplicate Outlet_IDs"
assert not sub["Maximum_Monthly_Liters"].isna().any(), "FATAL: NaN in predictions"
assert (sub["Maximum_Monthly_Liters"] >= 0).all(), "FATAL: negative predictions"

# Reindex to outlet_master order (deterministic)
sub = outlet_master[["Outlet_ID"]].merge(sub, on="Outlet_ID", how="left")
print(f"Submission shape: {sub.shape}")
```

The four asserts run on `preds`, then `sub` is **replaced** by a left-merge against `outlet_master`. Any `Outlet_ID` present in `outlet_master.csv` but missing from `preds` lands as a NaN in `Maximum_Monthly_Liters`. The asserts have already passed; `to_csv` writes the NaN row as an empty cell. The portal then rejects either on schema (NaN parse) or on row-count (some validators count non-NaN rows).

This is unlikely to bite _if_ the gold features for all 20k outlets were built upstream. But if any outlet had no transaction history (or was excluded by silver cleaning's referential integrity check), it would silently disappear from `preds` and reappear as a NaN row here.

**Fix**: move the four asserts to **after** the reindex, and add a fifth: `assert len(sub) == 20_000`. Two-line change.

## 6) `data/silver_rejected/` is the original B3 blocker, still empty

`Glob D:/projects/Data-Storm-2026/data/silver_rejected/*.csv` returns zero files. Only `.gitkeep` exists. Same for `data/bronze/`, `data/silver/`, `data/gold/`. The v2 stack has **never been run end-to-end on this machine** — not even by the team that wrote the notebooks. This means:

- The notebook authors have not actually observed the runtime errors (G4 risk).
- The "9,606 rejected transactions, 480 rejected coordinates" claim in `final_report_draft.md:41` is a v1 number, never re-verified by the v2 pipeline.
- The R1 blocker B3 ("rejected store invisible to a reviewer") **regresses to fail** if a judge unzips the submission and looks at `data/silver_rejected/`.

---

# PDF Inconsistency Risk

`Docs/final_report_draft.md` is 100% v1. Concrete instances:

- **Line 8-9**: `Final Platform Output: Results/smile_labs_predictions.csv` (the 914-row file) / `Full Business Output: Results/smile_labs_predictions_full_20000.csv` (the 20k file with `row_id` schema).
- **Line 67**: `lower_bound = max(historical_max, january_max, recent_3_month_max)`. **v2 actually uses 3rd-highest month** (see `src/modeling/lower_bound.py` and notebook 21 cell 3).
- **Lines 74-82**: constraint score components list `structural capacity rank`, `cooler count rank`, `SKU breadth rank`, `catchment density rank`, `POI demand score`, **`coordinate availability`** (the killed DQ flag), `plateau behavior`. **v2 uses PCA + frontier-residual + plateau** (see `src/modeling/constraint_score.py` and notebook 21 cell 15). The two DO NOT MATCH.
- **Lines 96-105 (validation table)**:

| Metric                         | v1 PDF   | v2 expectation (per notebook 21 cell 19)        |
| ------------------------------ | -------- | ----------------------------------------------- |
| Platform output rows           | 914      | 20,000                                          |
| Mean potential                 | 445.34 L | TBD (no number recorded — pipeline not yet run) |
| Median potential               | 259.77 L | TBD                                             |
| Mean uplift vs observed max    | 1.36x    | "council target after fixes: 1.6-1.9x"          |
| Median uplift vs observed max  | 1.18x    | "council target after fixes: 1.4-1.7x"          |
| Maximum uplift vs observed max | 2.97x    | TBD                                             |

- **Line 107**: _"The final platform file is `Results/smile_labs_predictions.csv` with columns `row_id` and `Maximum_Monthly_Liters`."_ **Wrong column name per the official PDF.**
- **Line 111**: _"the platform validator expects 914 rows. The current platform file uses the 914-row fallback. If the official sample/test template becomes available, rerun `Notebooks/03_poi_enrichment.ipynb` and `Notebooks/01_latent_potential_pipeline.ipynb`"_. v1 notebook references.

**And the front-page `README.md` agrees with the PDF, not with v2.** Lines 9-11 list v1 notebooks. Line 39 says `pip install -r requirements.txt` (the short, broken list). Line 86: _"`row_id` - outlet identifier expected by the competition validator."_ Line 89: _"The current platform validator expects 914 rows."_

**Will judges spot the contradiction?** A competent judge cross-checking the PDF cover page against the submission CSV column header catches this in 30 seconds. Once they have one contradiction in hand they look for more: lower_bound formula mismatch (PDF vs code), constraint components mismatch (PDF vs code), row count mismatch (PDF vs file). Three or four contradictions in a single review pass and the judge stops trusting any number in the report.

**Severity**: **CRITICAL**. The PDF + repo README together are the 30%-weight rubric artifact. A contradicting front-door doesn't "just lose writing points" — it makes the judge doubt every other number.

**Required fix before submission**:

1. Delete or `git mv` `README.md` to `README_v1.md`; rename `README_v2.md` to `README.md`.
2. Delete or move `Docs/final_report_draft.md` and `Docs/final_report.pdf` to `Docs/_legacy/`.
3. Write `Reports/final_report.md` from scratch using only v2 numbers (after notebook 21 cell 19 has actually printed them). Re-render the PDF.
4. Add a fatal-by-default check in notebook 22: read all `.md` files in `Docs/` and `Reports/`; if any of `914`, `row_id`, `january_max`, `recent_3_month_max`, `coordinate availability` strings appear, raise `RuntimeError` and refuse to write the submission.

---

# 5 Killer Judge Questions the v2 Notebooks Introduce

> Defensible answers assume the team applies the fixes I list. Without the fixes, the answers are aspirational.

### Q1. "Notebook 21 cell 9 fits q50, q75, q90, q95 on the same Chernozhukov-Hong–filtered subset. The CH correction is for the frontier quantile, not the conditional median. Why is your median trained on data filtered for low censoring propensity?"

**Defensible answer**: it isn't — that was a wiring bug. We split cell 9 into two fits. `q90` is fit on the CH-filtered subset (to remove downward censoring bias on the frontier), and `q05/q50/q75/q95` are fit on the full sample (because the conditional median is well-identified everywhere and we need a real `q05` head for the CQR interval). The CQR file in `Results/conformal_intervals_v2.csv` was regenerated after the fix; empirical calibration coverage is still ≥ 90%.

**Time to fix**: 10 minutes in cell 9, 5 minutes to rerun downstream.

### Q2. "Your `manski_bands_v2.csv` shows different `point` values for some outlets than your submission CSV. Which file is your actual answer? And why does the Manski upper sometimes fall below the v2 point?"

**Defensible answer**: the submission CSV is the canonical point estimate. We discovered in pre-flight that `compute_manski_bands` was clipping the point estimate to the Manski interval (`manski.py:70`), and that the cap_table parameter was being silently dropped due to a merge-suffixes name collision with the `cap_uplift` column already on the predictions frame (`manski.py:54-61`). Both were fixed. After the fix the upper is `peer_p99` for ~all outlets and the point is no longer clipped.

**The honest answer if the fix isn't made**: the report cannot use the Manski section at all. Drop it.

### Q3. "Your `README.md` line 9-11 lists Notebooks 01/03/04 as 'Key files', line 39 says `pip install -r requirements.txt` which has only 6 packages and is missing all the v2 modeling dependencies, and line 86 says the submission columns are `row_id` and `Maximum_Monthly_Liters`. Are you submitting v1 or v2?"

**Defensible answer**: v2. The repository's README has been updated to point to Notebooks 20/21/22 and to `requirements_v2.txt`. The v1 README was archived to `README_v1.md`. The v1 PDF was moved to `Docs/_legacy/`. _(Today: none of this is true. The repo's front door still says v1 in three independent places.)_

### Q4. "Your prediction floor is `observed_max_monthly_liters` (`predict.py:59-64`), which means the model can never reduce a prediction below the historical max of an outlet. For an outlet whose historical max came from a Sinhala/Tamil New Year (Avurudu) spike or a single distributor error, you bake that outlier permanently into the floor. How does that interact with your data-quality story?"

**Defensible answer**: we use `lower_bound = max(3rd-highest-month, median_history)` as the _modeling_ floor (`src/modeling/lower_bound.py`), and only floor the _final_ prediction at `observed_max` to satisfy the V3b auto-validation that 99% of predictions are at-or-above demonstrated max. For outlets where `observed_max - 3rd_highest > 2σ`, we generate an outlier-floor audit CSV and the top-10 are manually inspected. The audit shows `<N>` flagged outlets across all 20,000, and the typical excess is `<X>%`. _(Today: this audit CSV does not exist; notebook 22 writes top-100-by-potential and top-100-by-uplift, not top-N-by-outlier-floor. 15 minutes to add.)_

### Q5. "You claim a 60/40 XGBoost q90 + SFA frontier ensemble. The code in notebook 21 cell 11 has `try/except Exception as e: print(...); sfa_ok = False`. If SFA failed silently in your final run, your CSV is pure-q90. How do we, as judges, know which model produced the file you uploaded?"

**Defensible answer**: notebook 22 writes `Results/run_manifest.json` recording `{poi_features_present, n_poi_features, sfa_converged, sigma_u, sigma_v, lambda, cqr_target_coverage, cqr_empirical_coverage, censoring_kept_pct, n_outlets_predicted}`. The README and PDF cite the manifest values verbatim, so the claim about the ensemble is always reproducible from a file in the zip. _(Today: no manifest exists. Notebook 22 prints these values to stdout only. 20 minutes to add.)_

---

# Pre-mortem A / B / C

### A. Team forgets the PDF update

- **What happens**: notebooks 20/21/22 all run cleanly. `smile_labs_predictions.csv` is overwritten with v2 contents (20k rows, `Outlet_ID`). Portal validation passes. PDF in the submission zip still says `Platform output rows: 914`, `Median uplift 1.18x`, `lower_bound = max(historical_max, january_max, recent_3_month_max)`, `coordinate availability` in the constraint score. `README.md` still points to Notebook 01 and to `requirements.txt`.
- **Severity**: **CRITICAL on the 30% report rubric, CASCADING to the 30% methodology rubric.** A judge reading the PDF, then opening `src/modeling/lower_bound.py` or `constraint_score.py`, finds direct contradictions. They conclude either (a) the PDF documents an older version of the code, or (b) the code does not do what the PDF says. Either interpretation costs methodology points. Likely realised grade hit: **-10 to -15** from the model's "optimistic" score.
- **Mitigation (do this NOW, before any final run)**:
  1. `git mv README.md README_v1.md && git mv README_v2.md README.md`. (Done in one minute.)
  2. Move `Docs/final_report_draft.md` and `Docs/final_report.pdf` to `Docs/_legacy/`. If they aren't in the submission zip, they can't be inspected.
  3. Add a fatal preflight check in notebook 22 that greps every `.md` in `Docs/` and `Reports/` for the v1 marker strings and refuses to write the CSV if any are found.

### B. SFA convergence failure cascades into a silent overclaim

- **What happens**: cell 11 raises (most likely `scipy.optimize.minimize` returns `success=False` and `_extract_params` raises, OR `log(0)` from an outlet with `observed_max == 0`). Cell 13 prints _"SFA fit failed → using pure XGBoost q90 frontier"_ and continues. `predictions_v2.parquet` is written; downstream cells (CQR, Manski, validation) all run on pure-q90. Notebook 22 has no idea SFA failed. Portal validation passes. Team uploads.
- **What the team says to the judges later** (because they didn't read the printed output carefully): "we used a 60/40 XGBoost + SFA ensemble." Judge: "show me σ_u, σ_v, λ." Team can't produce them.
- **Severity**: **HIGH on the methodology rubric** (claim ≠ reality). **LOW on prediction quality** (XGBoost q90 alone is competitive). Net hit: **-5 to -10** because credibility-by-overclaim is worse than honesty-with-fewer-methods.
- **Mitigation** (do at least one of these):
  1. Promote the failure: change cell 13's failure print to `raise RuntimeError("SFA failed; rerun with leaner features OR drop SFA from PDF claims")`. Loud, not quiet.
  2. **OR** add `Results/run_manifest.json` with `sfa_converged: false` and have the report template branch on it.
  3. **OR (lowest effort, highest credibility)**: drop SFA from the headline methodology in the PDF. Keep it in an appendix as "robustness check." The architect's R3 recommendation is exactly this.

### C. Team uploads v1 by muscle memory

- **What happens**: it's hour 33 of 36. Someone clicks into `Results/`, sees `smile_labs_predictions.csv` (the file the PDF and the README both name as the platform file), drags it to the portal. The portal either auto-rejects on schema ("expected `Outlet_ID`, got `row_id`") OR accepts-but-scores-on-914-outlets (worst case: silently scored as if the team missed 19,086 predictions). Or — worse — a panicked teammate sees `smile_labs_predictions_full_20000.csv` (20k rows!), thinks "this looks right", uploads it. Schema is still `row_id`. Same disqualifier outcome.
- **Severity**: **DISQUALIFIER.** Single highest realised cost of any failure mode in the entire 36 hours.
- **Mitigation** (in priority order, do all three):
  1. **NOW, before any final run**:
     ```powershell
     New-Item -ItemType Directory -Force Results\_legacy_do_not_submit
     Move-Item Results\smile_labs_predictions.csv Results\_legacy_do_not_submit\smile_labs_predictions_v1_914row.csv
     Move-Item Results\smile_labs_predictions_full_20000.csv Results\_legacy_do_not_submit\smile_labs_predictions_full_20000_v1_wrongschema.csv
     ```
  2. Add a fatal preflight assertion in notebook 22 cell 3:
     ```python
     legacy = RESULTS_DIR / "smile_labs_predictions.csv"
     if legacy.exists():
         hdr = pd.read_csv(legacy, nrows=0).columns.tolist()
         n_rows = sum(1 for _ in open(legacy)) - 1
         if "row_id" in hdr or n_rows == 914:
             raise RuntimeError(f"Legacy v1 file still in Results/ (cols={hdr}, rows={n_rows}). Move it before continuing.")
     ```
  3. Create `Results/FINAL_UPLOAD/smile_labs_predictions.csv` (the only file in that folder) plus a `Results/FINAL_UPLOAD/README_UPLOAD_THIS_FILE.txt` that reads exactly: _"Upload this file. 20,000 rows. Columns: Outlet_ID, Maximum_Monthly_Liters."_ Friction-free for the panicked operator.

---

# Honest Strengths

1. **Notebook 21's cell flow is finally sequential and auditable**: lower bound → CH proxy → CH correction → multi-quantile → SFA → ensemble → constraint score → caps → final potential → CQR → Manski → save. No backtracking, no notebook-state surprises if a teammate runs cells top-to-bottom. R1 was a 1500-line monolith; v2 reads like a paper appendix.
2. **CH-3 censoring correction is genuinely preprocessing, not theatre.** `chernozhukov_hong_correction` returns `(X_uncensored, y_uncensored, summary)`; cell 7 prints `corr.n_uncensored_kept / corr.n_total` and `corr.propensity_summary` so a judge can audit the filter step. The threshold (0.10) is conservative.
3. **SFA target leakage is genuinely fixed.** Cell 11 explicitly drops `{observed_mean, observed_median, observed_p90, observed_p95}` from `sfa_X`. The R2 N3 blocker I personally raised in round 2 is gone in code.
4. **The cap table is empirical, not vibes-coded.** `cap_table_v2.csv` from `bootstrap_size_type_caps(gold)` (cell 17) replaces the v1 `{Small:3.0, Medium:3.5, Large:4.0, XL:4.5}` ladder. A judge asking _"where did the cap come from?"_ can be answered with a CSV — _if_ the team avoids the manski.py merge bug above for the Manski path.
5. **The 6-item validation suite is enforced.** Notebook 22 cell 5 runs `run_validation_suite` over the submission. V1 schema, V2 non-negativity/uniqueness, V3a referential integrity, V3b historical-max floor (now genuinely floored at `observed_max` in `predict.py:59-64`), V4 uplift range, V5 cap-binding using bucket-specific cap (R2 V5 hardcoded `5.9×` is fixed).
6. **Top-100-by-uplift anti-overfit check is in notebook 22 cell 13.** The comparison `top100_uplift mean constraint_score >> population mean constraint_score` is exactly the right anti-overfit guard for the rebuilt score. R1 had no equivalent.
7. **Bronze → Silver → Gold split with reusable DQ checks is real code, not narrative.** `src/quality/checks.py` is parameterised; notebook 20 wires it across the five raw datasets and persists rejected records to `data/silver_rejected/` — _if_ the notebook actually runs (which currently it hasn't on this machine; B3 risk).

---

# Final Grade

| Scenario                                                                                     | P (my estimate) | Grade       | Reasoning                                                                                                                                                                                                                                                                                     |
| -------------------------------------------------------------------------------------------- | --------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Team ships v2 cleanly across all 6 gates + PDF rewrite + README swap + v1 files archived** | ~30%            | **B+ / A-** | The Architect's "A- after packaging fix" verdict is right _if_ the team executes the packaging fix. Methodology is defensible, validation passes, top-100 audit is in. The q50/q75/q95-on-wrong-subset and manski-clip bugs each cost ~2 points but are invisible to non-statistician judges. |
| **Team ships v2 but forgets PDF + README cutover**                                           | ~25%            | **B- / C+** | Strong code + contradicting PDF + contradicting README = judges discount methodology because they no longer trust the report. The 30% report rubric is the chokepoint.                                                                                                                        |
| **Team ships v2 but POI is partial (2 of 9 categories)**                                     | ~15%            | **B / B-**  | The headline external-data deliverable is partial; constraint score loses inputs; report can honestly disclose (B-) or quietly claim "9 POI categories" while shipping 2 (B-, with reputational risk if a judge greps the gold parquet for `*_decay_score` columns).                          |
| **Team ships v1 by muscle memory (wrong CSV)**                                               | ~20%            | **D / F**   | Disqualifier or near-disqualifier. The single failure mode the team must engineer out _today_.                                                                                                                                                                                                |
| **Pipeline fails mid-run (G2 deps or G4 cell error), team reverts to v1**                    | ~10%            | **C-**      | Back to the R1 grade. Where the team was 60 hours ago.                                                                                                                                                                                                                                        |

**Expected-value grade**: between **B- and B**, weighted by the above. The architecture supports A-; the packaging risk drags the expectation down ~one full letter.

**The single most valuable next action** (~45 minutes total, no model changes):

1. Move `Results/smile_labs_predictions.csv` and `Results/smile_labs_predictions_full_20000.csv` to `Results/_legacy_do_not_submit/`. (2 minutes.)
2. Rename `README.md` → `README_v1.md`, rename `README_v2.md` → `README.md`. (1 minute.)
3. Move `Docs/final_report_draft.md` and `Docs/final_report.pdf` to `Docs/_legacy/`. (1 minute.)
4. Make notebook 22 cell 16 destructive by default (5-line shutil block above). (10 minutes.)
5. Fix the two `manski.py` bugs (merge suffixes collision + point clip). (5 minutes.)
6. Move notebook 22 cell 3's asserts to **after** the reindex and add `assert len(sub) == 20_000`. (2 minutes.)
7. Split notebook 21 cell 9 into two fits (`q05/q50/q75/q95` on full sample, `q90` on CH-filtered). (15 minutes.)
8. Run all three notebooks end-to-end at least once, confirm `data/{silver_rejected,gold}/` populate, confirm `Results/smile_labs_predictions.csv` matches v2. (10 minutes.)

Doing those eight things moves the expected grade from **B-** to **B+** because steps 1-3 kill Scenario C (20% disqualifier weight) and steps 4-5 kill the cap-merge + point-clip bugs that the methodology audit would catch.

---

# 7-Line Summary

1. **q90 IS correctly fit on uncensored only** (R2 M4 fix lands), but `q50/q75/q95` are also fit on the uncensored subset → wrong subset for the conditional median → notebook 21 cell 21 then uses `q50` as the "conservative lower edge" while the cell-25 summary calls the interval `[q05, q95]` (three errors in one CQR step, 15-minute fix).
2. **Notebook 22 is non-destructive by design** — cell 0 explicitly says it does _not_ overwrite `smile_labs_predictions.csv`; cell 16 hands the team a manual `copy` command plus a confusing "verify the 914-row constraint" warning; meanwhile `Results/smile_labs_predictions.csv` (914 rows, `row_id`) and `Results/smile_labs_predictions_full_20000.csv` (20k rows but **still wrong schema**) sit in `Results/` waiting to be misuploaded.
3. **Three previously-unflagged code bugs in v2**: (a) `manski.py:54-61` merge silently drops the `cap_table` parameter because of a `suffixes` collision with `predict.py`'s already-existing `cap_uplift` column; (b) `manski.py:70` clips the point estimate inside the Manski interval, so `manski_bands_v2.csv` "point" disagrees with the submission CSV for any outlet where the v2 point exceeds the empirical upper; (c) notebook 22 cell 3's `isna().any()` assert runs **before** the reindex against `outlet_master`, so a left-merge can introduce NaN rows that bypass all four asserts.
4. **SFA will probably converge** after the R2 N3 fix (correctly applied in cell 11), but the 60/40 ensemble is largely cosmetic; the silent `try/except` cushion + no run-manifest means a judge cannot verify that what the README claims is what the uploaded CSV reflects.
5. **The repo's front door still says v1**: `README.md:9-11` lists Notebook 01/03/04 as "Key files", `README.md:39` says `pip install -r requirements.txt` (the 6-package broken list, not `requirements_v2.txt`), `README.md:86-89` documents `row_id` schema and the 914-row fallback. `Docs/final_report_draft.md` matches the README — 914 rows, `row_id`, median uplift 1.18x, `max(historical_max, january_max, recent_3_month_max)` lower bound, `coordinate availability` in the constraint score. A judge spots the contradiction in 30 seconds.
6. **`data/{bronze,silver,silver_rejected,gold}/` are all empty except `.gitkeep`** and `poi_pipeline/data/pois/` has only 2 of 9 promised categories. The v2 stack has never been run end-to-end on disk — not by reviewers, not by the team that wrote it. All runtime risk is therefore unobserved.
7. **Clean-ship probability ~30%**, expected-value grade **B-/B**. The 45-minute packaging fix (8 steps above; no model changes) moves the expectation to **B+** by killing Scenario C (20% disqualifier weight) and the two manski.py bugs. The Architect's "B+ now, A- after packaging fix" is right _only if_ that packaging fix is engineered into the repo today, not left as a manual instruction in a markdown cell.
