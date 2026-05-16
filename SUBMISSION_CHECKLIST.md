# Submission Pre-flight Checklist

Run through this top-to-bottom right before uploading. Every item must be PASS or you don't ship.

## 1. Code is runnable on a fresh venv

- [ ] `python -m venv .venv`
- [ ] `.\.venv\Scripts\Activate.ps1`
- [ ] `pip install -r requirements.txt` succeeds (no errors)
- [ ] `python -c "from src import quality, cleaning, features, modeling, reporting"` succeeds

## 2. POI pipeline ran (or honestly skipped)

- [ ] `cd poi_pipeline && python 01_download_pbf.py` -> `data/raw/sri-lanka-latest.osm.pbf` exists, > 100 MB
- [ ] `python 02_extract_pois.py` -> `data/pois/*.parquet` for all 9 categories
- [ ] `python 03_build_features.py` -> `output/poi_features.parquet` exists, ~20k rows, ~63 cols
- [ ] `python 04_quality_audit.py` -> `output/poi_coverage_report.md` exists
- [ ] OR (if POI skipped) the report explicitly states "POI features not used" and explains why

## 3. Main pipeline ran end-to-end

- [ ] `python run_pipeline.py` finishes without errors
- [ ] `data/bronze/` contains 5 raw CSVs + `_ingestion_audit.csv`
- [ ] `data/silver/` contains 5 parquet files
- [ ] `data/silver_rejected/` contains at least 2 CSVs (`outlet_coordinates_rejected.csv`, `transactions_history_rejected.csv`) -- NOT empty
- [ ] `data/gold/outlet_features.parquet` exists, 20k rows
- [ ] `data/gold/cap_table.csv` exists
- [ ] `data/gold/quantile_predictions.parquet` exists

## 4. Submission CSV is correct

- [ ] `Results/teamname_predictions.csv` exists
- [ ] Header is exactly `Outlet_ID,Maximum_Monthly_Liters` (case sensitive)
- [ ] 20,001 lines (1 header + 20,000 data rows)
- [ ] No `NaN`, no negative values, no duplicate `Outlet_ID`
- [ ] All `Outlet_ID` values exist in `outlet_master.csv`
- [ ] File size < 1 MB
- [ ] UTF-8 encoded, no BOM, no leading/trailing whitespace in headers

## 5. 6-item auto-validation passes

- [ ] `Results/validation_report.md` shows all V1, V2, V3a, V3b, V4, V5 = PASS
- [ ] If any FAIL, fix or explain in the PDF (do not silently ship)

## 6. PDF report

- [ ] `Reports/final_report.md` has `[Team Name]` and `[Submission Date]` filled in
- [ ] `cd Reports && python build_pdf.py` succeeds
- [ ] `Reports/final_report.pdf` is exactly 5 pages including cover
- [ ] DAG renders correctly (page 3 or wherever it lands)
- [ ] All 4 mandatory sections present: Forensics, POI, Causal Logic, GenAI Log

## 7. Repo packaging

- [ ] No accidental large files: `find . -size +50M` shows nothing inside the repo
- [ ] `data/bronze/` and `poi_pipeline/data/raw/` are excluded from the zip
- [ ] `.venv/`, `__pycache__/`, `.pytest_cache/` excluded
- [ ] `Results/_legacy/` either excluded OR clearly marked DO NOT SUBMIT
- [ ] `README.md` reads cleanly and matches the actual code
- [ ] `Docs/ai_transparency_log.md` is up to date

## 8. Manual sanity audit

- [ ] Open `Results/teamname_predictions.csv` in a viewer; head + tail + a few random rows look reasonable
- [ ] Compare top-100 highest predictions against `outlet_master.csv`: are they large outlets in dense urban zones?
- [ ] Compare bottom-100 lowest predictions: are they small rural outlets?
- [ ] If anything looks wrong, do NOT ship -- fix first

## 9. Final go / no-go

- [ ] Two team members independently signed off above
- [ ] Submission window is still open
- [ ] Backup of submission CSV stored separately (in case re-upload needed)

## On the Day at submission time

```powershell
cd autokaggle/competition

# fresh end-to-end
python run_pipeline.py

# rebuild PDF
cd Reports
python build_pdf.py
cd ..

# verify CSV one more time
python -c "import pandas as pd; df = pd.read_csv('Results/teamname_predictions.csv'); print(df.shape, df.columns.tolist(), df.head(3))"
```

If all 9 sections above are checked, you're cleared to submit.

---

## What gets uploaded to the Data Storm portal

1. **`Results/teamname_predictions.csv`** -- the prediction CSV.
2. **Zipped repo** (excluding `data/bronze/`, `data/silver/`, `poi_pipeline/data/raw/`, `.venv/`, `__pycache__/`, `Results/_legacy/`):
   ```powershell
   # PowerShell example (run from competition/ parent)
   Compress-Archive -Path competition\* `
     -DestinationPath teamname_codebase.zip `
     -Force
   # then manually delete heavy data folders from the zip if needed
   ```
3. **`Reports/final_report.pdf`** -- the 5-page PDF.

That's it. Three files.
