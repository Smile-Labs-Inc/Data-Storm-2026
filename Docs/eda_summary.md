# Full Dataset EDA Summary

This EDA uses the full local raw datasets in `Datasets/`, including the complete transaction history. It is separate from the 914-row platform submission file.

## Key Findings

- The raw data contains 20,000 outlet master records and 2,376,389 transaction rows across 2023-2025.
- All 20,000 outlets appear in the transaction history after profiling, which means the modeling table can cover the full outlet universe.
- Outlet master has 196 missing outlet-size values, 600 lowercase `small` values, 390 `Grocry` values, and 395 `Bakry` values.
- Coordinate validation flags 240 outlet coordinate rows outside plausible Sri Lankan bounds.
- Transaction quality checks flag 4,853 rows with non-positive volume or bill value; these are treated as rejected records before feature engineering.
- Valid transaction history covers 10 distributors, 10 SKUs, and 36 distinct months.
- The median outlet max observed monthly volume is 164.0 liters, while the 95th percentile is 1,307.9 liters. This gap supports a peer-frontier approach for latent potential.
- Holiday data has 93 duplicate date-name-type rows, so holiday features should be aggregated carefully rather than treated as unique event records.

## Dataset Overview

| dataset | rows | columns | duplicate_rows | memory_mb |
| --- | --- | --- | --- | --- |
| outlet_master.csv | 20000 | 4 | 0 | 3.8 |
| outlet_coordinates.csv | 20000 | 3 | 0 | 1.56 |
| transactions_history_final.csv | 2376389 | 7 | 0 | 514.9 |
| distributor_seasonality_details.csv | 360 | 4 | 0 | 0.05 |
| holiday_list.csv | 349 | 3 | 93 | 0.07 |

## Missing Values

| dataset | column | missing_rows | missing_pct |
| --- | --- | --- | --- |
| outlet_master.csv | Outlet_Size | 196 | 0.98 |

## Raw Outlet Size Counts

| Outlet_Size_raw | rows |
| --- | --- |
| Small | 9672 |
| Medium | 5702 |
| Large | 2887 |
| Extra Large | 943 |
| small | 600 |
| <missing> | 196 |

## Raw Outlet Type Counts

| Outlet_Type_raw | rows |
| --- | --- |
| Eatery | 2867 |
| Hotel | 2797 |
| Grocery | 2768 |
| SMMT | 2723 |
| Kiosk | 2691 |
| Pharmacy | 2691 |
| Bakery | 2678 |
| Bakry | 395 |
| Grocry | 390 |

## Cooler and Sales by Outlet Size

| Outlet_Size_Normalized | outlets | avg_coolers | zero_cooler_pct | avg_max_monthly_liters | median_max_monthly_liters |
| --- | --- | --- | --- | --- | --- |
| Extra Large | 943 | 3.494 | 0 | 2039.854 | 2029.965 |
| Large | 2887 | 3.464 | 0 | 957.25 | 950.619 |
| Medium | 5702 | 1.496 | 0 | 320.774 | 308.365 |
| Small | 10272 | 0.363 | 67.88 | 134.112 | 115.073 |
| Unknown | 196 | 1.347 | 34.18 | 139.667 | 115.198 |

## Sales by Outlet Type

| Outlet_Type_Normalized | outlets | avg_coolers | avg_max_monthly_liters | median_max_monthly_liters | avg_mean_monthly_liters |
| --- | --- | --- | --- | --- | --- |
| Pharmacy | 2691 | 1.288 | 407.609 | 161.88 | 221.799 |
| Kiosk | 2691 | 1.289 | 401.94 | 170.057 | 218.176 |
| Grocery | 3158 | 1.274 | 400.875 | 164.878 | 214.503 |
| Hotel | 2797 | 1.307 | 399.928 | 163.619 | 217.218 |
| Eatery | 2867 | 1.297 | 394.81 | 166.817 | 212.061 |
| Bakery | 3073 | 1.295 | 389.474 | 160.714 | 210.422 |
| SMMT | 2723 | 1.288 | 378.022 | 161.878 | 202.394 |

## Coordinate Quality

| metric | value |
| --- | --- |
| coordinate_rows | 20000 |
| unique_outlets_with_coordinates | 20000 |
| duplicate_coordinate_outlet_ids | 0 |
| invalid_coordinate_rows | 240 |
| valid_coordinate_rows | 19760 |
| min_latitude | 0 |
| max_latitude | 80.792 |
| min_longitude | 0 |
| max_longitude | 80.8 |

