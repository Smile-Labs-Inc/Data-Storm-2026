# Legacy submission files — DO NOT UPLOAD

Audit / diff only. The **canonical submission** is `Results/smile_labs_predictions.csv` (one file, 20,000 rows, columns `[Outlet_ID, Maximum_Monthly_Liters]`, validation 6/6 PASS).

| File                                             | Why kept                                                                     | Why NOT to upload                                                        |
| ------------------------------------------------ | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `smile_labs_predictions_v1.csv`                  | original 914-row v1 platform file                                            | column is `row_id` (PDF says `Outlet_ID`); 914-row constraint unverified |
| `smile_labs_predictions_full_20000_v1.csv`       | original 20k v1 business output                                              | column is `row_id`; uses v1 broken methodology                           |
| `smile_labs_predictions_pre_v2_*.csv`            | pre-v2 snapshot of canonical file (auto-moved by notebook 22's release gate) | superseded by current v2 output                                          |
| `smile_labs_predictions_full_20000_pre_v2_*.csv` | pre-v2 business output snapshot                                              | same as above                                                            |
| `smile_labs_predictions_full_20000.csv`          | duplicate v2 business output written by `run_pipeline.py`                    | duplicate of canonical; moved in R7 cleanup per council R6 N6.3          |
| `smile_labs_predictions_full_20000_v2.csv`       | duplicate v2 business output from notebook 22                                | duplicate of canonical; moved in R7 cleanup                              |
| `smile_labs_predictions_v2.csv`                  | duplicate v2 platform output from notebook 22                                | duplicate of canonical; moved in R7 cleanup                              |

The current submission is produced by running either:

```
python run_pipeline.py                          # one-shot CLI
```

or:

```
Notebooks/20_v2_data_pipeline.ipynb
Notebooks/21_v2_modeling.ipynb
Notebooks/22_v2_validation_and_submission.ipynb
```

Both write `Results/smile_labs_predictions.csv` as the canonical file.
