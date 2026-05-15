# TL;DR

- Keep the current `Small 3.0x / Medium 3.5x / Large 4.0x / Extra Large 4.5x` caps as an outer safety guardrail, but do not present them as the main evidence. The defensible method is to estimate a cap per outlet-size and outlet-type bucket from the dataset, then bound it by these maxima.
- Public FMCG evidence supports meaningful upside, but not unlimited upside. Cooler, display, assortment, and availability interventions often show `7%` to `114%` uplift, with selected case studies reaching about `2.0x`; anything above `3.0x` should need strong peer evidence.
- Current output is already conservative: the latest methodology notes median uplift around `1.20x`, average uplift around `1.37x`, and max uplift below `3.0x` versus historical max. That means `3x`, `4x`, and `5x` sensitivity runs should be almost identical unless the model is changed upstream.

# Industry Benchmarks

## 1. Cooler and chilled placement

Useful public numbers:

- A beverage display study on end-of-aisle placement found sales effects of `52%` to `114%` for non-alcoholic beverages and `23%` to `46%` for alcoholic beverages. This is roughly `1.23x` to `2.14x`, depending on category and display context. Source: Nakamura et al., *Social Science & Medicine*, "Sales impact of displaying alcoholic and non-alcoholic beverages in end-of-aisle locations" ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0277953614001361)).
- A commercial cooler case study reports that stores supplied with a cooler recorded more than `30%` growth in total store volume. The same case page reports `29%` volume uplift from cooler technology, `19%` and `38%` uplift in checkout-zone activations, `9%` uplift from evolutionary cooler planogram changes, and `27%` uplift from more aggressive planogram redesign. Source: Perfect Data Smart Shelf case studies ([Perfect Data](https://perfect-data.pl/case-study/)).
- A recent FMCG cooler-assignment paper frames commercial cooler allocation around growth thresholds of `10%`, `30%`, and `50%` year-on-year growth. That is useful because practitioners are not treating `3x` to `5x` as normal cooler-only lift. Source: "Improving Asset Allocation in a Fast Moving Consumer Goods B2B Company" ([arXiv](https://arxiv.org/html/2511.06642v1)).

Implication for this competition:

- Cooler addition alone justifies `1.3x` to `2.1x` for many constrained outlets.
- Cooler addition plus better placement and assortment can justify around `2x`.
- Cooler evidence alone does not justify `4x` to `5x`.

## 2. Credit limit relaxation

Trade credit evidence is strong on direction, weaker on universal uplift size:

- Order-based trade credit in nanostore channels is designed to reduce cash shortages and improve order quantity, supplier engagement, and operational performance. This directly matches Sri Lankan small retail logic, where shop cash flow can cap purchases even when demand exists. Source: "Order-Based Trade Credits and Operational Performance in the Nanostore Retail Channel" ([Tilburg University record](https://research.tilburguniversity.edu/en/publications/order-based-trade-credit-and-operational-performance-in-the-nanos)).
- The practical uplift should be treated as a liquidity multiplier, not a demand multiplier. If a shop is credit-constrained, higher credit can move it toward the peer frontier. If footfall is low, credit does not create demand.

Recommended numeric assumption:

- Use `1.05x` to `1.30x` as a normal credit-relaxation lift.
- Allow up to `1.50x` only when the outlet has high sales density signals but low current purchase volume.
- Do not use credit relaxation to justify caps above `3x` without bucket-level peer evidence.

## 3. SKU breadth expansion

Useful public numbers:

- NielsenIQ reports that assortment planning and optimization has delivered up to a `7%` increase in sales and gross profit while streamlining assortment by `10%`. Source: NIQ Activate assortment announcement ([NIQ](https://nielseniq.com/global/en/news-center/2025/niq-activates-assortment-planning-optimization-solution-brings-retailers-closer-to-consumers-through-precision-planning-and-localized-execution/)).
- NielsenIQ also reports an `11%` incremental growth case from assortment optimization. Source: "Achieving 11% incremental growth..." ([NIQ](https://nielseniq.com/global/en/insights/analysis/2023/achieving-11-incremental-growth-amidst-consumer-recession-with-assortment-optimization/)).
- Academic assortment work generally finds positive but category-dependent assortment elasticity. A longitudinal retail study finds that product variety and inventory levels affect store sales, but also warns that more variety can create "phantom products" and availability problems. Source: Ton and Raman, *Production and Operations Management*, "The Effect of Product Variety and Inventory Levels on Retail Store Sales" ([Wiley](https://onlinelibrary.wiley.com/doi/10.1111/j.1937-5956.2010.01120.x)).

Implication:

- SKU breadth is a real uplift signal, but normal assortment effects are closer to `1.07x` to `1.11x`, not `3x`.
- SKU breadth should strengthen the constraint score and peer frontier, not independently create a very high cap.

## 4. Stockout elimination and on-shelf availability

Useful public numbers:

- The global retail out-of-stock study reports an average FMCG out-of-stock rate around `8.3%`. Source: Gruen, Corsten, and Bharadwaj, "Retail Out-of-Stocks: A Worldwide Examination..." ([ReadKong mirror](https://www.readkong.com/page/retail-out-of-stock-study-3467133)).
- The same study reports that shopper responses vary: some substitute, some delay purchase, some switch stores, and some do not buy. That means eliminating stockouts usually recovers a fraction of lost demand, not all theoretical demand.
- Trade summaries cite out-of-stock costs of about `4%` of annual retailer sales and around `2.3%` of manufacturer sales in FMCG contexts.

Recommended numeric assumption:

- Normal availability recovery: `1.03x` to `1.10x`.
- Severe repeated stockout recovery: `1.15x` to `1.30x`.
- Stockout elimination does not justify `3x+` unless current history is clearly censored and peer outlets prove the missed demand.

## 5. Combined theoretical uplift

A simple multiplicative stack can explain why `2x` is plausible but `5x` is risky:

| Constraint removed | Conservative lift | Aggressive lift |
| --- | ---: | ---: |
| Cooler / chilled placement | `1.30x` | `2.10x` |
| Credit relaxation | `1.10x` | `1.50x` |
| SKU breadth / assortment | `1.07x` | `1.15x` |
| Stockout reduction | `1.05x` | `1.30x` |
| Combined | `1.58x` | `4.71x` |

Interpretation:

- `1.5x` to `2.5x` is commercially normal for constrained outlets.
- `3x` can be defended for small outlets with many simultaneous constraints.
- `4x` to `4.5x` should be rare and should require strong same-size, same-type peer evidence.
- `5x` is a stress-test cap, not a business-default cap.

# Critique of Team's Current Caps

Current guardrails:

| Outlet size | Current cap | Recommendation | Reason |
| --- | ---: | --- | --- |
| Unknown | `2.0x` | Keep | Missing size should not receive aggressive upside. |
| Small | `3.0x` | Keep as outer cap | Small shops can be highly constrained by cooler, credit, and SKU breadth. But make the actual cap bucket-estimated. |
| Medium | `3.5x` | Keep as outer cap | Plausible for under-ranged outlets in dense areas, but should bind rarely. |
| Large | `4.0x` | Keep only with peer proof | Large outlets already have more capacity. A `4x` jump needs same-type top-decile evidence. |
| Extra Large | `4.5x` | Lower to `4.0x` unless data proves otherwise | Extra Large outlets already average about `2,040L` max monthly volume in the EDA. A `4.5x` cap can imply very large absolute jumps. |

Main critique:

- The current caps are directionally sensible, but too easy to attack as hand-picked.
- The strongest defense is not "industry studies say 4.5x is possible." They usually do not.
- The better defense is: "The cap is the smaller of a business guardrail and an empirical peer-frontier ratio estimated inside each outlet-size and outlet-type bucket."

Current output check from the latest files:

| Metric | Current full prediction file |
| --- | ---: |
| Rows | `20,000` |
| Mean predicted liters | `453.76` |
| Median predicted liters | `269.70` |
| 90th percentile | `980.48` |
| 95th percentile | `1,307.90` |
| 98th percentile | `2,062.86` |
| 99th percentile | `2,105.37` |
| Max | `10,457.94` |
| Total liters | `9,075,182.78` |

Sensitivity interpretation:

| Uniform cap scenario | Expected final distribution effect | Business view |
| --- | --- | --- |
| `2x` | Would reduce only outlets whose model uplift exceeds `2x`. Exact rerun needs `prediction_diagnostics.csv`, which is not present in the committed `data/gold` folder. | Safest, but may understate true latent demand for heavily constrained small outlets. |
| `3x` | Should match the current run closely, because the methodology document says max uplift is below `3.0x`. | Most defensible default. |
| `4x` | Same as `3x` unless upstream raw potential increases. | Useful as a stress test, not needed as normal cap. |
| `5x` | Same as `3x` on the latest run if max uplift remains below `3.0x`. | Too loose for the report; invites reviewer pushback. |

Best competition answer:

- Use the current stepped caps as maximum possible ratios.
- Present `3x` as the practical business cap for the current model because the final output already stays below `3x`.
- Use `4x+` only as a non-binding safety ceiling for larger formats, not as a claim that such uplift is common.

# Recommended Cap Methodology

## 1. Estimate caps from the data

Create an empirical uplift ratio inside each `Outlet_Size x Outlet_Type` bucket:

```text
historical_max_i = max monthly liters observed for outlet i
bucket_median_b = median(historical_max_i) inside bucket b
bucket_top_decile_b = p90(historical_max_i) inside bucket b
raw_bucket_ratio_b = bucket_top_decile_b / bucket_median_b
```

Then bootstrap it:

```text
For each bucket b:
  Repeat 1,000 times:
    sample outlets in bucket b with replacement
    compute p90(sample historical_max) / median(sample historical_max)
  empirical_cap_b = p95(bootstrap ratios)
```

Recommended final cap:

```text
business_max_by_size = {
  Unknown: 2.0,
  Small: 3.0,
  Medium: 3.5,
  Large: 4.0,
  Extra Large: 4.0
}

final_cap_i = min(
  empirical_cap_for_size_type_bucket_i,
  business_max_by_size_i,
  peer_98th_percentile_i / lower_bound_i
)
```

Minimum sample rule:

- If a bucket has at least `100` outlets, use `Outlet_Size x Outlet_Type`.
- If it has `30` to `99` outlets, blend with size-level and type-level caps.
- If it has fewer than `30` outlets, use the size-level cap only.

## 2. Use shrinkage instead of a hard cliff

Hard caps create a visible pile-up at the cap. Replace this:

```text
prediction = min(raw_potential, lower_bound * cap)
```

with this:

```text
cap_value = lower_bound * final_cap
peer_anchor = peer_group_median + 0.75 * (peer_group_p90 - peer_group_median)

if raw_potential <= cap_value:
    prediction = raw_potential
else:
    excess = raw_potential - cap_value
    shrink_weight = n_bucket / (n_bucket + 50)
    prediction = cap_value + 0.25 * shrink_weight * excess
    prediction = min(prediction, peer_group_p98)
```

Plain meaning:

- If the model is below the cap, leave it alone.
- If the model crosses the cap, keep a small part of the excess only when the peer bucket is large enough to trust.
- This prevents artificial cliffs while still controlling extreme forecasts.

Bayesian version:

```text
bucket_cap = (n / (n + k)) * bucket_empirical_cap + (k / (n + k)) * size_prior_cap
```

Use `k = 50` as the prior strength.

## 3. Required sensitivity table for the notebook

The team should rerun the final prediction formula at uniform caps `2x`, `3x`, `4x`, and `5x`, then report:

```text
cap
mean_prediction
median_prediction
p90_prediction
p95_prediction
p99_prediction
max_prediction
total_liters
share_outlets_at_cap
share_total_liters_from_capped_outlets
```

Decision rule:

- If `3x`, `4x`, and `5x` are identical, say the model is frontier-limited, not cap-limited.
- If `5x` materially increases total liters, it is probably too loose.
- If `2x` materially reduces small outlets in dense catchments, it is probably too conservative.
- Pick the lowest cap where `total_liters`, `p99`, and `share_outlets_at_cap` stabilize.

## 4. Data fields to inspect before final cap choice

Check these before submission:

- `p90 / median historical_max_monthly_liters` by `Outlet_Size x Outlet_Type`.
- `p95 / median historical_max_monthly_liters` by `Outlet_Size x Outlet_Type`.
- `p98 / median historical_max_monthly_liters` by `Outlet_Size x Outlet_Type`.
- Median and p90 SKU count by bucket.
- Median and p90 cooler count by bucket.
- Share of zero-cooler outlets by size. Current EDA says `67.88%` of Small outlets have zero coolers.
- Top-decile versus median volume gap. Current EDA says median outlet max is `164.0L`, while p95 is `1,307.9L`, an `8.0x` cross-outlet gap. This supports a peer frontier, but caps must be bucket-specific.
- Ratio of final prediction to historical max by bucket.
- Number of outlets hitting each cap.
- Total liters contributed by capped outlets.

# Defensible Report Narrative

Use this wording:

> We model latent monthly potential as censored demand: observed purchases are a lower bound because outlets may be constrained by cold space, credit, SKU breadth, and stock availability. To avoid turning this into an unconstrained extrapolation, we apply evidence-based uplift guardrails. The guardrails are not arbitrary constants. They are anchored in peer-outlet frontier ratios inside each outlet-size and outlet-type bucket, then bounded by conservative business maxima. Public FMCG evidence shows that individual interventions such as cooler placement, assortment optimization, and availability improvements commonly produce `7%` to `114%` uplift, while combined constraints can justify larger but rare multipliers. Our final output remains conservative: median uplift is about `1.20x`, average uplift about `1.37x`, and maximum uplift remains below `3.0x` versus observed historical maximum.

Reviewer pushback and pre-emption:

| Pushback | Pre-emptive answer |
| --- | --- |
| "The caps are arbitrary." | Show the bootstrap `p90/median` and `p95/median` ratios by size-type bucket. |
| "Why can small outlets triple?" | Small outlets have the highest constraint risk: EDA shows `67.88%` have zero coolers, so cold-space and availability limits can censor demand. |
| "Why do Extra Large outlets get `4.5x`?" | Revise to `4.0x` unless the bucket bootstrap supports higher. Extra Large already has high capacity and high baseline volume. |
| "Industry studies do not support `5x`." | Agree. `5x` is only a stress test, not the selected cap. |
| "Your model may allocate too much to low-demand stores." | Use peer `p98`, catchment density, SKU breadth, cooler count, and shrinkage when the cap binds. |
| "Your model may just reproduce historical sales." | The model moves from lower bound toward peer frontier using constraint score, so it can estimate latent potential while staying bounded. |

Commercial risk framing:

- Too aggressive: sales teams over-allocate coolers, credit, and stock to outlets that cannot sell through. This creates dead inventory, warm stock, expiry risk, and poor working-capital use.
- Too conservative: the model becomes a historical-sales forecast and misses the competition target, which is latent maximum potential.
- Trade marketers handle this by ranking outlets by expected incremental return, not by unconstrained demand alone. A good cap should preserve upside where the peer frontier supports it, but penalize unsupported jumps.

Recommended final position:

- Keep `Small 3.0x`.
- Keep `Medium 3.5x`.
- Keep `Large 4.0x`, but require peer support.
- Change `Extra Large 4.5x` to `4.0x` unless bootstrap evidence supports `4.5x`.
- Keep `Unknown 2.0x`.
- Add empirical bucket caps and shrinkage. This is the strongest way to call the final cap "evidence-based."

# References

- Nakamura, R., Pechey, R., Suhrcke, M., Jebb, S. A., and Marteau, T. M. "Sales impact of displaying alcoholic and non-alcoholic beverages in end-of-aisle locations: An observational study." *Social Science & Medicine*. Reported uplift: alcoholic beverages `23%` to `46%`; non-alcoholic beverages `52%` to `114%`. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0277953614001361)
- Perfect Data. "Case Study." Reported commercial cooler and display uplifts: `19%`, `29%`, `30%+`, `38%`, `9%`, `27%`, and `12%` depending on intervention. [Perfect Data](https://perfect-data.pl/case-study/)
- NielsenIQ. "NIQ Activate's Assortment Planning & Optimization Solution..." Reported up to `7%` increase in sales and gross profit while streamlining assortment by `10%`. [NIQ](https://nielseniq.com/global/en/news-center/2025/niq-activates-assortment-planning-optimization-solution-brings-retailers-closer-to-consumers-through-precision-planning-and-localized-execution/)
- NielsenIQ. "Achieving 11% incremental growth amidst consumer recession with assortment optimization." Reported `11%` incremental growth from assortment optimization. [NIQ](https://nielseniq.com/global/en/insights/analysis/2023/achieving-11-incremental-growth-amidst-consumer-recession-with-assortment-optimization/)
- Gruen, T. W., Corsten, D. S., and Bharadwaj, S. "Retail Out-of-Stocks: A Worldwide Examination of Extent, Causes and Consumer Responses." Reported average FMCG out-of-stock rate around `8.3%`. [ReadKong mirror](https://www.readkong.com/page/retail-out-of-stock-study-3467133)
- Ton, Z., and Raman, A. "The Effect of Product Variety and Inventory Levels on Retail Store Sales: A Longitudinal Study." *Production and Operations Management*. Shows store sales depend on both variety and inventory, with operational risks from excess variety. [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/j.1937-5956.2010.01120.x)
- "Improving Asset Allocation in a Fast Moving Consumer Goods B2B Company: An Interpretable Machine Learning Framework for Commercial Cooler Assignment Based on Multi-Tier Growth Targets." Uses growth thresholds of `10%`, `30%`, and `50%` for cooler allocation. [arXiv](https://arxiv.org/html/2511.06642v1)
- "Order-Based Trade Credits and Operational Performance in the Nanostore Retail Channel." Trade credit can reduce cash shortages and improve order behavior in small retail channels. [Tilburg University](https://research.tilburguniversity.edu/en/publications/order-based-trade-credit-and-operational-performance-in-the-nanos)