## Transaction Quality

| metric | value |
| --- | --- |
| transaction_rows | 2376389 |
| unique_outlets_in_transactions | 20000 |
| unique_distributors | 10 |
| unique_skus | 10 |
| negative_or_zero_volume_rows | 4853 |
| negative_or_zero_bill_rows | 4753 |
| rows_failing_volume_or_bill_positive_check | 4853 |
| valid_positive_transaction_rows | 2371536 |

## Transaction Volume Distribution

| metric | value |
| --- | --- |
| count | 2371536 |
| mean | 52.836 |
| std | 95.378 |
| min | 1.237 |
| 1% | 2.832 |
| 5% | 4.217 |
| 10% | 5.497 |
| 25% | 10.241 |
| 50% | 23.218 |
| 75% | 54.532 |
| 90% | 117.096 |
| 95% | 197.411 |
| 99% | 554.361 |
| max | 9438.578 |

## Outlet Monthly Volume Distribution

| metric | value |
| --- | --- |
| count | 450588 |
| mean | 278.085 |
| std | 384.252 |
| min | 1.264 |
| 1% | 4.223 |
| 5% | 9.955 |
| 10% | 16.205 |
| 25% | 36.978 |
| 50% | 102.217 |
| 75% | 354.492 |
| 90% | 750.503 |
| 95% | 1265.456 |
| 99% | 1846.729 |
| max | 10457.941 |

## Monthly Time Series

| Year | Month | transaction_rows | active_outlets | total_liters | total_bill_value | avg_liters_per_active_outlet |
| --- | --- | --- | --- | --- | --- | --- |
| 2023 | 1 | 65374 | 12498 | 3445811.058 | 904346265.141 | 275.709 |
| 2023 | 2 | 65530 | 12491 | 3469527.246 | 907976980.399 | 277.762 |
| 2023 | 3 | 66708 | 12492 | 3337347.615 | 876306270.184 | 267.159 |
| 2023 | 4 | 65825 | 12536 | 4763914.031 | 1249379239.979 | 380.019 |
| 2023 | 5 | 65859 | 12483 | 2594021.444 | 681416088.866 | 207.804 |
| 2023 | 6 | 66036 | 12477 | 2623146.15 | 685426691.389 | 210.239 |
| 2023 | 7 | 65779 | 12508 | 3275888.205 | 860936598.574 | 261.903 |
| 2023 | 8 | 65872 | 12561 | 3601155.881 | 939903943.81 | 286.693 |
| 2023 | 9 | 66183 | 12638 | 3286698.142 | 865346730.493 | 260.065 |
| 2023 | 10 | 66172 | 12575 | 3305286.18 | 865080829.107 | 262.846 |
| 2023 | 11 | 65282 | 12419 | 3252717.626 | 855918867.465 | 261.915 |
| 2023 | 12 | 65461 | 12473 | 4782096.671 | 1247115631.328 | 383.396 |
| 2024 | 1 | 65709 | 12537 | 3457312.824 | 909897566.758 | 275.769 |
| 2024 | 2 | 65698 | 12465 | 3469826.306 | 909143878.117 | 278.366 |
| 2024 | 3 | 66937 | 12587 | 3351304.713 | 877939791.991 | 266.251 |
| 2024 | 4 | 65451 | 12505 | 4762022.959 | 1247526943.805 | 380.81 |
| 2024 | 5 | 65795 | 12513 | 2597683.29 | 681064208.34 | 207.599 |
| 2024 | 6 | 65779 | 12513 | 2607417.788 | 682198504.917 | 208.377 |
| 2024 | 7 | 65800 | 12472 | 3282709.943 | 863163491.028 | 263.206 |
| 2024 | 8 | 65947 | 12533 | 3591780.918 | 938529602.069 | 286.586 |
| 2024 | 9 | 65681 | 12543 | 3282066.743 | 858679296.326 | 261.665 |
| 2024 | 10 | 65997 | 12459 | 3317090.217 | 868024936.007 | 266.24 |
| 2024 | 11 | 65835 | 12584 | 3275753.303 | 857619329.894 | 260.311 |
| 2024 | 12 | 65722 | 12493 | 4772147.037 | 1247905589.506 | 381.986 |
| 2025 | 1 | 65821 | 12501 | 3477398.297 | 912564169.834 | 278.17 |
| 2025 | 2 | 65352 | 12380 | 3488471.704 | 911752468.414 | 281.783 |
| 2025 | 3 | 66592 | 12526 | 3344323.955 | 872528191.466 | 266.991 |
| 2025 | 4 | 65898 | 12560 | 4753633.864 | 1249247085.14 | 378.474 |
| 2025 | 5 | 65798 | 12501 | 2598064.104 | 680263597.652 | 207.829 |
| 2025 | 6 | 65632 | 12487 | 2604771.046 | 682137864.852 | 208.599 |
| 2025 | 7 | 66319 | 12620 | 3294366.121 | 863918043.173 | 261.043 |
| 2025 | 8 | 66000 | 12505 | 3592918.67 | 943547365.869 | 287.319 |
| 2025 | 9 | 66041 | 12537 | 3286847.102 | 862141421.875 | 262.172 |
| 2025 | 10 | 65865 | 12537 | 3297531.597 | 866058533.838 | 263.024 |
| 2025 | 11 | 65781 | 12496 | 3279458.908 | 860241921.341 | 262.441 |
| 2025 | 12 | 66005 | 12583 | 4779443.345 | 1252118631.231 | 379.833 |

