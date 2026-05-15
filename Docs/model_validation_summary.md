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
| mean | 396.059 | 445.339 | 1.359 | 0.167 | 0.5 | 0.023 |
| 50% | 164.047 | 259.767 | 1.182 | 0.171 | 0.463 | 0.0 |
| 90% | 973.439 | 980.42 | 2.019 | 0.246 | 0.843 | 0.0 |
| 95% | 1307.899 | 1307.899 | 2.443 | 0.282 | 0.884 | 0.0 |
| 99% | 2096.503 | 2105.366 | 2.961 | 0.374 | 0.935 | 0.759 |
| max | 10457.941 | 10457.941 | 2.971 | 0.597 | 0.995 | 0.996 |

## Outlet Size Summary

| Outlet_Size | outlets | avg_potential | median_potential | avg_uplift | avg_constraint | avg_poi_score |
| --- | --- | --- | --- | --- | --- | --- |
| Extra Large | 943 | 2064.117 | 2050.767 | 1.014 | 0.242 | 0.025 |
| Large | 2887 | 968.592 | 961.24 | 1.011 | 0.219 | 0.022 |
| Medium | 5702 | 369.7 | 357.64 | 1.164 | 0.161 | 0.025 |
| Small | 10272 | 196.438 | 173.979 | 1.595 | 0.149 | 0.021 |
| Unknown | 196 | 194.624 | 168.896 | 1.515 | 0.161 | 0.019 |

## Outlet Type Summary

| Outlet_Type | outlets | avg_potential | median_potential | avg_uplift | avg_constraint | avg_poi_score |
| --- | --- | --- | --- | --- | --- | --- |
| Hotel | 2797 | 455.236 | 251.758 | 1.412 | 0.181 | 0.017 |
| Grocery | 3158 | 451.138 | 266.545 | 1.371 | 0.168 | 0.028 |
| Pharmacy | 2691 | 448.841 | 231.714 | 1.288 | 0.151 | 0.022 |
| Eatery | 2867 | 447.434 | 274.173 | 1.39 | 0.174 | 0.021 |
| Kiosk | 2691 | 442.242 | 240.343 | 1.276 | 0.148 | 0.022 |
| SMMT | 2723 | 437.508 | 262.409 | 1.447 | 0.188 | 0.021 |
| Bakery | 3073 | 435.001 | 241.409 | 1.329 | 0.158 | 0.026 |

## Signal Correlation

| index | poi_demand_score | catchment_density_score | constraint_score | Maximum_Monthly_Liters | uplift_ratio_vs_max |
| --- | --- | --- | --- | --- | --- |
| poi_demand_score | 1.0 | 0.199 | 0.136 | 0.107 | -0.014 |
| catchment_density_score | 0.199 | 1.0 | 0.257 | 0.031 | 0.186 |
| constraint_score | 0.136 | 0.257 | 1.0 | 0.4 | 0.526 |
| Maximum_Monthly_Liters | 0.107 | 0.031 | 0.4 | 1.0 | -0.369 |
| uplift_ratio_vs_max | -0.014 | 0.186 | 0.526 | -0.369 | 1.0 |

## Review Artifacts

- `data/gold/validation_top_100_potential.csv`
- `data/gold/validation_top_100_uplift.csv`