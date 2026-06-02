"""Scenario Planner — what-if budget sizing grounded in the real optimiser.

Instead of a naive linear projection, the response curve is reconstructed from
the optimiser's own output: every funded outlet carries a marginal efficiency
(litres per 1,000 LKR), and the optimiser funds the most efficient outlets
first. Sorting funded outlets by efficiency and taking the cumulative spend vs
cumulative litres reproduces the true **diminishing-returns frontier** — the
6th million rupee buys fewer litres than the first.

Underlying optimiser model: g(s) = H·(1 − e^(−s/k)) per outlet, solved by
Lagrangian water-filling (KKT bisection).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "Results"

st.set_page_config(page_title="Scenario Planner — smile Labs", page_icon="📈", layout="wide")

# Fallback constants (Final Round submission figures)
FALLBACK = dict(budget=4_901_675.0, outlets=3_729, liters=109_021.0, rev_per_liter=248.4)


@st.cache_data(show_spinner=False)
def load_frontier() -> dict:
    """Reconstruct the optimiser's marginal-returns frontier from its output."""
    path = RESULTS / "smile_labs_budget_allocations_detailed.csv"
    if not path.exists():
        return None
    a = pd.read_csv(path)
    fu = a[a["Trade_Spend_Allocation_LKR"] > 0].copy()
    if fu.empty:
        return None
    # Fund the most efficient outlets first → diminishing returns.
    fu = fu.sort_values("liters_per_1000_lkr", ascending=False)
    cum_spend = fu["Trade_Spend_Allocation_LKR"].cumsum().to_numpy()
    cum_liters = fu["expected_incremental_liters"].cumsum().to_numpy()
    sat_spend = float(cum_spend[-1])
    sat_liters = float(cum_liters[-1])
    rev_per_liter = float(
        fu["expected_incremental_revenue_lkr"].sum() / sat_liters
    ) if sat_liters else FALLBACK["rev_per_liter"]
    # Marginal efficiency of the least-efficient funded slice → extrapolation rate.
    tail = fu.tail(max(1, len(fu) // 10))
    tail_rate = float(tail["liters_per_1000_lkr"].mean()) / 1000.0  # L per LKR
    return dict(
        cum_spend=cum_spend, cum_liters=cum_liters, sat_spend=sat_spend,
        sat_liters=sat_liters, n_funded=int(len(fu)), rev_per_liter=rev_per_liter,
        tail_rate=tail_rate,
    )


F = load_frontier()


def project(budget: float):
    """Return (liters, outlets, revenue, region) for a given budget."""
    if F is None:
        scale = budget / FALLBACK["budget"]
        liters = FALLBACK["liters"] * scale
        outlets = int(FALLBACK["outlets"] * min(scale, 1.15))
        return liters, outlets, liters * FALLBACK["rev_per_liter"], "Optimised allocation"

    if budget <= F["sat_spend"]:
        liters = float(np.interp(budget, F["cum_spend"], F["cum_liters"]))
        outlets = int((F["cum_spend"] <= budget).sum())
        region = "Optimised allocation"
    else:
        # Beyond the optimiser's deployed spend: extrapolate at the declining
        # tail efficiency (already below the blended rate → diminishing returns).
        extra = budget - F["sat_spend"]
        liters = F["sat_liters"] + extra * F["tail_rate"]
        outlets = F["n_funded"]
        region = "Extrapolated (diminishing)"
    return liters, outlets, liters * F["rev_per_liter"], region


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
base_budget = F["sat_spend"] if F else FALLBACK["budget"]
base_liters = F["sat_liters"] if F else FALLBACK["liters"]
base_outlets = F["n_funded"] if F else FALLBACK["outlets"]
base_eff = base_liters / (base_budget / 1000)

st.title("📈 Scenario Planner")
st.caption(
    "Size the promotional budget and see the projected impact — modelled on the "
    "optimiser's own diminishing-returns frontier, not a flat linear guess."
)

c1, c2, c3 = st.columns(3)
c1.metric("Optimised baseline budget", f"LKR {base_budget:,.0f}")
c2.metric("Outlets funded at baseline", f"{base_outlets:,}")
c3.metric("Baseline efficiency", f"{base_eff:.1f} L / 1k LKR")

st.markdown("---")

budget = st.slider(
    "Promotional budget (LKR)",
    min_value=500_000, max_value=10_000_000, value=5_000_000, step=100_000,
    format="LKR %d",
)

est_liters, est_outlets, est_revenue, region = project(budget)

m1, m2, m3 = st.columns(3)
m1.metric("Outlets funded", f"{est_outlets:,}", f"{est_outlets - base_outlets:+,}")
m2.metric("Incremental volume", f"{est_liters:,.0f} L", f"{est_liters - base_liters:+,.0f} L")
m3.metric("Est. revenue uplift", f"LKR {est_revenue:,.0f}")

if region == "Extrapolated (diminishing)":
    st.warning(
        "⚠️ Above the optimiser's deployed spend, every extra rupee earns the **tail "
        f"efficiency** ({F['tail_rate']*1000:.1f} L per 1,000 LKR) — below the blended "
        f"{base_eff:.1f}. The marginal return is falling: this is the diminishing-returns region."
    )
else:
    cur_eff = est_liters / (budget / 1000) if budget else 0
    st.info(
        f"At this budget the plan funds the most efficient **{est_outlets:,} outlets** at a "
        f"blended **{cur_eff:.1f} L per 1,000 LKR**. Efficiency is highest at low budgets and "
        f"tapers as lower-ROI outlets are added."
    )

st.markdown("---")

# --------------------------------------------------------------------------
# Response curve — real frontier + extrapolation
# --------------------------------------------------------------------------
grid = list(range(500_000, 10_100_000, 100_000))
ys = [project(b)[0] for b in grid]
regions = [project(b)[3] for b in grid]
opt_x = [b for b, r in zip(grid, regions) if r == "Optimised allocation"]
opt_y = [y for y, r in zip(ys, regions) if r == "Optimised allocation"]
ext_x = [b for b, r in zip(grid, regions) if r != "Optimised allocation"]
ext_y = [y for y, r in zip(ys, regions) if r != "Optimised allocation"]
# bridge the two segments visually
if opt_x and ext_x:
    ext_x = [opt_x[-1]] + ext_x
    ext_y = [opt_y[-1]] + ext_y

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=opt_x, y=opt_y, mode="lines", name="Optimised allocation",
    line=dict(color="#0068C9", width=3),
))
if ext_x:
    fig.add_trace(go.Scatter(
        x=ext_x, y=ext_y, mode="lines", name="Extrapolated (diminishing)",
        line=dict(color="#5A9BD5", width=2, dash="dash"),
    ))
fig.add_vline(
    x=base_budget, line_dash="dot", line_color="#888",
    annotation_text="Optimiser saturation", annotation_position="top left",
)
fig.add_vline(
    x=budget, line_dash="dash", line_color="orange",
    annotation_text=f"LKR {budget:,.0f}", annotation_position="top right",
)
fig.update_layout(
    height=440, margin=dict(l=10, r=10, t=30, b=10),
    xaxis_title="Promotional budget (LKR)", yaxis_title="Incremental volume (L)",
    title="Volume vs. budget — optimiser response frontier",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Solid line: the optimiser's realised response, reconstructed from its per-outlet "
    "marginal efficiencies (it funds the highest-ROI outlets first). Dashed line: "
    "extrapolation beyond the deployed spend at the declining tail rate. The curve bends "
    "because returns genuinely diminish — modelled by g(s)=H·(1−e^(−s/k)), solved by "
    "Lagrangian water-filling."
)