## Distributor Performance

| Distributor_ID | transaction_rows | active_outlets | total_liters | total_bill_value | avg_transaction_liters |
| --- | --- | --- | --- | --- | --- |
| DIST_W_01 | 365580 | 3020 | 18918040.683 | 4959040214.204 | 51.748 |
| DIST_W_03 | 362269 | 2991 | 18793478.022 | 4915796046.559 | 51.877 |
| DIST_W_02 | 364466 | 2989 | 18351445.816 | 4810784398.482 | 50.352 |
| DIST_NW_01 | 239332 | 2015 | 13190300.914 | 3461830444.847 | 55.113 |
| DIST_NW_02 | 235607 | 1985 | 12662426.587 | 3321245789.391 | 53.744 |
| DIST_C_01 | 163954 | 1385 | 9118309.984 | 2388150277.676 | 55.615 |
| DIST_C_03 | 152832 | 1296 | 8909557.768 | 2335380268.251 | 58.296 |
| DIST_S_02 | 168457 | 1495 | 8758725.602 | 2295683085.287 | 51.994 |
| DIST_S_01 | 167007 | 1505 | 8367820.199 | 2191781539.666 | 50.105 |
| DIST_C_02 | 152032 | 1319 | 8231849.426 | 2157674505.816 | 54.146 |

## SKU Performance

| SKU_ID | transaction_rows | active_outlets | total_liters | avg_transaction_liters | avg_value_per_liter |
| --- | --- | --- | --- | --- | --- |
| SKU_06 | 231577 | 19963 | 57258177.881 | 247.253 | 84 |
| SKU_02 | 231507 | 19953 | 17161300.999 | 74.129 | 253.329 |
| SKU_07 | 232157 | 19927 | 11463285.359 | 49.377 | 649.997 |
| SKU_05 | 231402 | 19950 | 11447567.102 | 49.47 | 89.999 |
| SKU_01 | 287097 | 20000 | 6498560.702 | 22.635 | 339.48 |
| SKU_08 | 231310 | 19931 | 5723717.897 | 24.745 | 439.997 |
| SKU_04 | 231781 | 19949 | 4585054.079 | 19.782 | 325 |
| SKU_03 | 231552 | 19947 | 4580335.102 | 19.781 | 349.996 |
| SKU_10 | 231849 | 19949 | 3722443.169 | 16.055 | 369.226 |
| SKU_09 | 231304 | 19945 | 2861512.713 | 12.371 | 2199.983 |

## Seasonality Index Counts

| Seasonality_Index | rows |
| --- | --- |
| Moderate | 249 |
| Favorable | 81 |
| Un-Favorable | 30 |

## Holiday Duplicate Summary

| metric | value |
| --- | --- |
| holiday_rows | 349 |
| exact_duplicate_rows | 93 |
| duplicate_date_name_type_rows | 93 |
| unique_dates | 76 |

## Holiday Type Counts

| Holiday_Type | rows |
| --- | --- |
| Bank | 99 |
| Public | 98 |
| Mercantile | 93 |
| Poya Day | 59 |

## Modeling Implications

- Use historical maximum monthly volume as a conservative lower bound, not as the final potential estimate.
- Use outlet size, type, cooler count, distributor behavior, SKU breadth, and peer frontiers to estimate uncapped potential.
- Quarantine invalid coordinates and non-positive transaction values before feature engineering.
- Treat duplicated holiday rows carefully when creating calendar features.
- Add external POI density and nearest-distance features next, because internal data alone cannot fully explain latent catchment demand.
