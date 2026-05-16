# Research Swarm: 10 parallel channels (Round 0 pattern)

Use this ONCE per new competition / methodology landscape scan. ~$30-60 in
subagent cost. Each channel agent uses WebSearch + WebFetch to produce a
cited research file.

This is what built the original `research/research_brief.md` for Data Storm.
Adapt the channel topics to a new competition.

---

## Mission

Run 10 parallel research subagents (Task tool), one per channel below. Each
channel covers a distinct angle of the problem domain. Synthesize into one
master `research/research_brief.md` at the end.

## Step 1 -- Launch 10 critics in ONE parallel Task batch

Use `claude-opus-4-7-thinking-xhigh` for 7 channels and `gpt-5.5-extra-high`
for 3 channels (diversity of blind spots). Each agent gets:

- Common context block (define for your comp; see Data Storm example below)
- One channel-specific deep-dive question
- Instruction to use WebSearch + WebFetch aggressively
- Output path: `research/0X_<channel_name>.md`
- Structure: TL;DR (3 bullets), Key Findings, Concrete Recommendations,
  References (URLs)

## Common context block template (Data Storm example -- adapt for your comp)

```
COMPETITION CONTEXT (same for all channels):
- Predict latent maximum monthly volume potential (liters) for 20,000 Sri
  Lanka beverage retail outlets, January 2026.
- NO ground truth. Historical sales are CENSORED: observed = min(true_demand,
  operational_constraints like credit limits, stockouts, delivery caps).
- Judging is 100% qualitative: Data Engineering & Forensics 40%,
  Methodology & Base Math 40%, GenAI Workflow 20%.

DATA AVAILABLE:
- 20,000 outlets across 4 provinces, 10 distributors, 7 outlet types,
  4 sizes, cooler counts.
- Outlet coordinates (lat/lon).
- 2.37M transactions across 36 months (2023-2025), 10 SKUs.
- Distributor monthly seasonality.
- Holiday list.
- POI data NOT provided -- teams must scrape (OSM Overpass etc.).
```

## The 10 channels (Data Storm example -- replace topics for new comp)

| # | Channel | Model | Focus question |
|---|---|---|---|
| 1 | latent_demand_modeling | opus thinking | Tobit, censored QR, Manski bounds, deep censored regression |
| 2 | stochastic_frontier_analysis | opus thinking | Aigner-Lovell-Schmidt SFA, Battese-Coelli, JLMS efficiency |
| 3 | quantile_regression_for_potential | opus thinking | Multi-quantile + Conformalised QR + crossing fixes |
| 4 | osm_overpass_for_sri_lanka | opus thinking | Geofabrik PBF, Overpass QL, pyrosm, country-specific coverage |
| 5 | sri_lanka_fmcg_market | gpt-5.5 | Domain context (channels, seasonality, regional dynamics) |
| 6 | poi_feature_engineering | opus thinking | BallTree + Gaussian decay + Huff + cannibalisation |
| 7 | constraint_likelihood_methods | opus thinking | PCA + frontier-residual + plateau composite |
| 8 | past_data_storm_winners | gpt-5.5 | Past comp writeups, winning patterns, judge preferences |
| 9 | causal_inference_unobserved_demand | opus thinking | Heckman, IV, RD, Manski, EconML CATE |
| 10 | defensible_uplift_caps | gpt-5.5 | Industry benchmarks for retail uplift, bootstrap caps |

## Per-channel prompt template

```
You are channel <N> of 10 in a parallel research swarm for <comp name>.

COMPETITION CONTEXT:
<paste the common block above>

YOUR CHANNEL: <channel_name>
YOUR TASK:
<5-10 specific questions in the channel's deep-dive area>

INSTRUCTIONS:
1. Use WebSearch and WebFetch aggressively. Prefer 2020+ sources,
   peer-reviewed papers, library docs, reputable blogs.
2. Be concrete: name techniques, give equations, name Python libraries,
   cite sources with URLs.
3. Map every recommendation to the specific data above. No generic advice.
4. Write your full output to:
   D:/projects/Data-Storm-2026/research/0<N>_<channel_name>.md
5. Format: # TL;DR (3 bullets), # Key Findings, # Concrete Recommendations
   for THIS Comp, # References (URLs).
6. Return a 5-line summary in your response.
```

## Step 2 -- Synthesize

After all 10 finish, read every `research/0X_<name>.md` and write
`research/research_brief.md` with:

- TL;DR (3 bullets -- the big convergent recommendations)
- Convergent findings (where 2+ channels agree)
- Critical bugs / risks surfaced
- Top-5 action plan (ranked by ROI in remaining time)
- Open methodology debates (where channels disagree)
- Domain notes (Sri Lanka specifics in this case)
- POI playbook (or whatever the equivalent external-data step is)
- Per-channel quick references (table)
- Methodology story arc for the final report

## Tips

- Don't run this every cycle. Once per new comp is enough.
- Channels 1, 2, 9 are mathematically dense -- opus thinking is right.
- Channels 5, 8, 10 are market/industry -- gpt-5.5 gives a different lens.
- Channel 4 (POI scraping for THIS country) is the highest-volatility one --
  the recommendation here drives a multi-hour engineering investment.
- The synthesis is yours to write -- don't outsource it to an 11th subagent
  unless the 10 outputs are very large (>30 KB each).
