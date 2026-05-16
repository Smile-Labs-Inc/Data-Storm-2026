# Submission Pre-flight Validation
| # | Check | Pass? | Detail |
| ---: | --- | :---: | --- |
| 1 | V1: schema + row count | **OK** | cols=['Maximum_Monthly_Liters', 'Outlet_ID'], rows=20000 (expected 20000) |
| 2 | V2: no NaN, no negatives, unique IDs | **OK** | NaN=0, neg=0, unique=True |
| 3 | V3a: every Outlet_ID exists in outlet_master | **OK** | missing=0 |
| 4 | V3b: predicted >= historical max for >= 99% of outlets | **OK** | 0.00% below historical max |
| 5 | V4: median uplift in [1.25, 2.2] | **OK** | median_uplift=1.250 |
| 6 | V5: cap-binding rate < 25.0% (bucket-specific cap) | **OK** | 0.00% appear at the cap |
