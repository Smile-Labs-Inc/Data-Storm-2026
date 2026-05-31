"""Generate Final-Round report figures into Reports/figures/.

Run:  python Reports/make_final_round_figures.py
Reads: Results/outlet_intelligence.csv, smile_labs_budget_allocations_detailed.csv,
       smile_labs_predictions.csv
Writes: Reports/figures/fr_*.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "Results"
FIG = ROOT / "Reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

PRIMARY = "#0066CC"
ACCENT = "#E8511D"
GREEN = "#1F9D55"
GREY = "#888888"
plt.rcParams.update({
    "figure.dpi": 140,
    "savefig.dpi": 140,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
})

oi = pd.read_csv(RES / "outlet_intelligence.csv")
det = pd.read_csv(RES / "smile_labs_budget_allocations_detailed.csv")
preds = pd.read_csv(RES / "smile_labs_predictions.csv")


def save(fig, name):
    p = FIG / name
    fig.tight_layout()
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {p.relative_to(ROOT)}")


# ---------------------------------------------------------------- §4 spend figs
funded = det[det["Trade_Spend_Allocation_LKR"] > 0].copy()
unfunded = det[det["Trade_Spend_Allocation_LKR"] <= 0]

# 1. Lorenz curve of spend concentration
def lorenz(fig_name):
    s = np.sort(det["Trade_Spend_Allocation_LKR"].values)
    cum = np.cumsum(s)
    cum = cum / cum[-1]
    x = np.linspace(0, 1, len(cum))
    fig, ax = plt.subplots(figsize=(5.2, 4))
    ax.plot(x, cum, color=PRIMARY, lw=2.2, label="Spend concentration")
    ax.plot([0, 1], [0, 1], "--", color=GREY, lw=1, label="Perfect equality")
    ax.fill_between(x, cum, x, color=PRIMARY, alpha=0.08)
    funded_frac = (det["Trade_Spend_Allocation_LKR"] > 0).mean()
    ax.axvline(1 - funded_frac, color=ACCENT, ls=":", lw=1.5)
    ax.text(1 - funded_frac + 0.01, 0.05,
            f"{funded_frac*100:.0f}% of outlets\nfunded", color=ACCENT, fontsize=8)
    ax.set_xlabel("Cumulative share of Western outlets (low→high spend)")
    ax.set_ylabel("Cumulative share of LKR 5M budget")
    ax.set_title("Budget concentration (Lorenz curve)")
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    save(fig, fig_name)

lorenz("fr_spend_lorenz.png")

# 2. Spend vs headroom, coloured by competitive intensity
def spend_vs_headroom(fig_name):
    fig, ax = plt.subplots(figsize=(5.6, 4))
    sc = ax.scatter(funded["headroom_liters"], funded["Trade_Spend_Allocation_LKR"],
                    c=funded["competitive_intensity"], cmap="viridis",
                    s=10, alpha=0.6, edgecolors="none")
    cb = fig.colorbar(sc, ax=ax)
    cb.set_label("Competitive intensity", fontsize=8)
    ax.set_xlabel("Latent headroom (litres / month)")
    ax.set_ylabel("Allocated trade spend (LKR)")
    ax.set_title("Spend follows headroom & margin, not history")
    save(fig, fig_name)

spend_vs_headroom("fr_spend_vs_headroom.png")

# 3. Funded vs unfunded + utilisation summary bars
def allocation_summary(fig_name):
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6))
    a = axes[0]
    counts = [len(funded), len(unfunded)]
    a.bar(["Funded", "Not funded"], counts, color=[GREEN, GREY], width=0.6)
    for i, c in enumerate(counts):
        a.text(i, c, f"{c:,}", ha="center", va="bottom", fontsize=9)
    a.set_ylabel("Western outlets")
    a.set_title("Outlets funded (3,729 / 9,000)")

    b = axes[1]
    spent = det["Trade_Spend_Allocation_LKR"].sum()
    budget = 5_000_000
    b.barh(["Budget"], [budget], color="#dddddd", label="Budget LKR 5M")
    b.barh(["Budget"], [spent], color=PRIMARY, label=f"Allocated ({spent/budget*100:.0f}%)")
    b.set_xlabel("LKR")
    b.set_title("Budget utilisation")
    b.legend(fontsize=8, frameon=False, loc="lower right")
    b.grid(axis="y", alpha=0)
    save(fig, fig_name)

allocation_summary("fr_allocation_summary.png")

# 4. Marginal efficiency: liters per 1000 LKR distribution
def efficiency_hist(fig_name):
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.hist(funded["liters_per_1000_lkr"], bins=40, color=PRIMARY, alpha=0.85)
    med = funded["liters_per_1000_lkr"].median()
    ax.axvline(med, color=ACCENT, lw=1.5, ls="--", label=f"median {med:.1f} L / 1k LKR")
    ax.set_xlabel("Litres gained per LKR 1,000 spent")
    ax.set_ylabel("Funded outlets")
    ax.set_title("Spend efficiency across funded outlets")
    ax.legend(fontsize=8, frameon=False)
    save(fig, fig_name)

efficiency_hist("fr_spend_efficiency.png")

# 5. Spend by distributor (Western)
def spend_by_distributor(fig_name):
    g = det.groupby("dominant_distributor").agg(
        spend=("Trade_Spend_Allocation_LKR", "sum"),
        liters=("expected_incremental_liters", "sum"),
    ).reset_index().sort_values("spend", ascending=True)
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ax.barh(g["dominant_distributor"], g["spend"] / 1e6, color=PRIMARY)
    for i, (_, r) in enumerate(g.iterrows()):
        ax.text(r["spend"]/1e6, i, f" {r['liters']:,.0f} L", va="center", fontsize=8, color=GREY)
    ax.set_xlabel("Allocated spend (LKR millions)")
    ax.set_title("Spend & expected litres by Western distributor")
    save(fig, fig_name)

spend_by_distributor("fr_spend_by_distributor.png")

# ---------------------------------------------------------------- portfolio figs
# 6. Predicted potential distribution
def potential_hist(fig_name):
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    v = preds["Maximum_Monthly_Liters"]
    ax.hist(v, bins=60, color=PRIMARY, alpha=0.85)
    ax.axvline(v.median(), color=ACCENT, ls="--", lw=1.5, label=f"median {v.median():,.0f} L")
    ax.set_xlabel("Predicted maximum monthly litres")
    ax.set_ylabel("Outlets")
    ax.set_title("Latent potential across 20,000 outlets")
    ax.legend(fontsize=8, frameon=False)
    save(fig, fig_name)

potential_hist("fr_potential_dist.png")

# 7. Uplift ratio distribution
def uplift_hist(fig_name):
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    u = oi["uplift_ratio"].clip(upper=oi["uplift_ratio"].quantile(0.995))
    ax.hist(u, bins=50, color=GREEN, alpha=0.85)
    ax.axvline(oi["uplift_ratio"].median(), color=ACCENT, ls="--", lw=1.5,
               label=f"median {oi['uplift_ratio'].median():.3f}×")
    ax.set_xlabel("Uplift ratio (predicted / historical max)")
    ax.set_ylabel("Outlets")
    ax.set_title("Uplift distribution")
    ax.legend(fontsize=8, frameon=False)
    save(fig, fig_name)

uplift_hist("fr_uplift_dist.png")

# 8. Headroom by province
def headroom_by_province(fig_name):
    g = oi.groupby("province").agg(
        outlets=("Outlet_ID", "count"),
        headroom=("headroom_liters", "sum"),
    ).reindex(["Western", "Central", "North-Western", "Southern"])
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    ax.bar(g.index, g["headroom"] / 1e6, color=PRIMARY)
    for i, (_, r) in enumerate(g.iterrows()):
        ax.text(i, r["headroom"]/1e6, f"{r['outlets']:,}\noutlets",
                ha="center", va="bottom", fontsize=8, color=GREY)
    ax.set_ylabel("Total latent headroom (M litres / month)")
    ax.set_title("Untapped headroom by province")
    save(fig, fig_name)

headroom_by_province("fr_headroom_by_province.png")

# 9. Competitive intensity vs uplift (market saturation effect)
def competition_effect(fig_name):
    fig, ax = plt.subplots(figsize=(5.6, 3.8))
    bins = np.linspace(0, oi["competitive_intensity"].max(), 11)
    oi["_cbin"] = pd.cut(oi["competitive_intensity"], bins)
    g = oi.groupby("_cbin", observed=True)["uplift_ratio"].median()
    centers = [iv.mid for iv in g.index]
    ax.plot(centers, g.values, "o-", color=ACCENT, lw=2)
    ax.set_xlabel("Competitive intensity (outlets within 500 m, normalised)")
    ax.set_ylabel("Median uplift ratio")
    ax.set_title("Market saturation dampens potential uplift")
    save(fig, fig_name)

competition_effect("fr_competition_effect.png")

# 10. Geographic scatter of Western spend
def western_map(fig_name):
    w = oi[oi["province"] == "Western"].merge(
        det[["Outlet_ID", "Trade_Spend_Allocation_LKR"]], on="Outlet_ID", how="left")
    w["Trade_Spend_Allocation_LKR"] = w["Trade_Spend_Allocation_LKR"].fillna(0)
    fig, ax = plt.subplots(figsize=(5.2, 5.4))
    nf = w[w["Trade_Spend_Allocation_LKR"] <= 0]
    fd = w[w["Trade_Spend_Allocation_LKR"] > 0]
    ax.scatter(nf["Longitude"], nf["Latitude"], s=4, color="#cccccc", label="Not funded")
    sc = ax.scatter(fd["Longitude"], fd["Latitude"], s=12,
                    c=fd["Trade_Spend_Allocation_LKR"], cmap="plasma", label="Funded")
    fig.colorbar(sc, ax=ax, label="Spend (LKR)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Western Province spend allocation map")
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    ax.grid(alpha=0.15)
    save(fig, fig_name)

western_map("fr_western_spend_map.png")

print("\nAll figures generated.")
