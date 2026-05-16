# Legacy submission files — DO NOT UPLOAD

These v1 files are kept here for audit/diff only. They have the **wrong column name** (`row_id` instead of `Outlet_ID` per the official Data Storm 7.0 PDF) and the v1 platform file has only 914 rows.

| File | Why kept | Why NOT to upload |
|---|---|---|
| `smil_labs_predictions_v1.csv` | original 914-row platform file | column is `row_id` (PDF says `Outlet_ID`); 914-row constraint unverified |
| `smil_labs_predictions_full_20000_v1.csv` | original 20k business output | column is `row_id` (PDF says `Outlet_ID`); uses v1 broken methodology |

The **current submission** is `Results/smil_labs_predictions_v2.csv` produced by running:

```
Notebooks/20_v2_data_pipeline.ipynb
Notebooks/21_v2_modeling.ipynb
Notebooks/22_v2_validation_and_submission.ipynb
```

If the team chooses to ship v1 (despite the council reviews), copy the file back:

```powershell
copy Results\_legacy\smil_labs_predictions_v1.csv Results\smil_labs_predictions.csv
```

But you should fix the `row_id` -> `Outlet_ID` column header first.
