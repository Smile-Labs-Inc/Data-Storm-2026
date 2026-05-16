# Model Validation Summary

This validation summary was generated from `Notebooks/04_model_validation.ipynb`.

## Schema Checks

| check | value | expected | passed |
| --- | --- | --- | --- |
| platform_rows | 914 | 914 | True |
| platform_columns | row_id, Maximum_Monthly_Liters | row_id, Maximum_Monthly_Liters | True |
| platform_missing_values | 0 | 0 | True |
| platform_unique_row_id | 914 | 914 | True |
| full_rows | 20000 | 20000 | True |
| full_missing_values | 0 | 0 | True |

## Key Distribution Metrics

| index | observed_max_monthly_liters | Maximum_Monthly_Liters | uplift_ratio_vs_max | constraint_score | catchment_density_score | poi_demand_score |
| --- | --- | --- | --- | --- | --- | --- |
| mean | 396.059 | 445.025 | 1.357 | 0.166 | 0.5 | 0.0 |
| 50% | 164.047 | 258.498 | 1.181 | 0.17 | 0.463 | 0.0 |
| 90% | 973.439 | 980.42 | 2.008 | 0.245 | 0.843 | 0.0 |
| 95% | 1307.899 | 1307.899 | 2.433 | 0.28 | 0.884 | 0.0 |
| 99% | 2096.503 | 2105.366 | 2.961 | 0.368 | 0.935 | 0.0 |
| max | 10457.941 | 10457.941 | 2.971 | 0.556 | 0.995 | 0.0 |

## Outlet Size Summary

| Outlet_Size | outlets | avg_potential | median_potential | avg_uplift | avg_constraint | avg_poi_score |
| --- | --- | --- | --- | --- | --- | --- |
| Extra Large | 943 | 2064.067 | 2050.767 | 1.014 | 0.242 | 0.0 |
| Large | 2887 | 968.583 | 961.164 | 1.011 | 0.219 | 0.0 |
| Medium | 5702 | 369.455 | 357.245 | 1.163 | 0.161 | 0.0 |
| Small | 10272 | 195.971 | 173.734 | 1.59 | 0.148 | 0.0 |
| Unknown | 196 | 194.624 | 168.896 | 1.515 | 0.16 | 0.0 |

## Outlet Type Summary

| Outlet_Type | outlets | avg_potential | median_potential | avg_uplift | avg_constraint | avg_poi_score |
| --- | --- | --- | --- | --- | --- | --- |
| Hotel | 2797 | 455.073 | 251.758 | 1.411 | 0.18 | 0.0 |
| Grocery | 3158 | 450.6 | 262.318 | 1.367 | 0.167 | 0.0 |
| Pharmacy | 2691 | 448.625 | 230.078 | 1.287 | 0.151 | 0.0 |
| Eatery | 2867 | 447.098 | 272.531 | 1.388 | 0.173 | 0.0 |
| Kiosk | 2691 | 442.006 | 238.405 | 1.274 | 0.148 | 0.0 |
| SMMT | 2723 | 437.253 | 262.409 | 1.445 | 0.187 | 0.0 |
| Bakery | 3073 | 434.596 | 237.948 | 1.325 | 0.157 | 0.0 |

## Signal Correlation

| index | poi_demand_score | catchment_density_score | constraint_score | Maximum_Monthly_Liters | uplift_ratio_vs_max |
| --- | --- | --- | --- | --- | --- |
| poi_demand_score |  |  |  |  |  |
| catchment_density_score |  | 1.0 | 0.248 | 0.03 | 0.182 |
| constraint_score |  | 0.248 | 1.0 | 0.408 | 0.521 |
| Maximum_Monthly_Liters |  | 0.03 | 0.408 | 1.0 | -0.37 |
| uplift_ratio_vs_max |  | 0.182 | 0.521 | -0.37 | 1.0 |

## Review Artifacts

- `data/gold/validation_top_100_potential.csv`
- `data/gold/validation_top_100_uplift.csv`