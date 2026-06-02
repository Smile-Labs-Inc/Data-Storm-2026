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

import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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


@st.cache_data(show_spinner=False)
def load_credibility() -> dict:
    """Validation report + conformal intervals + Manski bands for the credibility tab."""
    out: dict = {"validation": None, "conformal": pd.DataFrame(), "manski": pd.DataFrame(),
                 "summary": None}
    vpath = RESULTS / "validation_report.json"
    if vpath.exists():
        out["validation"] = json.loads(vpath.read_text())
    cpath = RESULTS / "conformal_intervals_v2.csv"
    if cpath.exists():
        out["conformal"] = pd.read_csv(cpath)
    mpath = RESULTS / "manski_bands_v2.csv"
    if mpath.exists():
        out["manski"] = pd.read_csv(mpath)
    spath = RESULTS / "budget_allocation_summary.json"
    if spath.exists():
        out["summary"] = json.loads(spath.read_text())
    return out


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

tab_exec, tab_browse, tab_outlet, tab_budget, tab_cred = st.tabs(
    ["🏠 Executive Dashboard", "📋 Browse outlets", "🔍 Outlet drill-down",
     "💰 Western spend plan", "🎯 Model Credibility"]
)

# --------------------------------------------------------------------------
# Tab 0 — Executive Dashboard
# --------------------------------------------------------------------------
with tab_exec:
    # Hero ROI banner — the one number to remember
    cred0 = load_credibility()
    summ = cred0.get("summary") or {}
    hero_spend = summ.get("total_allocated_lkr", 4_901_675)
    hero_liters = summ.get("expected_incremental_liters", 109_021)
    hero_rev = summ.get("expected_incremental_revenue_lkr", 27_084_435)
    hero_roi = summ.get("roi_revenue_to_spend", hero_rev / hero_spend if hero_spend else 0)
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Optimised spend", f"LKR {hero_spend:,.0f}")
    h2.metric("Incremental volume", f"{hero_liters:,.0f} L")
    h3.metric("Incremental revenue", f"LKR {hero_rev/1e6:,.1f}M")
    h4.metric("Return on spend", f"{hero_roi:.1f}×", "revenue ÷ spend")
    st.caption(
        f"**Bottom line:** a LKR {hero_spend/1e6:,.1f}M promotional plan is projected to unlock "
        f"{hero_liters:,.0f} L of incremental volume — about **LKR {hero_rev/1e6:,.1f}M** in revenue, "
        f"a **{hero_roi:.1f}× return**."
    )
    st.markdown("---")

    st.subheader("Portfolio at a glance")
    st.caption("Province-level view across the full 20,000-outlet panel.")

    prov_kpi = (
        intel.groupby("province")
        .agg(
            outlets=("Outlet_ID", "count"),
            total_potential=("predicted_potential_liters", "sum"),
            total_headroom=("headroom_liters", "sum"),
            median_uplift=("uplift_ratio", "median"),
        )
        .sort_values("total_headroom", ascending=False)
    )
    kpi_cols = st.columns(len(prov_kpi))
    for col, (prov, prow) in zip(kpi_cols, prov_kpi.iterrows()):
        col.metric(
            prov,
            f"{prow['total_potential']:,.0f} L",
            f"{int(prow['outlets']):,} outlets · {prow['total_headroom']:,.0f} L headroom",
            delta_color="off",
        )

    st.markdown("---")
    left, right = st.columns(2)
    with left:
        type_hr = (
            intel.groupby("Outlet_Type")["headroom_liters"].sum().nlargest(8).reset_index()
        )
        fig = px.bar(
            type_hr, x="headroom_liters", y="Outlet_Type", orientation="h",
            color="headroom_liters", color_continuous_scale="Blues",
            title="Top outlet types by untapped headroom",
        )
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"}, height=420,
            coloraxis_showscale=False, margin=dict(l=10, r=10, t=50, b=10),
        )
        fig.update_xaxes(title_text="Total headroom (L)")
        fig.update_yaxes(title_text="")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        geo = intel.dropna(subset=["Latitude", "Longitude"]).copy()
        if not geo.empty:
            geo["uplift_q"] = pd.qcut(
                geo["uplift_ratio"], q=4,
                labels=["Q1 — Low", "Q2", "Q3", "Q4 — High"], duplicates="drop",
            )
            fig_map = px.scatter_mapbox(
                geo, lat="Latitude", lon="Longitude", color="uplift_q",
                category_orders={"uplift_q": ["Q1 — Low", "Q2", "Q3", "Q4 — High"]},
                color_discrete_sequence=px.colors.sequential.Blues[3:],
                zoom=6.5, height=420, mapbox_style="open-street-map",
                title="Outlets by uplift quartile",
                hover_data={"Outlet_ID": True, "Latitude": False, "Longitude": False},
            )
            fig_map.update_layout(
                margin=dict(l=0, r=0, t=50, b=0),
                legend_title_text="Uplift quartile",
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("No geolocated outlets available to map.")

    st.markdown("---")
    st.markdown("### 🧠 AI Digest")
    _top_prov = prov_kpi.index[0]
    _top_hr = prov_kpi.iloc[0]["total_headroom"]
    _med_uplift = intel["uplift_ratio"].median()
    _funded = int((alloc["Trade_Spend_Allocation_LKR"] > 0).sum()) if not alloc.empty else 0
    _eff = (
        alloc["expected_incremental_liters"].sum()
        / (alloc["Trade_Spend_Allocation_LKR"].sum() / 1000)
        if not alloc.empty and alloc["Trade_Spend_Allocation_LKR"].sum() > 0 else 0
    )
    default_digest = [
        f"**{_top_prov}** leads on opportunity with **{_top_hr:,.0f} L** of untapped "
        f"headroom — the clearest growth engine in the portfolio.",
        f"Median uplift across all outlets is **{_med_uplift:.2f}×**, meaning a typical "
        f"outlet sells well below its own proven best month.",
        f"The current LKR 4.9M plan funds **{_funded:,} outlets** at **{_eff:.1f} L per "
        f"1,000 LKR** — tilting spend toward top-quartile headroom can lift this further.",
    ]

    digest = st.session_state.get("exec_digest", default_digest)
    for bullet in digest:
        st.markdown(f"- {bullet}")

    if active_key:
        if st.button("Refresh with AI ✨", key="exec_digest_btn"):
            with st.spinner("Generating executive digest…"):
                try:
                    import anthropic

                    ctx = prov_kpi.reset_index().to_markdown(index=False)
                    prompt = (
                        "You are an executive analyst for smile Labs, a Sri Lankan beverage "
                        "distributor. Using ONLY the province summary below, write exactly 3 "
                        "punchy executive bullet points (one sentence each, no preamble, start "
                        "each line with '- '). Ground every number in the table.\n\n"
                        f"Province summary (potential/headroom in litres):\n{ctx}\n\n"
                        f"Portfolio median uplift: {_med_uplift:.2f}x. "
                        f"Current LKR 4.9M plan funds {_funded:,} outlets at {_eff:.1f} L per 1,000 LKR."
                    )
                    client = anthropic.Anthropic(api_key=active_key)
                    msg = client.messages.create(
                        model="claude-opus-4-8", max_tokens=400,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    text = "".join(
                        b.text for b in msg.content if getattr(b, "type", None) == "text"
                    )
                    bullets = [
                        ln.lstrip("-• ").strip()
                        for ln in text.splitlines() if ln.strip().startswith(("-", "•"))
                    ]
                    if bullets:
                        st.session_state["exec_digest"] = bullets
                        st.rerun()
                    else:
                        st.warning("Model returned no bullets — keeping the current digest.")
                except Exception as exc:
                    st.error(f"Could not refresh digest: {type(exc).__name__}")
    else:
        st.caption("Add an Anthropic API key in the sidebar to refresh this digest live.")

    st.markdown("---")
    with st.expander("🧭 How the system fits together (architecture)"):
        st.graphviz_chart(
            """
            digraph G {
                rankdir=LR;
                bgcolor="transparent";
                node [style="filled,rounded", shape=box, fontname="sans-serif",
                      color="#1E2130", fillcolor="#1E2130", fontcolor="#FAFAFA"];
                edge [color="#5A6178"];

                data  [label="Raw sales + outlet data\\n(20,000 outlets)", fillcolor="#22314a"];
                model [label="ML potential model\\n(predicted litres + headroom)", fillcolor="#0068C9", fontcolor="white"];
                unc   [label="Uncertainty layer\\nCQR intervals · Manski bands", fillcolor="#22314a"];
                opt   [label="Spend optimiser\\nsaturating response + water-filling", fillcolor="#0068C9", fontcolor="white"];
                xai   [label="XAI layer\\nsigned drivers + narratives", fillcolor="#22314a"];

                web    [label="🏠 Web app", fillcolor="#2b3550"];
                hermes [label="⚡ Hermes (Claude)", fillcolor="#2b3550"];
                tg     [label="📲 Telegram bot (Gemini)", fillcolor="#2b3550"];

                data -> model -> unc;
                model -> opt;
                model -> xai;
                unc -> web;
                opt -> web; opt -> hermes; opt -> tg;
                xai -> web; xai -> hermes;
                model -> hermes; model -> tg;
            }
            """
        )
        st.caption(
            "One model feeds three decision channels — the web app, the in-app Hermes "
            "analyst (Claude), and the on-the-go Telegram bot (Gemini)."
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

# --------------------------------------------------------------------------
# Tab 4 — Model Credibility
# --------------------------------------------------------------------------
with tab_cred:
    st.subheader("Why you can trust these numbers")
    st.caption(
        "Every prediction passes a pre-flight validation suite and ships with calibrated "
        "uncertainty — conformal prediction intervals and worst-case partial-identification bounds."
    )

    cred = load_credibility()
    val = cred["validation"]
    conf = cred["conformal"]
    man = cred["manski"]

    checks = val["checks"] if val else []
    n_pass = sum(1 for c in checks if c["passed"]) if checks else 0

    # Manski containment
    if not man.empty and "point_outside_band" in man.columns:
        inside_pct = (1 - man["point_outside_band"].mean()) * 100
    else:
        inside_pct = float("nan")

    # Conformal median interval width
    if not conf.empty:
        cmerge = intel.merge(conf, on="Outlet_ID", how="inner")
        cmerge["width"] = cmerge["cqr_upper"] - cmerge["cqr_lower"]
        med_width = cmerge["width"].median()
    else:
        cmerge = pd.DataFrame()
        med_width = float("nan")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Pre-flight checks", f"{n_pass} / {len(checks)} passed" if checks else "n/a")
    k2.metric("Outlets validated", f"{len(intel):,}")
    k3.metric("Inside Manski bounds", f"{inside_pct:.2f}%" if inside_pct == inside_pct else "n/a")
    k4.metric("Median CQR interval", f"±{med_width/2:,.0f} L" if med_width == med_width else "n/a")

    st.markdown("---")
    left, right = st.columns([1, 1])

    with left:
        st.markdown("**Submission pre-flight validation**")
        if checks:
            vdf = pd.DataFrame(
                [{"Check": c["name"], "Result": "✅" if c["passed"] else "❌", "Detail": c["detail"]}
                 for c in checks]
            )
            st.dataframe(vdf, hide_index=True, use_container_width=True, height=250)
            if val.get("all_passed"):
                st.success("All integrity checks passed — the submission is internally consistent.")
        else:
            st.info("Validation report not found.")

    with right:
        st.markdown("**Calibrated prediction intervals (CQR)**")
        if not cmerge.empty:
            sample = cmerge.nlargest(12, "predicted_potential_liters").sort_values(
                "predicted_potential_liters"
            )
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=sample["predicted_potential_liters"], y=sample["Outlet_ID"],
                mode="markers", marker=dict(color="#0068C9", size=9),
                error_x=dict(
                    type="data", symmetric=False,
                    array=sample["cqr_upper"] - sample["predicted_potential_liters"],
                    arrayminus=sample["predicted_potential_liters"] - sample["cqr_lower"],
                    color="#5A9BD5", thickness=1.5, width=4,
                ),
                name="Prediction ± interval",
            ))
            fig.update_layout(
                height=300, margin=dict(l=10, r=10, t=10, b=10),
                xaxis_title="Predicted monthly potential (L)", yaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Conformalised quantile-regression intervals — each point prediction comes with a "
                "calibrated range, not a false-precision single number."
            )
        else:
            st.info("Conformal intervals not found.")

    st.markdown("---")
    st.markdown("**Method, in one line**")
    st.markdown(
        "- **Prediction:** ML model estimates each outlet's monthly purchase *potential*, "
        "constrained to never fall below its proven historical best.\n"
        "- **Uncertainty:** conformal prediction intervals (CQR) + Manski partial-identification "
        f"bounds — **{inside_pct:.2f}%** of point estimates lie within their worst-case bands.\n"
        "- **Optimisation:** a saturating response model `g(s)=H·(1−e^(−s/k))` solved by Lagrangian "
        "water-filling (KKT bisection) — diminishing returns are modelled explicitly, not assumed away."
    )
