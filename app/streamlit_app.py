"""Outlet Intelligence web app (Final Round deliverable #4).

A Streamlit app for trade-marketing leaders to explore the latent-potential
model: browse every outlet, filter by province / distributor, drill into a
single outlet to see its predicted potential, the signed drivers behind the
score, an LLM-generated plain-language explanation (XAI), and — for the Western
province — the recommended LKR 5M promotional spend.

Run:
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.intelligence import load_intelligence_table  # noqa: E402
from src.xai import build_driver_payload, compute_panel_stats, explain_outlet  # noqa: E402

RESULTS = ROOT / "Results"

st.set_page_config(page_title="Outlet Intelligence — smile Labs", page_icon="🧊", layout="wide")


# --------------------------------------------------------------------------
# Data loading (cached)
# --------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading outlet intelligence…")
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    intel = load_intelligence_table()
    alloc_path = RESULTS / "smile_labs_budget_allocations_detailed.csv"
    alloc = pd.read_csv(alloc_path) if alloc_path.exists() else pd.DataFrame()
    return intel, alloc


@st.cache_data
def panel_stats(intel: pd.DataFrame):
    return compute_panel_stats(intel)


intel, alloc = load_data()
stats = panel_stats(intel)
alloc_by_id = alloc.set_index("Outlet_ID") if not alloc.empty else pd.DataFrame()


# --------------------------------------------------------------------------
# Sidebar — filters
# --------------------------------------------------------------------------
st.sidebar.title("🧊 Outlet Intelligence")
st.sidebar.caption("smile Labs · Data Storm v7.0 — Final Round")

provinces = ["All"] + sorted(intel["province"].dropna().unique().tolist())
prov_sel = st.sidebar.selectbox("Province", provinces, index=0)

scoped = intel if prov_sel == "All" else intel[intel["province"] == prov_sel]
dists = ["All"] + sorted(scoped["dominant_distributor"].dropna().unique().tolist())
dist_sel = st.sidebar.selectbox("Distributor", dists, index=0)
if dist_sel != "All":
    scoped = scoped[scoped["dominant_distributor"] == dist_sel]

types = sorted(scoped["Outlet_Type"].dropna().unique().tolist())
type_sel = st.sidebar.multiselect("Outlet type", types, default=types)
scoped = scoped[scoped["Outlet_Type"].isin(type_sel)] if type_sel else scoped

search = st.sidebar.text_input("Search Outlet_ID").strip().upper()
if search:
    scoped = scoped[scoped["Outlet_ID"].str.contains(search, na=False)]

st.sidebar.markdown("---")
st.sidebar.markdown("**XAI narrative**")
key_input = st.sidebar.text_input(
    "Anthropic API key (optional)", type="password",
    help="Paste sk-ant-… to generate live narratives. Leave blank to use the "
         "offline template. The key is held only for this session, never stored.",
)
# precedence: pasted key > Streamlit secret > env var
try:
    secret_key = st.secrets.get("ANTHROPIC_API_KEY", None)
except Exception:
    secret_key = None
active_key = key_input.strip() or secret_key or os.environ.get("ANTHROPIC_API_KEY")
st.session_state["active_api_key"] = active_key
api_status = "🟢 live (Anthropic)" if active_key else "⚪ offline template"
st.sidebar.caption(f"Mode: **{api_status}**")
st.sidebar.caption(f"{len(scoped):,} / {len(intel):,} outlets in view")


# --------------------------------------------------------------------------
# Header KPIs
# --------------------------------------------------------------------------
st.title("Outlet Purchase-Potential Explorer")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Outlets in view", f"{len(scoped):,}")
c2.metric("Total predicted potential", f"{scoped['predicted_potential_liters'].sum():,.0f} L")
c3.metric("Median uplift vs best month", f"{scoped['uplift_ratio'].median():.2f}×")
c4.metric("Total headroom", f"{scoped['headroom_liters'].sum():,.0f} L")

tab_browse, tab_outlet, tab_budget = st.tabs(
    ["📋 Browse outlets", "🔍 Outlet drill-down", "💰 Western spend plan"]
)

# --------------------------------------------------------------------------
# Tab 1 — browse
# --------------------------------------------------------------------------
with tab_browse:
    st.subheader("Outlet-level predictions")
    show_cols = [
        "Outlet_ID", "province", "dominant_distributor", "Outlet_Type", "Outlet_Size",
        "observed_mean_monthly_liters", "observed_max_monthly_liters",
        "predicted_potential_liters", "headroom_liters", "uplift_ratio",
        "competitor_count_500m",
    ]
    sort_col = st.selectbox("Sort by", ["predicted_potential_liters", "headroom_liters", "uplift_ratio"], index=0)
    view = scoped[show_cols].sort_values(sort_col, ascending=False)
    st.dataframe(
        view, use_container_width=True, height=460, hide_index=True,
        column_config={
            "predicted_potential_liters": st.column_config.NumberColumn("Potential (L)", format="%.0f"),
            "observed_mean_monthly_liters": st.column_config.NumberColumn("Normal (L)", format="%.0f"),
            "observed_max_monthly_liters": st.column_config.NumberColumn("Best month (L)", format="%.0f"),
            "headroom_liters": st.column_config.NumberColumn("Headroom (L)", format="%.0f"),
            "uplift_ratio": st.column_config.NumberColumn("Uplift", format="%.2f×"),
        },
    )
    st.download_button(
        "Download current view (CSV)", view.to_csv(index=False).encode(),
        file_name="outlet_view.csv", mime="text/csv",
    )
    if {"Latitude", "Longitude"}.issubset(scoped.columns):
        geo = scoped.dropna(subset=["Latitude", "Longitude"])
        if not geo.empty:
            st.caption("Geographic spread of outlets in view")
            st.map(geo.rename(columns={"Latitude": "lat", "Longitude": "lon"})[["lat", "lon"]], size=20)

# --------------------------------------------------------------------------
# Tab 2 — outlet drill-down + XAI
# --------------------------------------------------------------------------
with tab_outlet:
    if scoped.empty:
        st.warning("No outlets match the current filters.")
    else:
        oid = st.selectbox("Select an outlet", scoped["Outlet_ID"].tolist())
        row = intel[intel["Outlet_ID"] == oid].iloc[0]
        arow = alloc_by_id.loc[oid] if oid in alloc_by_id.index else None
        payload = build_driver_payload(row, stats, arow)

        left, right = st.columns([1, 1.2])
        with left:
            st.subheader(f"{oid}")
            st.caption(f"{row['Outlet_Size']} {row['Outlet_Type']} · {row['province']} · {row['dominant_distributor']}")
            m1, m2 = st.columns(2)
            m1.metric("Predicted potential", f"{payload.predicted_potential_liters:,.0f} L",
                      f"{(payload.uplift_vs_normal - 1) * 100:+.0f}% vs normal")
            m2.metric("Normal month", f"{payload.normal_baseline_liters:,.0f} L")
            m3, m4 = st.columns(2)
            m3.metric("Best month", f"{payload.best_month_liters:,.0f} L")
            m4.metric("Competitors ≤500 m", f"{int(row['competitor_count_500m'])}")
            if payload.allocation:
                st.success(
                    f"**Recommended trade spend: LKR {payload.allocation['trade_spend_lkr']:,.0f}** → "
                    f"+{payload.allocation['expected_incremental_liters']:,.0f} L "
                    f"(LKR {payload.allocation['expected_incremental_revenue_lkr']:,.0f})"
                )

            st.markdown("**Why this score — signed drivers**")
            for d in payload.drivers + payload.local_signals + payload.constraints:
                icon = {"increases": "🟢 ▲", "decreases": "🔴 ▼", "neutral": "⚪ ◼"}[d["direction"]]
                st.markdown(f"{icon} **{d['name']}** — {d['detail']}")

        with right:
            st.subheader("Plain-language explanation (XAI)")
            force_offline = st.toggle("Force offline template", value=False,
                                      help="Skip the Anthropic API even if a key is set.")
            if st.button("✨ Generate explanation", type="primary"):
                with st.spinner("Generating business narrative…"):
                    res = explain_outlet(
                        payload,
                        force_offline=force_offline,
                        api_key=st.session_state.get("active_api_key"),
                    )
                st.session_state[f"xai_{oid}"] = res
            res = st.session_state.get(f"xai_{oid}")
            if res:
                st.info(res["narrative"])
                st.caption(f"Source: {res['source']}" + (f" · {res['model']}" if res.get("model") else ""))
            else:
                st.caption("Click **Generate explanation** to produce the narrative.")
            with st.expander("Structured driver payload (sent to LLM)"):
                st.json(payload.to_dict())

# --------------------------------------------------------------------------
# Tab 3 — Western spend plan
# --------------------------------------------------------------------------
with tab_budget:
    st.subheader("Western Province — LKR 5M promotional allocation")
    if alloc.empty:
        st.warning("Run `python -m src.optimization.spend_allocation` to generate the plan.")
    else:
        funded = alloc[alloc["Trade_Spend_Allocation_LKR"] > 0]
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Budget", "LKR 5,000,000")
        b2.metric("Allocated", f"LKR {alloc['Trade_Spend_Allocation_LKR'].sum():,.0f}")
        b3.metric("Outlets funded", f"{len(funded):,} / {len(alloc):,}")
        b4.metric("Expected uplift", f"+{alloc['expected_incremental_liters'].sum():,.0f} L")
        st.caption(
            f"Expected incremental revenue: LKR {alloc['expected_incremental_revenue_lkr'].sum():,.0f} "
            f"· blended efficiency {alloc['expected_incremental_liters'].sum() / 5000:,.1f} L per 1,000 LKR"
        )
        st.dataframe(
            funded.sort_values("Trade_Spend_Allocation_LKR", ascending=False),
            use_container_width=True, height=420, hide_index=True,
            column_config={
                "Trade_Spend_Allocation_LKR": st.column_config.NumberColumn("Spend (LKR)", format="%.0f"),
                "expected_incremental_liters": st.column_config.NumberColumn("+Liters", format="%.0f"),
                "expected_incremental_revenue_lkr": st.column_config.NumberColumn("+Revenue (LKR)", format="%.0f"),
                "liters_per_1000_lkr": st.column_config.NumberColumn("L / 1k LKR", format="%.1f"),
            },
        )
        st.download_button(
            "Download allocation (submission CSV)",
            alloc[["Outlet_ID", "Trade_Spend_Allocation_LKR"]].to_csv(index=False).encode(),
            file_name="smile_labs_budget_allocations.csv", mime="text/csv",
        )
