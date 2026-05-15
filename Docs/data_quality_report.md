# Data Quality Report

This report is generated from `Notebooks/01_latent_potential_pipeline.ipynb`.

## Check Summary

| Dataset | Check | Failed Records | Failure Reason |
| --- | --- | ---: | --- |
| `outlet_master` | `duplicate_check` | 0 | Duplicate key on Outlet_ID |
| `outlet_master` | `null_check` | 0 | Null or empty mandatory field in Outlet_ID |
| `outlet_master` | `range_check` | 0 | Cooler_Count outside expected range |
| `outlet_master` | `domain_check` | 0 | Outlet_Size contains a value outside the allowed domain |
| `outlet_master` | `domain_check` | 0 | Outlet_Type contains a value outside the allowed domain |
| `outlet_coordinates` | `duplicate_check` | 0 | Duplicate key on Outlet_ID |
| `outlet_coordinates` | `null_check` | 0 | Null or empty mandatory field in Outlet_ID, Latitude, Longitude |
| `outlet_coordinates` | `referential_integrity_check` | 0 | Outlet_ID does not exist in reference dataset |
| `outlet_coordinates` | `range_check` | 240 | Latitude outside expected range |
| `outlet_coordinates` | `range_check` | 240 | Longitude outside expected range |
| `transactions_history` | `null_check` | 0 | Null or empty mandatory field in Outlet_ID, Year, Month, Distributor_ID, SKU_ID |
| `transactions_history` | `referential_integrity_check` | 0 | Outlet_ID does not exist in reference dataset |
| `transactions_history` | `domain_check` | 0 | Distributor_ID contains a value outside the allowed domain |
| `transactions_history` | `range_check` | 0 | Year outside expected range |
| `transactions_history` | `range_check` | 0 | Month outside expected range |
| `transactions_history` | `range_check` | 4853 | Volume_Liters outside expected range |
| `transactions_history` | `range_check` | 4753 | Total_Bill_Value outside expected range |
| `distributor_seasonality` | `duplicate_check` | 0 | Duplicate key on Distributor_ID, Year, Month |
| `distributor_seasonality` | `domain_check` | 0 | Distributor_ID contains a value outside the allowed domain |
| `distributor_seasonality` | `range_check` | 0 | Year outside expected range |
| `distributor_seasonality` | `range_check` | 0 | Month outside expected range |
| `distributor_seasonality` | `domain_check` | 0 | Seasonality_Index contains a value outside the allowed domain |
| `holiday_list` | `null_check` | 0 | Null or empty mandatory field in Date, Holiday_Name, Holiday_Type |
| `holiday_list` | `range_check` | 0 | Year outside expected range |
| `holiday_list` | `range_check` | 0 | Month outside expected range |

## Rejected Record Stores

| File | Rejected Rows |
| --- | ---: |
| `distributor_seasonality_rejected.csv` | 0 |
| `holiday_list_rejected.csv` | 0 |
| `outlet_coordinates_rejected.csv` | 480 |
| `outlet_master_rejected.csv` | 0 |
| `transactions_history_rejected.csv` | 9606 |