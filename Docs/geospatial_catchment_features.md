# Geospatial Catchment Features

This document describes the implemented catchment feature layer in `Notebooks/01_latent_potential_pipeline.ipynb`.

## Why This Was Added

The full EDA showed a wide gap between typical outlets and high-performing outlets. Internal sales history alone does not explain whether an outlet is constrained or located in a naturally stronger catchment.

Until external POI data is added, outlet coordinates can still provide useful local market-intensity signals.

## Implemented Features

The pipeline now uses valid outlet coordinates to create local catchment features with a haversine `BallTree`.

| Feature | Meaning |
| --- | --- |
| `outlet_count_1km` | Number of nearby outlets within 1 km. |
| `outlet_count_2km` | Number of nearby outlets within 2 km. |
| `outlet_count_5km` | Number of nearby outlets within 5 km. |
| `same_type_outlet_count_2km` | Number of nearby outlets of the same outlet type within 2 km. |
| `same_distributor_outlet_count_5km` | Number of nearby outlets served by the same dominant distributor within 5 km. |
| `nearest_outlet_distance_km` | Distance to the nearest other valid outlet. |
| `catchment_density_score` | Weighted local market-density proxy from the features above. |

## Modeling Usage

These features are now included in the model feature set.

The `catchment_density_score` also contributes to the constraint score:

```text
demand_proxy =
  structural capacity rank
  + cooler count rank
  + SKU breadth rank
  + catchment density rank
  + valid coordinate rank
```

This means a low-selling outlet in a dense outlet catchment is more likely to be treated as constrained than a similarly low-selling outlet in a sparse catchment.

## Latest Diagnostics

After adding catchment features:

- full prediction output remains 20,000 rows.
- platform submission output remains 914 rows.
- median uplift versus historical maximum is about 1.21x.
- mean uplift versus historical maximum is about 1.42x.
- maximum uplift remains below 3.0x.

The catchment score is intentionally used as a supporting signal, not as a standalone demand estimate.

## Remaining Improvement

This is still an internal geospatial proxy. The next stronger version should add external POI data, such as:

- schools.
- transport hubs.
- markets.
- hospitals.
- offices.
- eateries.
- supermarkets.
- religious places.
- hotels and tourist attractions.

Those POI features should be merged with the existing catchment features to improve the latent-demand framework.
