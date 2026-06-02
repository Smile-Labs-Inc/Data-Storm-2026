"""Scenario Planner — what-if budget sizing for the trade-spend plan.

Scales the optimised LKR 4.9M allocation linearly to let a trade-marketing
leader see the projected volume, outlet reach, and revenue impact of a
different promotional budget in real time.

The baseline is read from the actual allocation CSV; if it is missing, sensible
fallback constants (the figures from the Final Round submission) are used.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "Results"

st.set_page_config(page_title="Scenario Planner — smile Labs", page_icon="📈", layout="wide")

# Fallback constants (Final Round submission figures)
BASE_BUDGET = 4_901_675     # LKR actually allocated
BASE_OUTLETS = 3_729        # outlets funded
BASE_LITERS = 109_021       # expected incremental litres
REV_PER_LITER = 248         # LKR revenue per incremental litre


@st.cache_data(show_spinner=False)
def load_baseline() -> tuple[float, int, float, float]:
    path = RESULTS / "smile_labs_budget_allocations_detailed.csv"
    if not path.exists():
        return BASE_BUDGET, BASE_OUTLETS, BASE_LITERS, REV_PER_LITER
    a = pd.read_csv(path)
    funded = a[a["Trade_Spend_Allocation_LKR"] > 0]
    budget = float(a["Trade_Spend_Allocation_LKR"].sum())
    outlets = int(len(funded))
    liters = float(funded["expected_incremental_liters"].sum())
    rev = (
        float(funded["expected_incremental_revenue_lkr"].sum() / liters)
        if liters > 0 else REV_PER_LITER
    )
    return budget, outlets, liters, rev


base_budget, base_outlets, base_liters, rev_per_liter = load_baseline()
efficiency = base_liters / (base_budget / 1000)  # L per 1,000 LKR

st.title("📈 Scenario Planner")
st.caption(
    "Size the promotional budget and see the projected commercial impact, scaled from "
    "the optimised LKR 4.9M allocation."
)

c1, c2, c3 = st.columns(3)
c1.metric("Baseline budget", f"LKR {base_budget:,.0f}")
c2.metric("Baseline outlets funded", f"{base_outlets:,}")
c3.metric("Baseline efficiency", f"{efficiency:.1f} L / 1k LKR")

st.markdown("---")

budget = st.slider(
    "Promotional budget (LKR)",
    min_value=500_000, max_value=10_000_000, value=5_000_000, step=100_000,
    format="LKR %d",
)

scale = budget / base_budget
est_liters = base_liters * scale
est_outlets = int(base_outlets * min(scale, 1.15))  # soft cap: outlet base is finite
est_revenue = est_liters * rev_per_liter

m1, m2, m3 = st.columns(3)
m1.metric("Outlets funded", f"{est_outlets:,}", f"{est_outlets - base_outlets:+,}")
m2.metric("Incremental volume", f"{est_liters:,.0f} L", f"{est_liters - base_liters:+,.0f} L")
m3.metric("Est. revenue uplift", f"LKR {est_revenue:,.0f}")

if scale > 1.15:
    st.caption(
        "⚠️ Outlet reach is soft-capped: above ~15% over baseline, extra budget deepens "
        "spend on already-funded outlets rather than reaching new ones."
    )

st.markdown("---")

budgets = list(range(500_000, 10_100_000, 100_000))
curve = pd.DataFrame(
    {"Budget (LKR)": budgets, "Incremental Liters": [base_liters * (b / base_budget) for b in budgets]}
)
fig = px.line(
    curve, x="Budget (LKR)", y="Incremental Liters",
    title="Volume vs. budget (linear response model)",
)
fig.update_traces(line_color="#0068C9")
fig.add_vline(
    x=budget, line_dash="dash", line_color="orange",
    annotation_text=f"LKR {budget:,.0f}", annotation_position="top left",
)
fig.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10))
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Linear what-if model for planning conversations. Actual returns are non-linear: "
    "the optimiser front-loads the highest-efficiency outlets, so marginal litres "
    "decline as the budget grows beyond the funded base."
)
