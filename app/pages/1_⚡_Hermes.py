"""Hermes — conversational outlet-intelligence analyst.

A streaming Claude-powered chat agent grounded in the 20,000-outlet panel.
Falls back to a deterministic keyword-matched demo mode when no Anthropic API
key is available, so the page is always usable offline.

Run via the main app's sidebar (Streamlit multipage) or:
    streamlit run app/streamlit_app.py   # then open ⚡ Hermes in the sidebar
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.intelligence import load_intelligence_table  # noqa: E402

RESULTS = ROOT / "Results"

st.set_page_config(page_title="Hermes — Outlet Analyst", page_icon="⚡", layout="wide")


# --------------------------------------------------------------------------
# Data + context (cached)
# --------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading outlet intelligence…")
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    intel = load_intelligence_table()
    alloc_path = RESULTS / "smile_labs_budget_allocations_detailed.csv"
    alloc = pd.read_csv(alloc_path) if alloc_path.exists() else pd.DataFrame()
    return intel, alloc


@st.cache_data(show_spinner=False)
def build_context(intel: pd.DataFrame, alloc: pd.DataFrame) -> str:
    prov_ctx = (
        intel.groupby("province")
        .agg(
            outlets=("Outlet_ID", "count"),
            total_potential=("predicted_potential_liters", "sum"),
            total_headroom=("headroom_liters", "sum"),
            median_uplift=("uplift_ratio", "median"),
        )
        .round(2)
        .to_markdown()
    )
    top10 = (
        intel.nlargest(10, "headroom_liters")[
            ["Outlet_ID", "province", "Outlet_Type", "headroom_liters", "uplift_ratio"]
        ]
        .round(2)
        .to_markdown(index=False)
    )
    if not alloc.empty:
        funded = alloc[alloc["Trade_Spend_Allocation_LKR"] > 0]
        budget_ctx = (
            f"- Total promotional spend allocated: LKR {alloc['Trade_Spend_Allocation_LKR'].sum():,.0f}\n"
            f"- Outlets funded: {len(funded):,} of {len(alloc):,} (Western province)\n"
            f"- Expected incremental volume: {alloc['expected_incremental_liters'].sum():,.0f} L\n"
            f"- Blended efficiency: "
            f"{alloc['expected_incremental_liters'].sum() / (alloc['Trade_Spend_Allocation_LKR'].sum() / 1000):.1f} "
            f"L per 1,000 LKR"
        )
    else:
        budget_ctx = "- No allocation plan available."

    return (
        "## Province summary (potential & headroom in litres)\n"
        f"{prov_ctx}\n\n"
        "## Top 10 outlets by untapped headroom\n"
        f"{top10}\n\n"
        "## Current trade-spend allocation\n"
        f"{budget_ctx}\n"
    )


intel, alloc = load_data()
DATA_CTX = build_context(intel, alloc)

SYSTEM_PROMPT = (
    "You are Hermes, the outlet intelligence analyst for smile Labs, a Sri Lankan "
    "beverage distributor. You have access to a panel of 20,000 retail outlets with "
    "model-predicted monthly purchase potential, untapped headroom, and a recommended "
    "trade-spend allocation.\n\n"
    "DATA YOU CAN USE:\n"
    f"{DATA_CTX}\n\n"
    "Ground ALL answers strictly in the data above — never invent outlet IDs or numbers. "
    "Respond in under 200 words. Prefer short bullet points. Be direct and commercial: "
    "speak to a trade-marketing leader, not a data scientist."
)


# --------------------------------------------------------------------------
# Offline fallback (no API key) — keyword-matched demo responses
# --------------------------------------------------------------------------
def _offline_reply(question: str) -> str:
    q = question.lower()
    prov = (
        intel.groupby("province")["headroom_liters"].sum().sort_values(ascending=False)
    )
    top_prov = prov.index[0]
    top_prov_hr = prov.iloc[0]
    med_uplift = intel["uplift_ratio"].median()
    funded = int((alloc["Trade_Spend_Allocation_LKR"] > 0).sum()) if not alloc.empty else 0
    eff = (
        alloc["expected_incremental_liters"].sum()
        / (alloc["Trade_Spend_Allocation_LKR"].sum() / 1000)
        if not alloc.empty and alloc["Trade_Spend_Allocation_LKR"].sum() > 0 else 0
    )
    top_types = (
        intel.groupby("Outlet_Type")["headroom_liters"].sum().nlargest(3)
    )

    if any(k in q for k in ("headroom", "untapped", "province", "most")):
        return (
            f"**{top_prov}** province holds the most untapped headroom at "
            f"**{top_prov_hr:,.0f} L**, ahead of every other region. It combines the "
            f"largest outlet base with consistently high uplift, so it is the natural "
            f"priority for promotional investment."
        )
    if any(k in q for k in ("type", "prioritise", "prioritize", "channel")):
        lines = "\n".join(f"- **{t}** — {v:,.0f} L headroom" for t, v in top_types.items())
        return f"Prioritise these outlet types by total untapped headroom:\n{lines}"
    if any(k in q for k in ("efficient", "efficiency", "allocation", "spend", "budget")):
        return (
            f"The current LKR 4.9M plan funds **{funded:,} outlets** at a blended "
            f"**{eff:.1f} L per 1,000 LKR**. It is concentrated in Western province where "
            f"headroom is deepest. Reallocating marginal spend toward top-quartile-headroom "
            f"outlets would push efficiency higher still."
        )
    if any(k in q for k in ("top 5", "top five", "opportunit", "investment", "summar")):
        top5 = intel.nlargest(5, "headroom_liters")[
            ["Outlet_ID", "province", "Outlet_Type", "headroom_liters"]
        ]
        lines = "\n".join(
            f"- **{r.Outlet_ID}** ({r.Outlet_Type}, {r.province}) — {r.headroom_liters:,.0f} L headroom"
            for r in top5.itertuples()
        )
        return f"Top 5 investment opportunities by untapped headroom:\n{lines}"
    if "out_" in q:
        oid = next((w.upper() for w in q.replace("?", " ").split() if w.lower().startswith("out_")), None)
        match = intel[intel["Outlet_ID"] == oid] if oid else pd.DataFrame()
        if not match.empty:
            r = match.iloc[0]
            return (
                f"**{r['Outlet_ID']}** is a {r['Outlet_Size']} {r['Outlet_Type']} in "
                f"{r['province']} province. Predicted potential **{r['predicted_potential_liters']:,.0f} L** "
                f"with **{r['headroom_liters']:,.0f} L** of headroom and a "
                f"**{r['uplift_ratio']:.2f}×** uplift over its normal month — a strong growth candidate."
            )

    return (
        "I'm running in **offline demo mode** (no API key set). I can answer questions "
        "about province headroom, priority outlet types, trade-spend efficiency, the top "
        "investment opportunities, or a specific outlet ID. Add an Anthropic API key in "
        "the sidebar for full conversational answers."
    )


# --------------------------------------------------------------------------
# Sidebar — key + controls
# --------------------------------------------------------------------------
st.sidebar.title("⚡ Hermes")
st.sidebar.caption("Outlet intelligence analyst · smile Labs")

key_input = st.sidebar.text_input(
    "Anthropic API key", type="password",
    help="Paste sk-ant-… for live streaming answers. Held only for this session.",
)
try:
    secret_key = st.secrets.get("ANTHROPIC_API_KEY", None)
except Exception:
    secret_key = None
active_key = (
    key_input.strip()
    or st.session_state.get("active_api_key")
    or secret_key
    or os.environ.get("ANTHROPIC_API_KEY")
)
if key_input.strip():
    st.session_state["active_api_key"] = key_input.strip()
mode = "🟢 live streaming (Anthropic)" if active_key else "⚪ offline demo mode"
st.sidebar.caption(f"Mode: **{mode}**")

if st.sidebar.button("🗑️ Clear conversation"):
    st.session_state.messages = []
    st.rerun()


# --------------------------------------------------------------------------
# Chat state + suggested questions
# --------------------------------------------------------------------------
st.title("⚡ Hermes — ask the outlet panel anything")
st.caption("Grounded in 20,000 Sri Lankan beverage outlets and the live trade-spend plan.")

if "messages" not in st.session_state:
    st.session_state.messages = []

SUGGESTED = [
    "Which province has the most untapped headroom?",
    "Which outlet types should we prioritise?",
    "How efficient is the current trade-spend allocation?",
    "Summarise the top 5 investment opportunities.",
    "What makes OUT_18995 notable?",
]

pending: str | None = None
st.markdown("**Try a question:**")
chip_cols = st.columns(len(SUGGESTED))
for col, q in zip(chip_cols, SUGGESTED):
    if col.button(q, key=f"chip_{q}"):
        pending = q

# Render history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

typed = st.chat_input("Ask Hermes about outlets, provinces, headroom, or spend…")
pending = typed or pending


# --------------------------------------------------------------------------
# Handle a new question
# --------------------------------------------------------------------------
if pending:
    st.session_state.messages.append({"role": "user", "content": pending})
    with st.chat_message("user"):
        st.markdown(pending)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        if active_key:
            try:
                import anthropic

                client = anthropic.Anthropic(api_key=active_key)
                with client.messages.stream(
                    model="claude-opus-4-8",
                    max_tokens=512,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
            except Exception as exc:
                full_response = _offline_reply(pending) + (
                    f"\n\n_(Live API unavailable: {type(exc).__name__} — answered offline.)_"
                )
                placeholder.markdown(full_response)
        else:
            full_response = _offline_reply(pending)
            placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
